"""E0 — position-from-view classifier. CPU-only. Re-runnable from config.yaml alone.

Usage: uv run python experiments/e0_view_classifier/run.py
Outputs: metrics.json, figures/*.png, audit.json (contamination audit), gate call on stdout.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))

from pca.textutils import FEATURE_ORDER, hand_features  # noqa: E402

# ---------------------------------------------------------------- contamination
# Patterns that would constitute positional-metadata leakage if the generator
# ever stamped them into view text. Strip is defense-in-depth; audit proves
# the distribution is clean either way.
LEAK_PATTERNS = [
    (re.compile(r"(?i)\bpass\s+\d+\s+of\s+\d+\b"), "pass-N-of-K header"),
    (re.compile(r"(?i)\b[kK]\s*[:=]\s*\d+\b"), "k=/K= annotation"),
    (re.compile(r"(?i)\bchunk\s*#?\d+\b"), "chunk index"),
    (re.compile(r"govreport-\d+"), "doc_id echo"),
    (re.compile(r"(?i)\bcompression[ _-]?(ratio|level|schedule)\b"), "schedule annotation"),
    (re.compile(r"(?i)\bsigma[ _]?\d\b"), "sigma annotation"),
]


def strip_and_audit(records: list[dict]) -> dict:
    audit = {"n_views": len(records), "hits": {}, "n_views_modified": 0, "samples": []}
    for r in records:
        text, hit = r["view_text"], False
        for pat, label in LEAK_PATTERNS:
            ms = pat.findall(text)
            if ms:
                audit["hits"][label] = audit["hits"].get(label, 0) + len(ms)
                if len(audit["samples"]) < 10:
                    audit["samples"].append(
                        {"doc_id": r["doc_id"], "k": r["k"], "label": label, "match": str(ms[0])[:80]}
                    )
                text = pat.sub(" ", text)
                hit = True
        if hit:
            audit["n_views_modified"] += 1
            r["view_text"] = re.sub(r"\s+", " ", text).strip()
    return audit


# ---------------------------------------------------------------- helpers
def doc_split(doc_ids: list[str], cfg: dict, seed: int) -> dict[str, str]:
    rng = np.random.RandomState(seed)
    ids = sorted(set(doc_ids))
    rng.shuffle(ids)
    n = len(ids)
    n_tr = int(round(cfg["train"] * n))
    n_va = int(round(cfg["val"] * n))
    return {
        **{d: "train" for d in ids[:n_tr]},
        **{d: "val" for d in ids[n_tr : n_tr + n_va]},
        **{d: "test" for d in ids[n_tr + n_va :]},
    }


def bucket_of(k: int, K: int, cfg: dict) -> str:
    t = (k - 1) / (K - 1)
    if t < cfg["early_max_t"]:
        return "early"
    if t < cfg["mid_max_t"]:
        return "mid"
    return "late"


def evaluate_k(y_true, y_pred, K: int) -> dict:
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "acc_within_1": float(np.mean(np.abs(np.array(y_true) - np.array(y_pred)) <= 1)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(range(1, K + 1))).tolist(),
    }


def plot_confusion(cm, K, title, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cm = np.array(cm, dtype=float)
    cmn = cm / cm.sum(axis=1, keepdims=True).clip(min=1)
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    im = ax.imshow(cmn, cmap="viridis", vmin=0, vmax=1)
    ax.set_xticks(range(K), [str(i) for i in range(1, K + 1)])
    ax.set_yticks(range(K), [str(i) for i in range(1, K + 1)])
    ax.set_xlabel("predicted k")
    ax.set_ylabel("true k")
    ax.set_title(title)
    for i in range(K):
        for j in range(K):
            ax.text(j, i, f"{cmn[i, j]:.2f}", ha="center", va="center",
                    color="white" if cmn[i, j] < 0.6 else "black", fontsize=7)
    fig.colorbar(im, ax=ax, label="row-normalized")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fit_eval(Xtr, ytr, Xva, yva, Xte, yte, kind: str, seed: int, cfg: dict):
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if kind == "logreg":
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=cfg.get("max_iter", 2000), random_state=seed),
        )
    elif kind == "mlp":
        clf = make_pipeline(
            StandardScaler(),
            MLPClassifier(
                hidden_layer_sizes=(cfg.get("hidden", 256),),
                max_iter=cfg.get("max_iter", 400),
                early_stopping=cfg.get("early_stopping", True),
                random_state=seed,
            ),
        )
    else:
        raise ValueError(kind)
    clf.fit(Xtr, ytr)
    return clf, float(clf.score(Xva, yva)), clf.predict(Xte), float(clf.score(Xte, yte))


def main() -> None:
    cfg_path = HERE / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg_hash = hashlib.sha256(cfg_path.read_bytes()).hexdigest()[:16]
    seed = cfg["seed"]

    views_path = (HERE / cfg["views_path"]).resolve()
    records = [json.loads(l) for l in views_path.open(encoding="utf-8")]
    K = records[0]["K"]
    assert all(r["K"] == K for r in records), "mixed K not supported"

    audit = strip_and_audit(records)
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(f"contamination audit: {audit['n_views_modified']}/{audit['n_views']} views modified; "
          f"hits={audit['hits'] or 'none'}")

    split = doc_split([r["doc_id"] for r in records], cfg["split"], seed)
    for r in records:
        r["split"] = split[r["doc_id"]]
        r["bucket"] = bucket_of(r["k"], K, cfg["buckets"])

    idx = {s: [i for i, r in enumerate(records) if r["split"] == s] for s in ("train", "val", "test")}
    y_k = np.array([r["k"] for r in records])
    y_b = np.array([r["bucket"] for r in records])
    y_t = np.array([(r["k"] - 1) / (K - 1) for r in records])

    # ---- Tier A features
    print("computing Tier A features...")
    XA = np.array([[hand_features(r["view_text"])[f] for f in cfg["tier_a"]["features"]]
                   for r in records])

    # ---- Tier B embeddings
    print("encoding Tier B embeddings (MiniLM, CPU)...")
    from sentence_transformers import SentenceTransformer

    enc = SentenceTransformer(cfg["tier_b"]["encoder"], device="cpu")
    XB = enc.encode([r["view_text"] for r in records], batch_size=64,
                    show_progress_bar=False, convert_to_numpy=True)

    metrics: dict = {
        "config_hash": cfg_hash,
        "n_docs": len(set(r["doc_id"] for r in records)),
        "n_views": len(records),
        "K": K,
        "compressor": records[0].get("compressor", "unknown"),
        "split_sizes": {s: len(v) for s, v in idx.items()},
        "bucket_distribution": dict(Counter(y_b.tolist())),
        "chance": {"exact_k": 1.0 / K, "bucket_uniform": 1 / 3,
                   "bucket_majority": max(Counter(y_b[idx["test"]].tolist()).values())
                   / len(idx["test"])},
        "tiers": {},
    }

    def sel(X, ids):
        return X[ids]

    from sklearn.linear_model import Ridge
    from sklearn.metrics import r2_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    for tier, X, probes in (
        ("tier_a", XA, {"logreg": {"model": "logreg", **cfg["tier_a"]}}),
        ("tier_b", XB, cfg["tier_b"]["probes"]),
    ):
        tier_out = {}
        for pname, pcfg in probes.items():
            kind = pcfg.get("model", "mlp" if pname == "mlp" else "logreg")
            out = {}
            # exact k
            _, vacc, pred_k, tacc = fit_eval(sel(X, idx["train"]), y_k[idx["train"]],
                                             sel(X, idx["val"]), y_k[idx["val"]],
                                             sel(X, idx["test"]), y_k[idx["test"]],
                                             kind, seed, pcfg)
            out["exact_k"] = evaluate_k(y_k[idx["test"]], pred_k, K)
            out["exact_k"]["val_accuracy"] = vacc
            plot_confusion(out["exact_k"]["confusion_matrix"], K,
                           f"E0 {tier}/{pname}: exact k (test)",
                           HERE / "figures" / f"confusion_k_{tier}_{pname}.png")
            # bucket
            _, bvacc, pred_b, btacc = fit_eval(sel(X, idx["train"]), y_b[idx["train"]],
                                               sel(X, idx["val"]), y_b[idx["val"]],
                                               sel(X, idx["test"]), y_b[idx["test"]],
                                               kind, seed, pcfg)
            out["bucket"] = {"val_accuracy": bvacc, "test_accuracy": btacc}
            # normalized position regression
            reg = make_pipeline(StandardScaler(), Ridge(random_state=seed))
            reg.fit(sel(X, idx["train"]), y_t[idx["train"]])
            out["norm_position_r2"] = float(r2_score(y_t[idx["test"]],
                                                     reg.predict(sel(X, idx["test"]))))
            tier_out[pname] = out
            print(f"  {tier}/{pname}: k-acc={out['exact_k']['accuracy']:.3f} "
                  f"±1={out['exact_k']['acc_within_1']:.3f} "
                  f"bucket={btacc:.3f} R2={out['norm_position_r2']:.3f}")
        metrics["tiers"][tier] = tier_out

    # ---- gate (pre-registered)
    g = cfg["gate"]
    tb = metrics["tiers"]["tier_b"]
    best = max(tb, key=lambda p: tb[p]["bucket"]["val_accuracy"])
    gate_acc = tb[best]["bucket"]["test_accuracy"]
    if gate_acc >= g["time_agnostic_min"]:
        regime = "time-agnostic"
    elif gate_acc <= g["signal_carrying_max"]:
        regime = "signal-carrying"
    else:
        regime = "mixed"
    metrics["gate"] = {"selected_probe": best, "tier_b_bucket_test_accuracy": gate_acc,
                       "regime": regime, "provisional": bool(g.get("provisional", False))}
    (HERE / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nGATE: tier_b/{best} bucket test acc = {gate_acc:.3f} -> regime = {regime}"
          f"{' (E0-provisional)' if metrics['gate']['provisional'] else ''}")
    print(f"config_hash = {cfg_hash}")


if __name__ == "__main__":
    main()
