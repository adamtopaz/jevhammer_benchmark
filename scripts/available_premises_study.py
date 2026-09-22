"""Prepare and run the four-arm available-premise sensitivity study.

Both phases require one aggregate 16 GB, zero-swap cgroup. Preparation only
re-admits the original source states; run makes paid Jev requests and replays
every successful proof. All output directories must be fresh.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from confirmation_services import ROOT, options, read, require_bound, services, sha
from jevhammer_benchmark.cli import (build, fresh_output, phase, prepare_sources,
                                    project_info, rows, validate_visits, write_json)
from jevhammer_benchmark.resources import resource_snapshot
from reproduce_confirmation import preflight

REFERENCE = ROOT / "datasets/full-leanhammer-confirmation-v1"
ORDERS = [["strict", "cpu", "full", "neural"], ["cpu", "neural", "strict", "full"],
          ["neural", "full", "cpu", "strict"], ["full", "strict", "neural", "cpu"]]


def freeze(data, output):
    reference = read(REFERENCE / "dataset.json")
    if data["sites"] != reference["sites"] or data["imports"] != reference["imports"]:
        raise ValueError("follow-up must preserve all original sites and imports")
    if data["status"] != "complete" or data["failures"]:
        raise ValueError("incomplete admission")
    write_json(output / "dataset.json", data)
    write_json(output / "holdouts.json", read(REFERENCE / "holdouts.json"))
    modules = sorted(data["sources"], key=lambda m: hashlib.sha256(
        f"jevbench-available-premises-v1:{m}".encode()).hexdigest())
    batches = []
    for i, order in enumerate(ORDERS):
        group = set(modules[i::4])
        part = copy.deepcopy(data)
        part["sources"] = {m: s for m, s in data["sources"].items() if m in group}
        part["sites"] = [s for s in data["sites"] if s["module"] in group]
        path = output / f"batch-{i}.json"
        write_json(path, part)
        batches.append({"batch": i, "dataset": path.name, "datasetSha256": sha(path),
                        "sites": len(part["sites"]), "modules": len(group), "order": order,
                        "maxRequestsPerJevArm": 3 * len(part["sites"]),
                        "maxInputTokensPerJevArm": 35000 * len(part["sites"])})
    write_json(output / "schedule.json", {"schema": 1, "sites": 1024, "trials": 4096,
                                          "batches": batches})


def prepare(args):
    output, project = fresh_output(args.output), args.project.resolve()
    data = read(REFERENCE / "dataset.json")
    audit = {"status": "running", "realJevCalls": 0, "proofTrials": 0,
             "originalDatasetSha256": sha(REFERENCE / "dataset.json"),
             "resources": {"initial": resource_snapshot()}}
    try:
        build(project, output, data["imports"][1:])
        data["project"] = project_info(project)
        prepare_sources(project, output, data["sources"], data["imports"])
        # An unknown non-discovery phase with no methods only records selected
        # states; the hook does not invoke any tested tactic or model.
        failures = phase(project, output, data, "admit", methods=(), threads=8,
                         lean_options=data.get("leanOptions", []))
        if failures:
            audit["failures"] = failures
            raise ValueError("source admission failed; no modules or sites may be dropped")
        validate_visits(data, rows(output / "visited.jsonl"))
        data["followup"] = {"protocol": "docs/available-premises-protocol.md",
                            "originalDatasetSha256": audit["originalDatasetSha256"],
                            "previousProofExposure": "published confirmation outcomes"}
        freeze(data, output)
        audit.update(status="complete", visited=len(data["sites"]),
                     datasetSha256=sha(output / "dataset.json"))
    except BaseException as error:
        audit.update(status="incomplete", error=str(error))
        raise
    finally:
        audit["resources"]["final"] = resource_snapshot()
        write_json(output / "admission.json", audit)


def check_plan(plan):
    data, schedule = read(plan / "dataset.json"), read(plan / "schedule.json")
    ref = read(REFERENCE / "dataset.json")
    if data["sites"] != ref["sites"] or data["imports"] != ref["imports"]:
        raise ValueError("changed original goals or imports")
    if data["leanOptions"] != ref["leanOptions"] or data["status"] != "complete" or data["failures"]:
        raise ValueError("changed options or incomplete dataset")
    if {m: s["sha256"] for m, s in data["sources"].items()} != {
            m: s["sha256"] for m, s in ref["sources"].items()}:
        raise ValueError("changed Mathlib source files")
    if read(plan / "holdouts.json") != read(REFERENCE / "holdouts.json"):
        raise ValueError("changed holdouts")
    if schedule["sites"] != 1024 or schedule["trials"] != 4096 or len(schedule["batches"]) != 4:
        raise ValueError("expected four batches and 4,096 trials")
    modules = sorted(data["sources"], key=lambda m: hashlib.sha256(
        f"jevbench-available-premises-v1:{m}".encode()).hexdigest())
    for i, batch in enumerate(schedule["batches"]):
        group = set(modules[i::4])
        sites = [s for s in data["sites"] if s["module"] in group]
        part = read(plan / batch["dataset"])
        if (batch["batch"] != i or batch["order"] != ORDERS[i] or
                batch["datasetSha256"] != sha(plan / batch["dataset"]) or
                batch["sites"] != len(sites) or batch["modules"] != len(group) or
                batch["maxRequestsPerJevArm"] != 3 * len(sites) or
                batch["maxInputTokensPerJevArm"] != 35000 * len(sites)):
            raise ValueError("changed schedule or budget")
        expected = copy.deepcopy(data)
        expected["sources"] = {m: s for m, s in data["sources"].items() if m in group}
        expected["sites"] = sites
        if part != expected:
            raise ValueError("batch differs from admitted dataset")
    return data, schedule


def run(args):
    project, plan, index = args.project.resolve(), args.plan.resolve(), args.index.resolve()
    data, schedule = check_plan(plan)
    if data["project"] != project_info(project):
        raise ValueError("project changed since admission")
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise ValueError("set TYPESAFE_API_KEY through the environment")
    output = fresh_output(args.output)
    audit = {"schema": 1, "status": "running", "kind": "available-premises-sensitivity",
             "benchmarkFreeze": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
             "datasetSha256": sha(plan / "dataset.json"), "scheduleSha256": sha(plan / "schedule.json"),
             "publicIndexSha256": sha(index), "holdoutsSha256": sha(plan / "holdouts.json"),
             "launcherSha256": sha(Path(__file__)), "startedAt": time.time(),
             "maxTotalJevCalls": 9216, "maxReportedInputTokens": 107520000,
             "resources": {"initial": resource_snapshot()}, "completedArms": []}
    try:
        write_json(output / "deployment.json", audit)
        preflight(project, plan, index, output)
        for batch in schedule["batches"]:
            target = output / f"batch-{batch['batch']}"
            target.mkdir()
            batch_audit = {"status": "running", "batch": batch["batch"],
                           "order": batch["order"], "completedArms": []}
            write_json(target / "deployment.json", batch_audit)
            for arm in batch["order"]:
                audit["current"] = {"batch": batch["batch"], "arm": arm, "sites": batch["sites"]}
                write_json(output / "deployment.json", audit)
                started = time.monotonic()
                print(f"START batch {batch['batch'] + 1} {arm}", flush=True)
                with services(args, target / f"service-{arm}") as env:
                    env.update(JEVSELECTOR_PUBLIC_INDEX=str(index), LEAN_NUM_THREADS="8",
                               JEVSELECTOR_HOLDOUTS=str(plan / "holdouts.json"))
                    subprocess.run([sys.executable, "-m", "jevhammer_benchmark", "run", "--project", str(project),
                        "--dataset", str(plan / batch["dataset"]), "--methods", "LeanHammerComparison." + arm,
                        "--config", "{}", "--max-requests", str(1 if arm == "full" else batch["maxRequestsPerJevArm"]),
                        "--max-input-tokens", str(1 if arm == "full" else batch["maxInputTokensPerJevArm"]),
                        "--threads", "8", "--heartbeats", "200000", "--memory-limit", "16000000000",
                        "--output", str(target / arm)], cwd=ROOT, env=env, check=True)
                    summary = read(target / arm / "summary.json")
                    if summary["status"] != "complete" or read(target / arm / "verification.json")["status"] != "complete":
                        raise ValueError("incomplete arm retained; no automatic retry")
                    if arm == "full" and summary["usage"]["attempts"] != 0:
                        raise ValueError("full LeanHammer unexpectedly called Jev")
                audit["completedArms"].append({"batch": batch["batch"], "arm": arm,
                                               "wallSeconds": time.monotonic() - started})
                batch_audit["completedArms"].append(arm)
                write_json(target / "deployment.json", batch_audit)
                write_json(output / "deployment.json", audit)
            batch_audit["status"] = "complete"
            write_json(target / "deployment.json", batch_audit)
        audit["status"] = "complete"
        audit.pop("current", None)
    except BaseException as error:
        audit.update(status="incomplete", error=str(error))
        raise
    finally:
        audit["finishedAt"] = time.time()
        audit["resources"]["final"] = resource_snapshot()
        write_json(output / "deployment.json", audit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("prepare", "run"):
        p = sub.add_parser(action)
        p.add_argument("--project", type=Path, default=ROOT / "integrations/leanhammer")
        p.add_argument("--output", type=Path, required=True)
        if action == "run":
            options(p)
            p.add_argument("--plan", type=Path, required=True)
            p.add_argument("--index", type=Path, required=True)
    args = parser.parse_args()
    require_bound()
    (prepare if args.action == "prepare" else run)(args)


if __name__ == "__main__":
    main()
