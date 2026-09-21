"""Freeze a discovered confirmation cohort into six counterbalanced batches.

Does not discover goals, fit a selector, start services or attempt proofs.
"""
import argparse
from collections import Counter
import copy
import hashlib
import itertools
import json
from pathlib import Path


def write(path, value):
    if path.exists():
        raise ValueError(f"refusing to overwrite {path}")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("discovery", type=Path)
    parser.add_argument("old_holdouts", type=Path)
    parser.add_argument("output", type=Path, help="existing module-plan directory")
    args = parser.parse_args()
    data = json.loads(args.discovery.read_text())
    sites = data["sites"]
    assert data["status"] == "complete" and not data["failures"]
    assert len(sites) == len({r['site'] for r in sites}) == len({r['declaration'] for r in sites}) == 1024
    exclusions = json.loads((args.output / "exclusions.json").read_text())
    excluded_owners = set(exclusions["declarations"])
    excluded_modules = set(exclusions["modules"])
    assert all(r["declaration"] not in excluded_owners and r["module"] not in excluded_modules for r in sites)
    data["confirmation"] = {"protocol": "docs/full-leanhammer-confirmation-protocol.md",
                            "discoverySha256": hashlib.sha256(args.discovery.read_bytes()).hexdigest(),
                            "previousProofExposure": "none in recorded trial/module exclusions",
                            "oldReservedEvaluationSitesUsed": 0}
    write(args.output / "dataset.json", data)
    old = json.loads(args.old_holdouts.read_text())
    write(args.output / "holdouts.json", {
        "schema": 1, "declarations": sorted(set(old["declarations"]) | {r["declaration"] for r in sites}),
        "modules": old.get("modules", []),
        "provenance": {"oldHoldoutsSha256": hashlib.sha256(args.old_holdouts.read_bytes()).hexdigest(),
                       "confirmationDatasetSha256": hashlib.sha256((args.output / "dataset.json").read_bytes()).hexdigest()}})
    modules = sorted({r["module"] for r in sites}, key=lambda m: hashlib.sha256(
        f"jevbench-full-confirmation-order-v1:{m}".encode()).hexdigest())
    orders = list(itertools.permutations(["cpu", "full", "neural"]))
    schedule = []
    for i, order in enumerate(orders):
        group = set(modules[i::6])
        part = copy.deepcopy(data)
        part["sources"] = {m: s for m, s in data["sources"].items() if m in group}
        part["sites"] = [s for s in sites if s["module"] in group]
        part["confirmation"]["batch"] = i
        path = args.output / f"batch-{i}.json"
        write(path, part)
        schedule.append({"batch": i, "dataset": path.name,
                         "datasetSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "sites": len(part["sites"]), "modules": len(group), "order": list(order),
                         "maxRequestsPerJevArm": 3 * len(part["sites"]),
                         "maxInputTokensPerJevArm": 35000 * len(part["sites"])})
    write(args.output / "schedule.json", {"schema": 1, "sites": 1024, "trials": 3072,
                                          "batches": schedule})
    write(args.output / "summary.json", {"sites": len(sites), "owners": len(sites),
                                         "modules": len(modules),
                                         "areas": dict(sorted(Counter(r["module"].split('.')[1] for r in sites).items())),
                                         "discovered": data["discovered"], "eligible": data["eligible"]})
    print(json.dumps(schedule, indent=2))


if __name__ == "__main__":
    main()
