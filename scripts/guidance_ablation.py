"""Freeze and run the 256-goal current-system state-guidance ablation.

prepare performs source admission only. run makes paid Jev requests in one arm;
all four local baseline arms are credential-free. Both require a 16 GB cgroup.
"""
import argparse
from collections import defaultdict
import copy
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time

from confirmation_services import ROOT, read, require_bound, sha
from jevhammer_benchmark.cli import (build, fresh_output, phase, prepare_sources,
                                    project_info, rows, validate_visits, write_json)
from jevhammer_benchmark.resources import resource_snapshot

REFERENCE = ROOT / "datasets/full-leanhammer-confirmation-v1"
PROTOCOL = ROOT / "docs/guidance-ablation-protocol.md"
ARMS = {"jev": ("jev", 0), "fixed": ("fixed", 0),
        "random17": ("random", 17), "random29": ("random", 29), "random43": ("random", 43)}
ORDER_BASE = [[list(ARMS)[(v + shift) % 5] for v in (0, 1, 4, 2, 3)] for shift in range(5)]
ORDERS = ORDER_BASE + [list(reversed(order)) for order in ORDER_BASE]
METHOD = "LeanHammerComparison.strict"


def key(value):
    return hashlib.sha256(f"jevbench-state-guidance-v1:{value}".encode()).hexdigest()


def selection():
    """Outcome-free selection; no trial or report file is read here."""
    data = read(REFERENCE / "dataset.json")
    areas = defaultdict(list)
    for module in data["sources"]:
        areas[module.split(".")[1]].append(module)
    for group in areas.values():
        group.sort(key=key)
    chosen = []
    for i in range(max(map(len, areas.values()))):
        for area in sorted(areas):
            if i >= len(areas[area]) or len(chosen) == 256:
                continue
            module = areas[area][i]
            sites = sorted((s for s in data["sites"] if s["module"] == module), key=lambda s: key(s["site"]))
            chosen.extend(sites[:256 - len(chosen)])
    assert len(chosen) == len({s["declaration"] for s in chosen}) == 256
    modules = {s["module"] for s in chosen}
    assert len(modules) == 33 and len({m.split(".")[1] for m in modules}) == 17
    data["sites"] = chosen
    data["sources"] = {m: s for m, s in data["sources"].items() if m in modules}
    data["followup"] = {"kind": "proof-state-guidance-ablation-v1",
        "originalDatasetSha256": sha(REFERENCE / "dataset.json"),
        "previousProofExposure": "published confirmation and available-premise outcomes",
        "selection": "area-round-robin modules ordered by SHA256; boundary module truncated"}
    return data


def batch_data(data, i):
    group = set(sorted(data["sources"], key=key)[i::10])
    part = copy.deepcopy(data)
    part["sources"] = {m: s for m, s in data["sources"].items() if m in group}
    part["sites"] = [s for s in data["sites"] if s["module"] in group]
    return part


def freeze(data, output):
    write_json(output / "dataset.json", data)
    write_json(output / "holdouts.json", read(REFERENCE / "holdouts.json"))
    batches = []
    for i, order in enumerate(ORDERS):
        part = batch_data(data, i)
        path = output / f"batch-{i}.json"
        write_json(path, part)
        batches.append({"batch": i, "dataset": path.name, "datasetSha256": sha(path),
            "sites": len(part["sites"]), "modules": len(part["sources"]), "order": order,
            "maxRequests": 3 * len(part["sites"]), "maxInputTokens": 35000 * len(part["sites"])})
    write_json(output / "schedule.json", {"schema": 1, "sites": 256, "trials": 1280,
        "protocolSha256": sha(PROTOCOL), "arms": ARMS, "batches": batches})


def check_plan(plan):
    data, schedule = read(plan / "dataset.json"), read(plan / "schedule.json")
    expected = selection()
    expected["project"] = data["project"]
    if data != expected:
        raise ValueError("changed selected goals, source identities, or protocol metadata")
    if read(plan / "holdouts.json") != read(REFERENCE / "holdouts.json"):
        raise ValueError("changed original holdouts")
    if (schedule["sites"] != 256 or schedule["trials"] != 1280 or len(schedule["batches"]) != 10
            or schedule["protocolSha256"] != sha(PROTOCOL)
            or schedule["arms"] != {a: list(v) for a, v in ARMS.items()}):
        raise ValueError("changed protocol or treatment set")
    for i, b in enumerate(schedule["batches"]):
        part = batch_data(data, i)
        path = plan / f"batch-{i}.json"
        expected_batch = {"batch": i, "dataset": path.name, "datasetSha256": sha(path),
            "sites": len(part["sites"]), "modules": len(part["sources"]), "order": ORDERS[i],
            "maxRequests": 3 * len(part["sites"]), "maxInputTokens": 35000 * len(part["sites"])}
        if b != expected_batch or read(path) != part:
            raise ValueError("changed schedule, budget, or batch sites")
    return data, schedule


