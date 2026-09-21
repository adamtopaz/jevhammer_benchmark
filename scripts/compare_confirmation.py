"""Validate and export the completed 1,024-location confirmation study.

Usage: python scripts/compare_confirmation.py RUN_PARENT PLAN_DIRECTORY OUTPUT_JSON
Requires all six batches and all three independently replayed arms per batch.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from compare_full_leanhammer import compare, read, sha
from confirmation_statistics import holm, paired


def export(parent, plan):
    schedule = read(plan / "schedule.json")
    dataset = read(plan / "dataset.json")
    deployment = read(parent / "deployment.json")
    assert deployment["status"] == "complete"
    assert deployment["scheduleSha256"] == sha(plan / "schedule.json")
    assert schedule["sites"] == len(dataset["sites"]) == 1024
    assert len({s["declaration"] for s in dataset["sites"]}) == 1024
    expected_order = [(b["batch"], arm) for b in schedule["batches"] for arm in b["order"]]
    assert [(r["batch"], r["arm"]) for r in deployment["completedArms"]] == expected_order
    assert len(expected_order) == 18
    metrics, success = {}, {arm: set() for arm in ["cpu", "neural", "full"]}
    public, evidence, covered = [], {}, set()
    common_config, common_project = {}, None
    for batch in schedule["batches"]:
        key = f"batch-{batch['batch']}"
        path = parent / key
        assert sha(plan / batch["dataset"]) == batch["datasetSha256"]
        report, records = compare(path, expected_sites=batch["sites"])
        report["kind"] = "confirmation-batch"
        report["limitations"] = ["One counterbalanced batch; use the prespecified combined analysis."]
        assert report["datasetSha256"] == batch["datasetSha256"]
        sites = {r["site"] for r in read(plan / batch["dataset"])["sites"]}
        assert not sites & covered
        covered |= sites
        evidence[key] = report
        for arm, values in report["metrics"].items():
            manifest = read(path / arm / "run.json")
            assert not manifest["failures"]
            current = read(path / arm / "dataset.json")["project"]
            if common_project is None:
                common_project = current
            assert current == common_project
            if arm not in metrics:
                common_config[arm] = values["config"]
                metrics[arm] = {k: 0 for k in ["sites", "recorded", "onTimeVerified", "rawVerified", "lateVerified", "elapsedMs", "budgetBlocked", "rankFailures", "stateCalls", "premiseCalls", "retrievalMs", "warmupMs"]}
                metrics[arm]["usage"] = {k: 0 for k in values["usage"]}
            assert values["config"] == common_config[arm]
            for k in metrics[arm]:
                if k != "usage":
                    metrics[arm][k] += values[k]
            for k in values["usage"]:
                metrics[arm]["usage"][k] += values["usage"][k]
        for r in records:
            arm = r["method"].rsplit(".", 1)[1]
            if r["onTimeVerified"]:
                success[arm].add(r["site"])
            public.append({"batch": batch["batch"], **r})
    assert covered == {s["site"] for s in dataset["sites"]}
    assert len(public) == 3072
    assert all(n == 1 for n in Counter((r["site"], r["method"]) for r in public).values())
    pairs = [{"a": a, "b": b, "role": role,
              **paired(dataset["sites"], success[a], success[b])}
             for a, b, role in [("cpu", "full", "primary"), ("neural", "full", "secondary"),
                                ("cpu", "neural", "secondary")]]
    for result, adjusted in zip(pairs[1:], holm([p["exactMcNemarP"] for p in pairs[1:]])):
        result["secondaryHolmMcNemarP"] = adjusted
    full = [r["metrics"]["full"]["upstreamSelector"] for r in evidence.values()]
    metrics["full"]["upstreamSelector"] = {k: sum(r[k] for r in full) for k in
                                           ["calls", "elapsedMs", "candidates", "unavailable", "fallbacks"]}
    errors = Counter()
    for r in full:
        errors.update(r["errors"])
    metrics["full"]["upstreamSelector"]["errors"] = dict(errors)
    for arm in metrics:
        metrics[arm]["config"] = common_config[arm]
        assert metrics[arm]["sites"] == metrics[arm]["recorded"] == 1024
        assert metrics[arm]["onTimeVerified"] == len(success[arm])
    assert all(v["memoryMax"] <= 16000000000 and v["swapMax"] == "0"
               for v in deployment["resources"].values())
    return {"schema": 1, "status": "complete", "kind": "prespecified-full-tactic-confirmation",
            "sites": 1024, "trials": 3072,
            "successfulTrialsIndependentlyReplayed": sum(m["rawVerified"] for m in metrics.values()),
            "metrics": metrics, "paired": pairs, "deployment": deployment,
            "datasetSha256": sha(plan / "dataset.json"), "scheduleSha256": sha(plan / "schedule.json"),
            "oldReservedEvaluationTrials": 0, "batches": evidence,
            "limitations": ["Stratified size-filtered Mathlib population, not uniform all-Mathlib sampling.",
                            "Single fresh Jev decision sequence per location and method.",
                            "Third-party neural training overlap is unknown.",
                            "Exact McNemar is an unclustered sensitivity check; primary inference uses stratified module bootstrap.",
                            "Six counterbalanced arm orders; disk caches persist, initialization excluded and reported."]}, public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report, public = export(args.parent, args.plan)
    trials = args.output.with_name(args.output.stem + "-trials.jsonl")
    trials.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in public))
    report["publicTrials"] = {"path": trials.name, "sha256": sha(trials)}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["metrics", "paired", "successfulTrialsIndependentlyReplayed"]}, indent=2))


if __name__ == "__main__":
    main()
