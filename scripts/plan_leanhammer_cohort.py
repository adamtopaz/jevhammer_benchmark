"""Freeze an outcome-blind module plan for the full LeanHammer confirmation.

Inputs are explicit files/directories; no private paths or neural services are
needed. A trial root must contain public runner records with module/owner names.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mathlib", type=Path, required=True)
    parser.add_argument("--imports-log", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--old-cohort", type=Path, required=True)
    parser.add_argument("--areas-recipe", type=Path, required=True)
    parser.add_argument("--trial-root", type=Path, action="append", default=[])
    parser.add_argument("--modules-per-area", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prior = json.loads(args.prior.read_text())
    old = json.loads(args.old_cohort.read_text())
    owners, modules = set(prior["declarations"]), set(prior["modules"])
    modules.update(old["sources"])
    owners.update(s["declaration"] for s in old["sites"])
    records = []
    for root in args.trial_root:
        for path in sorted(root.rglob("trials.jsonl")):
            count = 0
            with path.open() as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    # Read identifiers only; never consult proof outcomes.
                    modules.add(row["module"])
                    owners.add(row["declaration"])
                    count += 1
            records.append({"path": str(path.relative_to(root)), "sha256": sha(path),
                            "records": count})
    lines = args.imports_log.read_text().splitlines()
    closure = set(json.loads(next(s for s in lines if s.startswith("JEVBENCH_IMPORTS:"))
                             .split(":", 1)[1]))
    blocked = modules | closure
    areas = [r["area"] for r in json.loads(args.areas_recipe.read_text())["areas"]]
    selected, candidates = [], {}
    seed = "jevbench-full-confirmation-v1"
    for area in areas:
        pool = []
        for path in (args.mathlib / "Mathlib" / area).rglob("*.lean"):
            name = ".".join(path.relative_to(args.mathlib).with_suffix("").parts)
            if name in blocked or not 3000 <= path.stat().st_size <= 30000:
                continue
            source = path.read_text()
            by_count = len(re.findall(r"\bby\b", source))
            if by_count < 12 or any(s in source for s in ["deprecated_module", "assert_not_exists"]):
                continue
            pool.append({"module": name, "sourceSha256": sha(path),
                         "sourceBytes": path.stat().st_size, "byTokens": by_count})
        pool.sort(key=lambda r: hashlib.sha256(f"{seed}:{r['module']}".encode()).hexdigest())
        if not pool:
            raise ValueError(f"no available modules in {area}")
        candidates[area] = pool
        selected.extend(r["module"] for r in pool[:args.modules_per_area])
    args.output.mkdir(parents=True, exist_ok=False)
    write(args.output / "modules.json", selected)
    write(args.output / "exclusions.json", {
        "schema": 1, "declarations": sorted(owners), "modules": sorted(modules),
        "provenance": {"priorSha256": sha(args.prior), "oldCohortSha256": sha(args.old_cohort),
                       "trialRecords": records}})
    write(args.output / "recipe.json", {
        "schema": 1, "name": "full-leanhammer-confirmation-v1", "moduleSeed": seed,
        "modulesPerArea": args.modules_per_area, "minSourceBytes": 3000,
        "maxSourceBytes": 30000, "minLexicalByTokens": 12,
        "excludeText": ["deprecated_module", "assert_not_exists"],
        "importClosureSha256": hashlib.sha256(json.dumps(sorted(closure)).encode()).hexdigest(),
        "importsLogSha256": sha(args.imports_log), "candidateOrder": candidates,
        "requestedSites": 1024, "siteSeed": 20260921, "maxPerDeclaration": 1})
    print(json.dumps({"modules": len(selected), "areas": len(areas),
                      "excludedModules": len(modules), "excludedOwners": len(owners)}))


if __name__ == "__main__":
    main()
