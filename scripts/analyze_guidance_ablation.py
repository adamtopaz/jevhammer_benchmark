"""Export matched ablation evidence, or recompute a public report offline.

Export: SCRIPT RUN PLAN OUTPUT.json
Check:  SCRIPT --check OUTPUT.json
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random

from guidance_ablation import ARMS, METHOD, ROOT, check_plan, read, rows, sha, write_json


def interval(values, alpha):
    values = sorted(values)
    n = len(values)
    return [values[int(alpha / 2 * n)], values[int((1 - alpha / 2) * n) - 1]]


def difference(sites, differences, resamples=20000, seed=20260924):
    """Keep all seed outcomes paired; resample whole modules within area."""
    expected = {s["site"] for s in sites}
    if set(differences) != expected or len(expected) != len(sites) or not sites:
        raise ValueError("differences must cover unique selected sites exactly")
    modules = defaultdict(list)
    for site in sites:
        modules[site["module"]].append(differences[site["site"]])
    strata = defaultdict(list)
    for module, values in sorted(modules.items()):
        strata[module.split(".")[1]].append((sum(values), len(values)))
    rng, samples = random.Random(seed), []
    for _ in range(resamples):
        total, count = 0, 0
        for group in strata.values():
            for value, n in rng.choices(group, k=len(group)):
                total += value
                count += n
        samples.append(total / count)
    return {"difference": sum(differences[s["site"]] for s in sites) / len(sites),
        "moduleStratifiedBootstrap95": interval(samples, .05),
        "moduleStratifiedBootstrap97_5": interval(samples, .025),
        "resamples": resamples, "seed": seed, "modules": len(modules), "areas": len(strata),
        "singleModuleAreas": sorted(a for a, g in strata.items() if len(g) == 1)}


def analyze(sites, records):
    expected = {s["site"] for s in sites}
    assert len(sites) == len(expected) == 256
    assert len(records) == 1280
    assert Counter((r["site"], r["arm"]) for r in records) == Counter(
        {(s, a): 1 for s in expected for a in ARMS})
    outcomes, metrics = {}, {}
    for arm in ARMS:
        group = [r for r in records if r["arm"] == arm]
        assert all(r["rawSolved"] == r["independentlyReplayed"] for r in group)
        assert all(r["onTimeVerified"] == (r["rawSolved"] and r["elapsedMs"] <= 6000) for r in group)
        outcomes[arm] = {r["site"] for r in group if r["onTimeVerified"]}
        after = [r for r in group if r["onTimeVerified"] and r["stats"]["stateRankCalls"]]
        metrics[arm] = {"sites": 256, "onTimeVerified": len(outcomes[arm]),
            "rawVerified": sum(r["rawSolved"] for r in group),
            "lateVerified": sum(r["rawSolved"] and not r["onTimeVerified"] for r in group),
            "elapsedMs": sum(r["elapsedMs"] for r in group),
            "stateRankCalls": sum(r["stats"]["stateRankCalls"] for r in group),
            "rankFailures": sum(r["stats"]["rankFailures"] for r in group),
            "budgetBlocked": sum(r["budgetBlocked"] for r in group),
            "solvesWithoutRanking": len(outcomes[arm]) - len(after),
            "solvesAfterRanking": len(after),
            "solvesWithAllRankingsFailed": sum(r["stats"]["rankFailures"] == r["stats"]["rankCalls"] for r in after)}
    comparisons = []
    for other in ("fixed", "randomMean", "random17", "random29", "random43"):
        if other == "randomMean":
            deltas = {s: (3 * (s in outcomes["jev"]) - sum(s in outcomes[a] for a in ARMS if a.startswith("random"))) / 3
                      for s in expected}
            binary = {}
        else:
            deltas = {s: int(s in outcomes["jev"]) - int(s in outcomes[other]) for s in expected}
            binary = {"gained": len(outcomes["jev"] - outcomes[other]),
                      "lost": len(outcomes[other] - outcomes["jev"]),
                      "bothSolved": len(outcomes["jev"] & outcomes[other])}
        comparisons.append({"a": "jev", "b": other,
            "role": "co-primary" if other in ("fixed", "randomMean") else "descriptive",
            **binary, **difference(sites, deltas)})
    return {"metrics": metrics, "paired": comparisons,
            "randomMeanSolves": sum(len(outcomes[a]) for a in ARMS if a.startswith("random")) / 3,
            "successfulTrialsIndependentlyReplayed": sum(m["rawVerified"] for m in metrics.values())}


def export(parent, plan, output):
    data, schedule = check_plan(plan)
    deployment = read(parent / "deployment.json")
    assert deployment["status"] == "complete"
    assert deployment["datasetSha256"] == sha(plan / "dataset.json")
    assert deployment["scheduleSha256"] == sha(plan / "schedule.json")
    assert [(r["batch"], r["arm"]) for r in deployment["completedArms"]] == [
        (b["batch"], a) for b in schedule["batches"] for a in b["order"]]
    public, decisions, preparations, evidence = [], [], [], {}
    usage = {a: Counter() for a in ARMS}
    request_errors, request_count = Counter(), 0
    config = None
    first_decisions, fits = defaultdict(dict), defaultdict(dict)
    for batch in schedule["batches"]:
        part = read(plan / batch["dataset"])
        expected = {s["site"] for s in part["sites"]}
        for arm in batch["order"]:
            root = parent / f"batch-{batch['batch']}" / arm
            manifest, summary, verification = [read(root / n) for n in ("run.json", "summary.json", "verification.json")]
            policy, seed = ARMS[arm]
            assert manifest["status"] == summary["status"] == verification["status"] == "complete"
            assert not manifest["failures"] and manifest["configOverrides"] == {}
            assert manifest["methods"] == [METHOD] and manifest["threads"] == 8 and manifest["outerHeartbeats"] == 200000
            assert manifest["guidance"] == policy and manifest["rankingSeed"] == seed
            assert manifest["datasetSha256"] == batch["datasetSha256"] and read(root / "dataset.json") == part
            assert manifest["maxRequests"] == batch["maxRequests"] and manifest["maxInputTokens"] == batch["maxInputTokens"]
            raw = rows(root / "trials.jsonl")
            assert len(raw) == len(expected) and {r["site"] for r in raw} == expected
            checks = rows(root / verification["directory"] / "replay.jsonl")
            assert all(r["verified"] and r["method"] == METHOD for r in checks)
            verified = {r["site"] for r in checks}
            assert len(verified) == len(checks) and verified == {r["site"] for r in raw if r["solved"]}
            ranking_rows = rows(root / "rankings.jsonl")
            assert len(ranking_rows) == sum(r["stats"]["stateRankCalls"] for r in raw)
            counts = Counter(r["site"] for r in ranking_rows)
            for r in ranking_rows:
                assert r["policy"] == policy and r["seed"] == seed and r["task"] == "continuations"
                if "order" in r:
                    assert sorted(r["order"]) == list(range(r["choiceCount"]))
                    if policy == "fixed":
                        assert r["order"] == list(range(r["choiceCount"]))
                if r["invocation"] == 0:
                    first_decisions[r["site"]][arm] = (r["stateHash"], r["choicesHash"])
                decisions.append({k: v for k, v in r.items() if k != "error"}
                                 | {"arm": arm, "batch": batch["batch"], "failed": "error" in r})
            for r in raw:
                assert r["method"] == METHOD and r["guidance"] == policy and r["rankingSeed"] == seed
                assert r["stats"]["premiseRankCalls"] == r["stats"]["selectorRankCalls"] == 0
                assert r["stats"]["stateRankCalls"] == r["stats"]["rankCalls"] == counts[r["site"]]
                assert r["stats"]["rankCalls"] <= 3 and not r["selectorGuidance"]
                if policy != "jev":
                    assert r["stats"]["rankFailures"] == 0
                if config is None:
                    config = r["config"]
                assert r["config"] == config and config["maxMillis"] == 6000 and not config["guidePremises"]
                public.append({k: r[k] for k in ("site", "module", "declaration", "elapsedMs", "stats", "budgetBlocked")}
                    | {"arm": arm, "batch": batch["batch"], "rawSolved": r["solved"],
                       "independentlyReplayed": r["site"] in verified,
                       "onTimeVerified": bool(r["onTime"] and r["site"] in verified)})
            assert summary["methods"][METHOD]["onTimeVerified"] == sum(r["onTime"] and r["site"] in verified for r in raw)
            if policy != "jev":
                assert not any(summary["usage"].values()) and not (root / "decisions.jsonl").exists()
            else:
                requests = rows(root / "decisions.jsonl")
                assert len(requests) == summary["usage"]["attempts"]
                request_count += len(requests)
                reported = [(r["usage"] or {}) for r in requests]
                assert sum(u.get("input_tokens") or 0 for u in reported) == summary["usage"]["inputTokens"]
                assert sum(u.get("output_tokens") or 0 for u in reported) == summary["usage"]["outputTokens"]
                assert sum(u.get("input_tokens") is None or u.get("output_tokens") is None for u in reported) == summary["usage"]["unknownUsage"]
                for request in requests:
                    error = request["response"].get("error")
                    if error:
                        # Publish categories, never arbitrary server-response text.
                        category = "HTTP 400" if error == "TypeSafe HTTP 400" else (
                            "rank probabilities do not sum to one" if error.startswith(
                                "TypeSafe response: rank: probabilities must sum to 1") else "other API error")
                        request_errors[category] += 1
            usage[arm].update(summary["usage"])
            warmups = rows(root / "warmup.jsonl")
            assert Counter(w["module"] for w in warmups) == Counter({m: 1 for m in part["sources"]})
            for w in warmups:
                p = w["provenance"]
                assert p["kind"] == "available-imported-statements-v1" and p["holdoutOwners"] == 1212
                assert p["proofInformation"] == "none" and w["module"] not in p["importedModules"]
                fits[w["module"]][arm] = p
                preparations.append({"arm": arm, "module": w["module"], "elapsedMs": w["elapsedMs"]})
            for resource in manifest["resources"].values():
                assert resource["memoryMax"] <= 16000000000 and resource["swapMax"] == "0"
            evidence[f"batch-{batch['batch']}/{arm}"] = {n: sha(root / n) for n in
                ("run.json", "dataset.json", "summary.json", "verification.json", "trials.jsonl",
                 "usage.json", "warmup.jsonl", verification["directory"] + "/replay.jsonl")}
            if (root / "rankings.jsonl").exists():
                evidence[f"batch-{batch['batch']}/{arm}"]["rankings.jsonl"] = sha(root / "rankings.jsonl")
            if (root / "decisions.jsonl").exists():
                evidence[f"batch-{batch['batch']}/{arm}"]["decisions.jsonl"] = sha(root / "decisions.jsonl")
    assert all(set(v) == set(ARMS) and all(p == v["jev"] for p in v.values()) for v in fits.values())
    result = analyze(data["sites"], public)
    trials_path = output.with_name(output.stem + "-trials.jsonl")
    rankings_path = output.with_name(output.stem + "-rankings.jsonl")
    preparation_path = output.with_name(output.stem + "-preparation.json")
    if any(p.exists() for p in (output, trials_path, rankings_path, preparation_path)):
        raise ValueError("refusing to overwrite an existing report")
    trials_path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in public))
    rankings_path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in decisions))
    write_json(preparation_path, {"schema": 1, "identicalAcrossArms": True,
        "modules": {m: values["jev"] for m, values in fits.items()}})
    diagnostics = {a: {"bothReachFirstDecision": sum(a in d and "jev" in d for d in first_decisions.values()),
                       "identicalFirstChoices": sum(a in d and "jev" in d and d[a] == d["jev"] for d in first_decisions.values())}
                   for a in ARMS if a != "jev"}
    report = {"schema": 1, "kind": "proof-state-guidance-ablation-v1", "status": "complete", "sites": 256,
        "trials": 1280, **result, "config": config, "usage": usage, "preparation": preparations,
        "firstDecisionDiagnostics": diagnostics, "deployment": deployment, "evidenceSha256": evidence,
        "analysisSha256": sha(Path(__file__)),
        "requestAudit": {"recordedJevRequests": request_count, "responseErrors": request_errors,
                         "usageReconciledWithRequestRecords": True},
        "publicTrials": {"path": trials_path.name, "sha256": sha(trials_path)},
        "publicRankings": {"path": rankings_path.name, "sha256": sha(rankings_path)},
        "publicPreparation": {"path": preparation_path.name, "sha256": sha(preparation_path)},
        "selectedSites": [{k: s[k] for k in ("site", "module", "declaration")} for s in data["sites"]],
        "limitations": ["First pass on previously exposed goals, with one Jev/fixed run and three fixed random seeds.",
            "Cluster subsample of 33 modules/17 areas, including one single-module stratum; not all Mathlib.",
            "Random-average intervals condition on the three seeds; model/run variability is not fully estimated.",
            "Two co-primary comparisons use 97.5% intervals; 95% intervals and per-seed contrasts are descriptive.",
            "Jev pretraining overlap unknown. Initialization excluded from goal time and reported separately.",
            "API failures and timing differences are retained; a call preceding a solve is not causal attribution."]}
    write_json(output, report)
    return report


def check(path):
    report = read(path)
    for field in ("publicTrials", "publicRankings", "publicPreparation"):
        assert sha(path.parent / report[field]["path"]) == report[field]["sha256"]
    actual = analyze(report["selectedSites"], rows(path.parent / report["publicTrials"]["path"]))
    assert all(report[k] == v for k, v in actual.items())
    fits = read(path.parent / report["publicPreparation"]["path"])["modules"]
    assert set(fits) == {s["module"] for s in report["selectedSites"]}
    assert Counter((p["module"], p["arm"]) for p in report["preparation"]) == Counter(
        {(m, a): 1 for m in fits for a in ARMS})
    assert all(m not in p["importedModules"] and p["holdoutOwners"] == 1212
               and p["proofInformation"] == "none" for m, p in fits.items())
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("parent", nargs="?", type=Path)
    p.add_argument("plan", nargs="?", type=Path)
    p.add_argument("output", nargs="?", type=Path)
    p.add_argument("--check", type=Path)
    args = p.parse_args()
    if args.check:
        report = check(args.check)
    else:
        if not all((args.parent, args.plan, args.output)):
            p.error("provide RUN PLAN OUTPUT.json, or --check REPORT.json")
        report = export(args.parent, args.plan, args.output)
    print(json.dumps({"verified": True, "coverage": {a: m["onTimeVerified"] for a, m in report["metrics"].items()},
                      "paired": report["paired"]}, indent=2))
