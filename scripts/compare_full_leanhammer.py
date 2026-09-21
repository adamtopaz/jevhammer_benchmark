"""Compare three separately executed, source-matched and replayed pilot arms.

Usage: python scripts/compare_full_leanhammer.py RUN_PARENT OUTPUT_JSON
The parent contains cpu/, neural/, full/, and deployment.json. No runs are started.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(parent):
    metrics, successes, evidence, public = {}, {}, {}, []
    expected_dataset = None
    dataset = None
    total_replayed = 0
    for arm in ("cpu", "neural", "full"):
        root = parent / arm
        manifest, summary, verification = [read(root / n) for n in
                                            ("run.json", "summary.json", "verification.json")]
        assert manifest["status"] == summary["status"] == verification["status"] == "complete"
        assert manifest["guidance"] == "jev", "Mock Jev runs are not performance evidence"
        assert manifest["threads"] == 8 and manifest["outerHeartbeats"] == 200000
        method = "LeanHammerComparison." + arm
        assert manifest["methods"] == [method]
        if expected_dataset is None:
            expected_dataset = manifest["datasetSha256"]
            dataset = read(root / "dataset.json")
        assert manifest["datasetSha256"] == expected_dataset
        assert read(root / "dataset.json") == dataset
        trials = rows(root / "trials.jsonl")
        expected = {s["site"] for s in dataset["sites"]}
        assert len(expected) == len(trials) == 34
        assert {r["site"] for r in trials} == expected
        assert all(r["method"] == method and r["config"]["maxMillis"] == 6000 for r in trials)
        checks = rows(root / verification["directory"] / "replay.jsonl")
        assert all(r["verified"] and r["method"] == method for r in checks)
        verified = {r["site"] for r in checks}
        assert len(verified) == len(checks)
        assert verified == {r["site"] for r in trials if r["solved"]}
        total_replayed += len(verified)
        ontime = {r["site"] for r in trials if r["onTime"] and r["site"] in verified}
        successes[arm] = ontime
        metrics[arm] = {**summary["methods"][method], "config": trials[0]["config"],
                        "usage": summary["usage"],
                        "stateCalls": sum(r["stats"]["stateRankCalls"] for r in trials),
                        "premiseCalls": sum(r["stats"]["premiseRankCalls"] for r in trials),
                        "retrievalMs": sum(r["stats"]["retrievalMs"] for r in trials),
                        "warmupMs": sum(r["elapsedMs"] for r in rows(root / "warmup.jsonl"))}
        assert metrics[arm]["onTimeVerified"] == len(ontime)
        if arm == "full":
            assert summary["usage"]["attempts"] == 0
            assert metrics[arm]["stateCalls"] == metrics[arm]["premiseCalls"] == 0
            counters = rows(root / "leanhammer-selector.jsonl")
            assert len(counters) >= len(trials), "Missing full-tactic instrumentation"
            metrics[arm]["upstreamSelector"] = {
                key: sum(r[key] for r in counters) for key in
                ("calls", "elapsedMs", "candidates", "unavailable", "fallbacks")}
            metrics[arm]["upstreamSelector"]["errors"] = dict(Counter(
                error for r in counters for error in r["errors"]))
        else:
            assert metrics[arm]["stateCalls"] > 0
            assert all(r["stats"]["rankCalls"] <= 3 for r in trials)
        for resource in manifest["resources"].values():
            assert resource["memoryMax"] <= 16000000000 and resource["swapMax"] == "0"
        metrics[arm]["scopePeakBytesAtCompletion"] = int(manifest["resources"]["final"]["memory.peak"])
        for r in trials:
            public.append({k: r[k] for k in
                           ("site", "module", "declaration", "method", "elapsedMs", "stats", "budgetBlocked")}
                          | {"rawSolved": r["solved"], "independentlyReplayed": r["site"] in verified,
                             "onTimeVerified": r["site"] in ontime})
        evidence[arm] = {n: sha(root / n) for n in
                         ("run.json", "dataset.json", "summary.json", "trials.jsonl", "verification.json",
                          verification["directory"] + "/replay.jsonl", "usage.json", "warmup.jsonl")}
        if arm == "full":
            evidence[arm]["leanhammer-selector.jsonl"] = sha(root / "leanhammer-selector.jsonl")
    assert metrics["cpu"]["config"] == metrics["neural"]["config"]
    owners = defaultdict(list)
    for site in dataset["sites"]:
        owners[site["declaration"]].append(site["site"])
    pairs = []
    for a, b in [("cpu", "full"), ("neural", "full"), ("cpu", "neural")]:
        gains, losses = successes[a] - successes[b], successes[b] - successes[a]
        rng, samples = random.Random(0), []
        groups = list(owners.values())
        for _ in range(1000):
            sample = [site for group in rng.choices(groups, k=len(groups)) for site in group]
            samples.append(sum((site in gains) - (site in losses) for site in sample) / len(sample))
        samples.sort()
        pairs.append({"a": a, "b": b, "gained": len(gains), "lost": len(losses),
                      "declarationBootstrap95": [samples[25], samples[974]]})
    return {"schema": 1, "status": "complete", "kind": "full-tactic-development-pilot",
            "sites": 34, "trials": len(public), "successfulTrialsIndependentlyReplayed": total_replayed,
            "datasetSha256": expected_dataset, "metrics": metrics, "paired": pairs,
            "deployment": read(parent / "deployment.json"), "evidenceSha256": evidence,
            "reservedEvaluationTrials": 0,
            "limitations": [
                "34 exposed development sites; not a held-out superiority evaluation.",
                "Fresh separate Lean processes per arm; full LeanHammer gets fresh neural service processes; model/corpus disk caches persist.",
                "Initialization excluded from goal timing and reported separately.",
                "Internal time/heartbeat mechanisms differ; primary coverage uses observed end-to-end deadline.",
                "Neural training overlap unknown; all local fitted cohort owners excluded.",
                "This measures current package configurations, not the historical monolithic tactic."]}, public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report, public = compare(args.parent)
    trials = args.output.with_name(args.output.stem + "-trials.jsonl")
    trials.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in public))
    report["publicTrials"] = {"path": trials.name, "sha256": sha(trials)}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("metrics", "paired", "successfulTrialsIndependentlyReplayed")}, indent=2))


if __name__ == "__main__":
    main()