def prepare(args):
    output, project = fresh_output(args.output), args.project.resolve()
    data = selection()
    audit = {"status": "running", "realJevCalls": 0, "proofTrials": 0,
             "resources": {"initial": resource_snapshot()}}
    try:
        build(project, output, data["imports"][1:])
        data["project"] = project_info(project)
        prepare_sources(project, output, data["sources"], data["imports"])
        failures = phase(project, output, data, "admit", methods=(), threads=8,
                         lean_options=data.get("leanOptions", []))
        if failures:
            audit["failures"] = failures
            raise ValueError("source admission failed; no replacement allowed")
        validate_visits(data, rows(output / "visited.jsonl"))
        freeze(data, output)
        check_plan(output)
        audit.update(status="complete", visited=256, datasetSha256=sha(output / "dataset.json"))
    except BaseException as error:
        audit.update(status="incomplete", error=str(error))
        raise
    finally:
        audit["resources"]["final"] = resource_snapshot()
        write_json(output / "admission.json", audit)


def run(args):
    project, plan = args.project.resolve(), args.plan.resolve()
    data, schedule = check_plan(plan)
    if data["project"] != project_info(project):
        raise ValueError("project changed since admission")
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise ValueError("provide TYPESAFE_API_KEY through your environment or secret manager")
    output = fresh_output(args.output)
    audit = {"schema": 1, "status": "running", "kind": "proof-state-guidance-ablation-v1",
        "benchmarkFreeze": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "datasetSha256": sha(plan / "dataset.json"), "scheduleSha256": sha(plan / "schedule.json"),
        "holdoutsSha256": sha(plan / "holdouts.json"), "launcherSha256": sha(Path(__file__)),
        "protocolSha256": sha(PROTOCOL), "maxTotalJevCalls": 768, "maxReportedInputTokens": 8960000,
        "startedAt": time.time(), "resources": {"initial": resource_snapshot()}, "completedArms": []}
    try:
        for batch in schedule["batches"]:
            target = output / f"batch-{batch['batch']}"
            target.mkdir()
            for arm in batch["order"]:
                policy, seed = ARMS[arm]
                audit["current"] = {"batch": batch["batch"], "arm": arm, "sites": batch["sites"]}
                write_json(output / "deployment.json", audit)
                print(f"START batch {batch['batch'] + 1}/10 {arm} ({batch['sites']} goals)", flush=True)
                started = time.monotonic()
                env = dict(os.environ, JEVSELECTOR_HOLDOUTS=str(plan / "holdouts.json"), LEAN_NUM_THREADS="8")
                for variable in ("JEVSELECTOR_PUBLIC_INDEX", "JEVBENCH_NEURAL_URL"):
                    env.pop(variable, None)
                if policy != "jev":
                    env.pop("TYPESAFE_API_KEY", None)
                subprocess.run([sys.executable, "-m", "jevhammer_benchmark", "run", "--project", str(project),
                    "--dataset", str(plan / batch["dataset"]), "--methods", METHOD,
                    "--ranking-policy", policy, "--ranking-seed", str(seed), "--config", "{}",
                    "--max-requests", str(batch["maxRequests"]), "--max-input-tokens", str(batch["maxInputTokens"]),
                    "--threads", "8", "--heartbeats", "200000", "--memory-limit", "16000000000",
                    "--output", str(target / arm)], cwd=ROOT, env=env, check=True)
                summary = read(target / arm / "summary.json")
                if summary["status"] != "complete" or read(target / arm / "verification.json")["status"] != "complete":
                    raise ValueError("incomplete arm retained; no automatic retry")
                if policy != "jev" and any(summary["usage"].values()):
                    raise ValueError("a local baseline unexpectedly used the API")
                audit["completedArms"].append({"batch": batch["batch"], "arm": arm,
                    "wallSeconds": time.monotonic() - started,
                    "onTimeVerified": summary["methods"][METHOD]["onTimeVerified"]})
                write_json(output / "deployment.json", audit)
                print(f"DONE batch {batch['batch'] + 1}/10 {arm}: "
                      f"{summary['methods'][METHOD]['onTimeVerified']}/{batch['sites']}", flush=True)
        audit["status"] = "complete"
        audit.pop("current", None)
    except BaseException as error:
        audit.update(status="incomplete", error=str(error))
        raise
    finally:
        audit["finishedAt"] = time.time()
        audit["resources"]["final"] = resource_snapshot()
        write_json(output / "deployment.json", audit)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("prepare", "run"):
        p = sub.add_parser(action)
        p.add_argument("--project", type=Path, default=ROOT / "integrations/leanhammer")
        p.add_argument("--output", type=Path, required=True)
        if action == "run":
            p.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    require_bound()
    (prepare if args.action == "prepare" else run)(args)
