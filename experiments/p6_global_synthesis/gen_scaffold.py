"""P6 — generate the Phase-A coarse scaffold via Haiku 4.5 (teacher-LLM compressor),
freeze to scaffold_haiku.json so the run is reproducible and guard (c) is checked
against the exact views the run uses. Reuses build_schedule's Phase-A chunk
boundaries; only the compressor changes (extractive stand-in -> real Haiku).

Backends: 'kiro' (KiroCompressor, needs KIRO_API_KEY) or 'claude' (LLMCompressor,
claude -p --model haiku, local OAuth). Same claude-haiku-4-5 model family either way.

  python experiments/p6_global_synthesis/gen_scaffold.py --backend claude --workers 3
"""
from __future__ import annotations

import argparse, json, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pca.compressor import get_compressor          # noqa: E402
from pca.planted import build_schedule, load_turns  # noqa: E402
from pca.textutils import n_tokens                  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["claude", "kiro"], default="claude")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    p4 = yaml.safe_load((HERE / cfg["p4_config"]).read_text(encoding="utf-8"))
    turns = load_turns((HERE / cfg["p4_config"]).resolve().parent / Path(p4["data_dir"]) / "conversation.jsonl")
    V = p4["schedule"]["V"]
    sch = build_schedule(turns, V, p4["schedule"]["R"], tuple(p4["schedule"]["stage_fracs"]))
    chunksA = [p for p in sch if p["phase"] == "A"]
    print(f"Phase-A chunks to compress: {len(chunksA)} (V={V})", flush=True)

    out_path = HERE / "scaffold_haiku.json"
    cache = {}
    if out_path.exists():
        cache = {c["chunk"]: c for c in json.loads(out_path.read_text(encoding="utf-8"))}
        print(f"resuming: {len(cache)} chunks already cached", flush=True)

    comp = get_compressor("llm" if args.backend == "claude" else "kiro")
    print(f"compressor: {comp.name} (backend={args.backend})", flush=True)
    lock = threading.Lock()

    def work(idx, p):
        view = comp.compress(p["slice_text"], V)
        return idx, {"chunk": idx, "turn_lo": p["turn_lo"], "turn_hi": p["turn_hi"],
                     "slice_tokens": p["slice_tokens"], "view_tokens": n_tokens(view),
                     "compression_ratio": round(p["slice_tokens"] / max(n_tokens(view), 1), 2),
                     "compressor": comp.name, "view_text": view}

    todo = [(i, p) for i, p in enumerate(chunksA) if i not in cache]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, i, p): i for i, p in todo}
        for fut in as_completed(futs):
            idx, rec = fut.result()
            with lock:
                cache[idx] = rec
                out_path.write_text(json.dumps([cache[k] for k in sorted(cache)], indent=1, ensure_ascii=False),
                                    encoding="utf-8")
            print(f"  chunk {idx} turns{rec['turn_lo']}-{rec['turn_hi']}: "
                  f"{rec['slice_tokens']}->{rec['view_tokens']}tok ({rec['compression_ratio']}x)", flush=True)
    print(f"DONE -> {out_path} ({len(cache)}/{len(chunksA)} chunks)", flush=True)


if __name__ == "__main__":
    main()
