"""Generate production Haiku views deterministically via `claude -p` (D29).

Reads slices.jsonl, compresses each slice with LLMCompressor (claude -p --model
haiku), appends view records to views_haiku.jsonl. RESUMABLE: skips (doc_id,k)
already present, so a quota interruption just means re-run to continue. Modest
parallelism; failures are skipped (not written) and retried on the next run.

Usage: uv run python -m pca.gen_views_llm --slices data/views/slices.jsonl \
         --out data/views/views_haiku.jsonl --workers 4 --target-tokens 512
"""

from __future__ import annotations

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .compressor import KiroCompressor, LLMCompressor
from .textutils import n_tokens


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slices", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--target-tokens", type=int, default=512)
    ap.add_argument("--stop-after-fails", type=int, default=8,
                    help="halt after this many consecutive failures (quota wall) instead of churning")
    ap.add_argument("--backend", choices=["claude", "kiro"], default="claude",
                    help="claude = claude -p (OAuth pool, local or --ssh-host); "
                         "kiro = Kiro CLI headless (credit-metered, needs KIRO_API_KEY in env)")
    ap.add_argument("--ssh-host", default=None,
                    help="route each claude -p call over ssh to this host (uses its OAuth pool)")
    ap.add_argument("--remote-claude", default="claude",
                    help="path to claude on the ssh host (use an absolute path if it is "
                         "not on the non-interactive shell PATH)")
    ap.add_argument("--seed", action="append", default=[],
                    help="extra completed views file(s) to add to the done-set without writing to them "
                         "(e.g. the main views_haiku.jsonl when this run writes a separate remote file)")
    ap.add_argument("--gen-path", default=None,
                    help="provenance label stamped into each record (e.g. local/remote/kiro) so the "
                         "delivery path is recoverable after merge")
    args = ap.parse_args()

    slices = [json.loads(l) for l in Path(args.slices).open(encoding="utf-8")]
    out = Path(args.out)
    done = set()
    for src in [out, *(Path(p) for p in args.seed)]:
        if src.exists():
            for l in src.open(encoding="utf-8"):
                try:
                    r = json.loads(l)
                    done.add((r["doc_id"], r["k"]))
                except json.JSONDecodeError:
                    pass
    todo = [s for s in slices if (s["doc_id"], s["k"]) not in done]
    print(f"slices={len(slices)} done={len(done)} todo={len(todo)} workers={args.workers} "
          f"backend={args.backend} ssh_host={args.ssh_host}", flush=True)

    if args.backend == "kiro":
        comp = KiroCompressor()
    else:
        comp = LLMCompressor(ssh_host=args.ssh_host, remote_claude=args.remote_claude)
    lock = threading.Lock()
    fh = out.open("a", encoding="utf-8")
    n_ok = [0]
    n_fail = [0]
    consec = [0]
    stop = threading.Event()

    def work(s):
        if stop.is_set():
            raise RuntimeError("skipped (quota wall reached)")
        view = comp.compress(s["slice_text"], args.target_tokens)
        vt = n_tokens(view)
        rec = {"doc_id": s["doc_id"], "k": s["k"], "K": s["K"], "view_text": view,
               "view_tokens": vt, "slice_tokens": s["slice_tokens"],
               "compression_ratio": round(s["slice_tokens"] / max(vt, 1), 3),
               "compressor": comp.name}
        if args.gen_path:
            rec["gen_path"] = args.gen_path
        return rec

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, s): s for s in todo}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                rec = fut.result()
                with lock:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    fh.flush()
                    n_ok[0] += 1
                    consec[0] = 0
                    if n_ok[0] % 10 == 0:
                        print(f"  ok={n_ok[0]} fail={n_fail[0]} (last {s['doc_id']} k{s['k']})", flush=True)
            except Exception as e:
                with lock:
                    n_fail[0] += 1
                    consec[0] += 1
                    if not stop.is_set() and "skipped" not in str(e):
                        print(f"  FAIL {s['doc_id']} k{s['k']}: {str(e)[:120]}", flush=True)
                    if consec[0] >= args.stop_after_fails and not stop.is_set():
                        stop.set()
                        print(f"  STOP: {consec[0]} consecutive failures — quota wall reached, halting cleanly.", flush=True)
    fh.close()
    tag = " (HALTED at quota wall — re-run to resume)" if stop.is_set() else ""
    print(f"DONE ok={n_ok[0]} fail={n_fail[0]} total_now={len(done) + n_ok[0]}/{len(slices)}{tag}", flush=True)


if __name__ == "__main__":
    main()
