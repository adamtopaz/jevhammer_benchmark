"""Reproduce the frozen 1,024-goal study, with fresh services for every arm.

Default: offline Lean/native-engine and holdout preflight only. --execute starts
the 3,072 live trials (paid Jev requests), followed by independent proof replay.
Always use a fresh output directory in one 16 GB, zero-swap cgroup.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from confirmation_services import ROOT, options, read, require_bound, services, sha
from jevhammer_benchmark.cli import fresh_output, lean_file, project_info, write_json
from jevhammer_benchmark.resources import resource_snapshot

REFERENCE = ROOT / "datasets/full-leanhammer-confirmation-v1"


def check_plan(plan):
    data, schedule = read(plan / "dataset.json"), read(plan / "schedule.json")
    reference, orders = read(REFERENCE / "dataset.json"), read(REFERENCE / "schedule.json")
    if data["status"] != "complete" or data["failures"]:
        raise ValueError("source admission must be complete")
    for key in ("schema", "imports", "seed", "leanOptions"):
        if data[key] != reference[key]:
            raise ValueError(f"changed discovery field: {key}")
    if data["sites"] != reference["sites"]:
        raise ValueError("reproduction must retain the exact frozen sites, owners and goal text")
    if {m: s["sha256"] for m, s in data["sources"].items()} != {
            m: s["sha256"] for m, s in reference["sources"].items()}:
        raise ValueError("source module hashes changed")
    for key in ("declarations", "modules"):
        if read(plan / "holdouts.json")[key] != read(REFERENCE / "holdouts.json")[key]:
            raise ValueError("training holdouts changed")
    if schedule["sites"] != 1024 or schedule["trials"] != 3072 or len(schedule["batches"]) != 6:
        raise ValueError("expected six batches and 3,072 trials")
    for batch, original in zip(schedule["batches"], orders["batches"]):
        for key in ("batch", "dataset", "sites", "modules", "order", "maxRequestsPerJevArm", "maxInputTokensPerJevArm"):
            if batch[key] != original[key]:
                raise ValueError(f"changed schedule field: {key}")
        part = read(plan / batch["dataset"])
        if sha(plan / batch["dataset"]) != batch["datasetSha256"]:
            raise ValueError("batch dataset checksum mismatch")
        original_part = read(REFERENCE / original["dataset"])
        if part["sites"] != original_part["sites"] or part["project"] != data["project"]:
            raise ValueError("batch sites or project identity changed")
        for key in ("schema", "imports", "seed", "leanOptions", "status", "failures"):
            if part[key] != original_part[key]:
                raise ValueError(f"changed batch discovery field: {key}")
        if {m: (s["sha256"], s["injectedBytes"]) for m, s in part["sources"].items()} != {
                m: (s["sha256"], s["injectedBytes"]) for m, s in original_part["sources"].items()}:
            raise ValueError("batch source identities changed")
    return data, schedule


def preflight(project, plan, index, output):
    report = read(index.parent / "report.json")
    if report["status"] != "complete" or report["indexSha256"] != sha(index):
        raise ValueError("selector preparation is incomplete or the artifact checksum changed")
    expected = {"algorithm": "statement-symbol-idf-v1", "modules": ["Mathlib"],
                "scopes": ["Mathlib"], "proofInformation": "none", "catalogPolicy": "public-constants"}
    if any(report["recipe"].get(k) != v for k, v in expected.items()):
        raise ValueError("selector preparation recipe differs from the confirmation")
    env = dict(os.environ, JEVSELECTOR_PUBLIC_INDEX=str(index), LEAN_NUM_THREADS="2")
    env.pop("TYPESAFE_API_KEY", None)
    source = output / "settings/ValidateArtifact.lean"
    source.write_text('import JevHammerBenchmark.Research\nimport Mathlib\nopen Lean Elab Command\nrun_cmd do\n'
        '  let idx ← JevHammerBenchmark.Research.publicIndex\n'
        '  let value ← IO.ofExcept (Json.parse (← IO.FS.readFile ' + json.dumps(str(plan / "holdouts.json")) + '))\n'
        '  let field ← IO.ofExcept (value.getObjVal? "declarations")\n'
        '  let names : Array String ← IO.ofExcept (fromJson? field)\n'
        '  discard <| idx.validateHoldouts (names.map String.toName)\n'
        '  liftTermElabM do idx.validateEnvironment\n'
        '  IO.println s!"JEVBENCH_VALIDATED_HOLDOUTS:{names.size}"\n')
    lean_file(project, source, output / "logs/holdouts.log", env, timeout=600,
              options=["-j2", "-M0", "-DmaxHeartbeats=0"])
    count = len(read(plan / "holdouts.json")["declarations"])
    if f"JEVBENCH_VALIDATED_HOLDOUTS:{count}" not in (output / "logs/holdouts.log").read_text():
        raise ValueError("holdout validation marker missing")
    lean_file(project, project / "Smoke.lean", output / "logs/engines.log", env,
              options=["-j8", "-M0", "-DElab.async=false"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options(parser)
    parser.add_argument("--project", type=Path, default=ROOT / "integrations/leanhammer")
    parser.add_argument("--plan", type=Path, default=REFERENCE)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    require_bound()
    project, plan, index = args.project.resolve(), args.plan.resolve(), args.index.resolve()
    data, schedule = check_plan(plan)
    if data["project"] != project_info(project):
        raise ValueError("project differs from admitted dataset; follow docs/reproducing-confirmation.md to re-admit it")
    if args.execute and not os.environ.get("TYPESAFE_API_KEY"):
        raise ValueError("set TYPESAFE_API_KEY through the environment for --execute")
    output = fresh_output(args.output)
    audit = {"schema": 1, "status": "running", "kind": "independent-reproduction",
             "benchmarkFreeze": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
             "datasetSha256": sha(plan / "dataset.json"), "scheduleSha256": sha(plan / "schedule.json"),
             "publicIndexSha256": sha(index), "holdoutsSha256": sha(plan / "holdouts.json"),
             "launcherSha256": sha(Path(__file__)), "servicesSha256": sha(ROOT / "scripts/confirmation_services.py"),
             "leanThreads": 8, "embeddingThreads": 2, "deadlineMs": 6000,
             "maxTotalJevCalls": 6144, "maxReportedInputTokens": 71680000,
             "resources": {"initial": resource_snapshot()}, "startedAt": time.time(), "completedArms": []}
    try:
        write_json(output / "deployment.json", audit)
        preflight(project, plan, index, output)
        if not args.execute:
            audit["status"] = "preflight-complete"
            print("Offline holdout and engine preflight passed; no Jev requests or proof trials were run.")
            return
        for batch in schedule["batches"]:
            target = output / f"batch-{batch['batch']}"
            target.mkdir()
            batch_audit = {"schema": 1, "status": "running", "batch": batch["batch"],
                           "order": batch["order"], "sites": batch["sites"],
                           "resources": {"initial": resource_snapshot()}, "completedArms": []}
            write_json(target / "deployment.json", batch_audit)
            for arm in batch["order"]:
                audit["current"] = {"batch": batch["batch"], "arm": arm, "sites": batch["sites"]}
                write_json(output / "deployment.json", audit)
                start = time.monotonic()
                print(f"START batch {batch['batch'] + 1} {arm}", flush=True)
                with services(args, target / f"service-{arm}") as env:
                    env.update(JEVSELECTOR_PUBLIC_INDEX=str(index), LEAN_NUM_THREADS="8")
                    subprocess.run([sys.executable, "-m", "jevhammer_benchmark", "run", "--project", str(project),
                        "--dataset", str(plan / batch["dataset"]), "--methods", "LeanHammerComparison." + arm,
                        "--config", "{}", "--max-requests", str(1 if arm == "full" else batch["maxRequestsPerJevArm"]),
                        "--max-input-tokens", str(1 if arm == "full" else batch["maxInputTokensPerJevArm"]),
                        "--threads", "8", "--heartbeats", "200000", "--memory-limit", "16000000000",
                        "--output", str(target / arm)], cwd=ROOT, env=env, check=True)
                    summary = read(target / arm / "summary.json")
                    if summary["status"] != "complete" or read(target / arm / "verification.json")["status"] != "complete":
                        raise ValueError("incomplete arm retained; no automatic retry or exclusion")
                    if arm == "full" and summary["usage"]["attempts"] != 0:
                        raise ValueError("full LeanHammer unexpectedly used Jev")
                completed = {"batch": batch["batch"], "arm": arm, "wallSeconds": time.monotonic() - start}
                audit["completedArms"].append(completed)
                batch_audit["completedArms"].append(completed)
                write_json(output / "deployment.json", audit)
                write_json(target / "deployment.json", batch_audit)
            batch_audit["status"] = "complete"
            batch_audit["resources"]["final"] = resource_snapshot()
            write_json(target / "deployment.json", batch_audit)
        audit["status"] = "complete"
        audit.pop("current", None)
    except BaseException as error:
        audit.update(status="incomplete", error=str(error))
        raise
    finally:
        audit["resources"]["final"] = resource_snapshot()
        audit["finishedAt"] = time.time()
        write_json(output / "deployment.json", audit)


if __name__ == "__main__":
    main()
