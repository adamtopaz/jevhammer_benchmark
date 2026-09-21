"""Admit only wholly elaborated modules from an outcome-free discovery pass.

Retains every rejected module and diagnostic checksum in compatibility metadata.
Never use this to drop failures from proof trials.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jevhammer_benchmark.cli import load_exclusions, rows, select_sites, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("discovery", type=Path)
    p.add_argument("exclusions", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    if (args.discovery / "trials.jsonl").exists():
        raise ValueError("refusing to filter a proof-trial run")
    original = json.loads((args.discovery / "dataset.json").read_text())
    failed = original["failures"]
    assert failed and len(failed) < len(original["sources"]) // 10
    data = copy.deepcopy(original)
    data["sources"] = {m: s for m, s in original["sources"].items() if m not in failed}
    complete = [r for r in rows(args.discovery / "discovery.jsonl") if r["module"] not in failed]
    owners, modules, _ = load_exclusions([args.exclusions])
    data["sites"] = select_sites(complete, 1024, 20260921,
                                  excluded_declarations=owners, excluded_modules=modules,
                                  max_per_declaration=1)
    assert len(data["sites"]) == 1024
    assert len({s["declaration"] for s in data["sites"]}) == 1024
    data["failures"], data["status"] = {}, "complete"
    data["discovered"] = len(complete)
    data["eligible"] = sum(r["eligible"] for r in complete)
    data["sampling"]["eligibleAfterExclusions"] = sum(r["eligible"] and r["module"] not in modules and
                                                       r["declaration"] not in owners for r in complete)
    details = {}
    for module in failed:
        log = args.discovery / "logs" / f"discover-{module}.log"
        messages = [s.split(": error", 1)[1] for s in log.read_text().splitlines() if ": error" in s]
        details[module] = {"logSha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                           "errors": messages}
    data["compatibility"] = {
        "originalDiscoverySha256": hashlib.sha256((args.discovery / "dataset.json").read_bytes()).hexdigest(),
        "originalStatus": original["status"], "candidateModules": len(original["sources"]),
        "admittedModules": len(data["sources"]), "excludedModules": details,
        "policy": "Whole-module source-elaboration failures excluded before any proof trials; fixed site seed/cap retained.",
        "realJevCalls": 0, "testedTacticCalls": 0}
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "dataset.json", data)
    write_json(args.output / "compatibility.json", data["compatibility"])
    print(json.dumps({"sites": len(data["sites"]), "owners": len(data["sites"]),
                      "admittedModules": len(data["sources"]), "excludedModules": list(failed)}))


if __name__ == "__main__":
    main()
