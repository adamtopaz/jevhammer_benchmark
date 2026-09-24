"""Audit the archived monolithic Jev/no-Jev comparison, without running Lean.

Default: check the public metadata export. --archive PATH --export exports from
the original final-practical-v1 directory; it never reruns the old experiment.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "docs/historical-guidance"
MODES = ("neural_search_jev", "neural_search")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def summarize(rows):
    groups = {m: {r["site"]: r for r in rows if r["mode"] == m} for m in MODES}
    assert len(rows) == 2048 and all(len(g) == 1024 for g in groups.values())
    assert groups[MODES[0]].keys() == groups[MODES[1]].keys()
    assert not any(r["censored"] for r in rows)
    successes = {m: {s for s, r in g.items() if r["solved"] and r["elapsedMs"] <= 6000}
                 for m, g in groups.items()}
    a, b = (successes[m] for m in MODES)
    return {"sites": 1024, "modules": len({r["module"] for r in rows}),
            "declarations": len({(r["module"], r["declaration"]) for r in rows}),
            "deadlineMs": 6000, "gained": len(a - b), "lost": len(b - a),
            "difference": (len(a) - len(b)) / 1024,
            "metrics": {m: {"onTime": len(successes[m]),
                "raw": sum(r["solved"] for r in g.values()),
                "freshCalls": sum(r["freshCalls"] for r in g.values()),
                "cachedDecisions": sum(r["cacheHits"] for r in g.values())}
                for m, g in groups.items()}}


def export(archive):
    manifest = {r["site"]: r for r in read(archive / "manifest.json")}
    assert len(manifest) == 1024
    assert read(archive / "metadata.json")["status"] == "complete"
    rows, total_solved, counts = [], 0, Counter()
    with (archive / "trials.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            counts[r["mode"]] += 1
            total_solved += r["solved"]
            if r["mode"] not in MODES:
                continue
            rows.append({k: r[k] for k in ("site", "module", "mode", "solved", "elapsedMs", "censored")}
                | {"declaration": manifest[r["site"]]["declaration"],
                   "freshCalls": r["external"]["freshCalls"], "cacheHits": r["external"]["cacheHits"],
                   "rankCalls": r["stats"]["rankCalls"], "rankFailures": r["stats"]["rankFailures"]})
    verification = read(archive / "replay-certificates/verification.json")
    assert len(counts) == 4 and set(counts.values()) == {1024}
    assert verification["certificates"] == total_solved == 1604 and not verification["network"]
    report = summarize(rows)
    comparison = next(c for c in read(archive / "hammer-comparison.json")["comparisons"]
                      if c["mode"] == MODES[0] and c["baseline"] == MODES[1]
                      and c["outcome"] == "withinDeadline")
    assert all(comparison[k] == report[k] for k in ("gained", "lost", "difference")
               if k in comparison)  # archived keys use gains/losses
    assert comparison["gains"] == report["gained"] and comparison["losses"] == report["lost"]
    PUBLIC.mkdir(exist_ok=True)
    path = PUBLIC / "trials.jsonl"
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    protocol = read(archive / "evaluation-protocol.json")
    source_files = {}
    for rel in ("JevFinish/Advanced.lean", "hammer-supported/JevHammerBackend.lean", "Bench/AtEachStep.lean"):
        source = archive / "sources/benchmarks" / rel
        assert sha(source) == protocol["sourceSha256"][rel]
        target = PUBLIC / source.name
        target.write_bytes(source.read_bytes())
        source_files[target.name] = sha(target)
    report.update(schema=1, kind="archived-combined-premise-and-state-guidance",
        publicTrials={"path": path.name, "sha256": sha(path)}, sourceSha256=source_files,
        archivedDeclarationBootstrap95=comparison["clusterInterval"],
        archivedReplayRecord=verification,
        archiveSha256={n: sha(archive / n) for n in ("trials.jsonl", "manifest.json", "metadata.json",
            "evaluation-protocol.json", "hammer-comparison.json", "replay-certificates/verification.json")},
        limitations=["Different monolithic engine and cohort from the current public tactic.",
            "Disables both premise and continuation ranking; not a state-only ablation.",
            "No-ranker control skips decision accounting, unlike the new slot-matched controls.",
            "Jev used 52 cached decisions with recorded latency charged.",
            "Neural/Jev pretraining overlap unknown; fixed 31-module sample.",
            "Metadata audit only; archived offline replay record is not a new kernel replay."])
    (PUBLIC / "audit.json").write_text(json.dumps(report, indent=2) + "\n")


def check():
    report = read(PUBLIC / "audit.json")
    path = PUBLIC / report["publicTrials"]["path"]
    assert sha(path) == report["publicTrials"]["sha256"]
    for name, digest in report["sourceSha256"].items():
        assert sha(PUBLIC / name) == digest
    actual = summarize([json.loads(s) for s in path.read_text().splitlines()])
    assert all(report[k] == v for k, v in actual.items())
    print(json.dumps({"verifiedMetadata": True, **actual}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path)
    p.add_argument("--export", action="store_true")
    args = p.parse_args()
    if args.export:
        if not args.archive:
            p.error("--export requires --archive")
        export(args.archive)
    check()
