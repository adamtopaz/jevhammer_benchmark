"""Export the complete, independently replayed available-premise study."""
import argparse
from collections import Counter
import json
from pathlib import Path

from available_premises_study import check_plan
from compare_full_leanhammer import compare, read, rows, sha
from confirmation_statistics import holm, paired


def export(parent, plan):
    data, schedule = check_plan(plan)
    deployment = read(parent / "deployment.json")
    assert deployment["status"] == "complete"
    assert deployment["scheduleSha256"] == sha(plan / "schedule.json")
    assert deployment["datasetSha256"] == sha(plan / "dataset.json")
    order = [(b["batch"], a) for b in schedule["batches"] for a in b["order"]]
    assert [(b["batch"], b["arm"]) for b in deployment["completedArms"]] == order
    arms = ("strict", "cpu", "neural", "full")
    metrics, successes, evidence = {}, {a: set() for a in arms}, {}
    public, preparations, covered = [], [], set()
    for batch in schedule["batches"]:
        key = f"batch-{batch['batch']}"
        root = parent / key
        batch_deployment = read(root / "deployment.json")
        assert batch_deployment["status"] == "complete"
        assert batch_deployment["completedArms"] == batch["order"]
        result, trials = compare(root, batch["sites"], arms)
        result["kind"] = "available-premises-batch"
        result["limitations"] = ["Use the combined sensitivity-study analysis."]
        assert result["datasetSha256"] == batch["datasetSha256"]
        assert result["metrics"]["strict"]["config"] == result["metrics"]["cpu"]["config"]
        sites = {s["site"] for s in read(plan / batch["dataset"])["sites"]}
        assert not sites & covered
        covered |= sites
        evidence[key] = result
        for arm, values in result["metrics"].items():
            run = read(root / arm / "run.json")
            assert not run["failures"]
            assert read(root / arm / "dataset.json")["project"] == data["project"]
            if arm not in metrics:
                metrics[arm] = {k: 0 for k in ["sites", "recorded", "onTimeVerified", "rawVerified",
                    "lateVerified", "elapsedMs", "budgetBlocked", "rankFailures", "stateCalls", "premiseCalls",
                    "retrievalMs", "warmupMs"]}
                metrics[arm]["usage"] = {k: 0 for k in values["usage"]}
                metrics[arm]["config"] = values["config"]
            assert metrics[arm]["config"] == values["config"]
            for k in metrics[arm]:
                if k not in ("usage", "config"):
                    metrics[arm][k] += values[k]
            for k in values["usage"]:
                metrics[arm]["usage"][k] += values["usage"][k]
        for trial in trials:
            arm = trial["method"].rsplit(".", 1)[1]
            if trial["onTimeVerified"]:
                successes[arm].add(trial["site"])
            public.append({"batch": batch["batch"], **trial})
        warmups = rows(root / "strict/warmup.jsonl")
        expected_modules = {s["module"] for s in read(plan / batch["dataset"])["sites"]}
        assert Counter(w["module"] for w in warmups) == Counter({m: 1 for m in expected_modules})
        for row in warmups:
            p = row["provenance"]
            assert p["kind"] == "available-imported-statements-v1"
            assert p["holdoutOwners"] == 1212 and p["proofInformation"] == "none"
            assert row["module"] not in p["importedModules"]
            preparations.append({"module": row["module"], "elapsedMs": row["elapsedMs"],
                                 "provenance": p})
    assert covered == {s["site"] for s in data["sites"]}
    assert len(public) == 4096 and all(n == 1 for n in Counter(
        (r["site"], r["method"]) for r in public).values())
    for arm in arms:
        assert metrics[arm]["sites"] == metrics[arm]["recorded"] == 1024
        assert metrics[arm]["onTimeVerified"] == len(successes[arm])
    comparisons = [{"a": "strict", "b": b, "role": "primary" if b == "cpu" else "secondary",
                    **paired(data["sites"], successes["strict"], successes[b])}
                   for b in ("cpu", "neural", "full")]
    for pair, adjusted in zip(comparisons[1:], holm([p["exactMcNemarP"] for p in comparisons[1:]])):
        pair["secondaryHolmMcNemarP"] = adjusted
    full = [v["metrics"]["full"]["upstreamSelector"] for v in evidence.values()]
    metrics["full"]["upstreamSelector"] = {k: sum(v[k] for v in full) for k in
        ("calls", "elapsedMs", "candidates", "unavailable", "fallbacks")}
    errors = Counter()
    for v in full:
        errors.update(v["errors"])
    metrics["full"]["upstreamSelector"]["errors"] = dict(errors)
    return {"schema": 1, "status": "complete", "kind": "available-premises-sensitivity",
            "sites": 1024, "trials": 4096, "metrics": metrics, "paired": comparisons,
            "successfulTrialsIndependentlyReplayed": sum(v["rawVerified"] for v in metrics.values()),
            "deployment": deployment, "batches": evidence, "preparation": preparations,
            "datasetSha256": sha(plan / "dataset.json"), "scheduleSha256": sha(plan / "schedule.json"),
            "limitations": ["Previously exposed goals; no tuning during this follow-up.",
                "Strict CPU fits imported statements only; current-file candidates use live types without refitting.",
                "Jev and neural-selector pretraining overlap remains unknown.",
                "Single run per method; wall time and Jev decisions vary.",
                "Stratified size-filtered Mathlib sample; initialization excluded and reported.",
                "Lack of significance does not establish equivalence."]}, public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report, records = export(args.parent, args.plan)
    trials = args.output.with_name(args.output.stem + "-trials.jsonl")
    if args.output.exists() or trials.exists():
        raise ValueError("refusing to overwrite a published result")
    trials.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    report["publicTrials"] = {"path": trials.name, "sha256": sha(trials)}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"coverage": {a: v["onTimeVerified"] for a, v in report["metrics"].items()},
                      "paired": report["paired"]}, indent=2))


if __name__ == "__main__":
    main()
