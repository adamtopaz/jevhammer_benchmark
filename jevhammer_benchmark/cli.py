"""Discovery, paired collection, independent replay, and offline reports.

Only the Python standard library is required. All Lean work occurs in the
explicit --project's Lake environment; no sibling checkout is consulted.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import sys
import time

from .resources import DEFAULT_LIMIT, ensure_bounded, resource_snapshot

SCHEMA = 1
CONFIG_KEYS = {"maxMillis", "maxNodes", "maxDepth", "maxCalls", "maxCandidates",
               "maxPremises", "premiseCount", "beamWidth", "tacticHeartbeats",
               "guidePremises", "refreshPremises", "model", "timeoutSeconds"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temp.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text())


def rows(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def valid_name(name):
    if not re.fullmatch(r"[^\W\d][\w']*(?:\.[^\W\d][\w']*)*", name, re.UNICODE):
        raise ValueError(f"expected an ordinary qualified Lean identifier: {name!r}")
    return name


def inject(source, imports):
    """Insert imports after an optional module header, skipping leading comments."""
    i = 0
    while i < len(source):
        if source[i].isspace():
            i += 1
        elif source.startswith("--", i):
            end = source.find("\n", i)
            i = len(source) if end < 0 else end + 1
        elif source.startswith("/-", i):
            depth, i = 1, i + 2
            while depth and i < len(source):
                if source.startswith("/-", i):
                    depth, i = depth + 1, i + 2
                elif source.startswith("-/", i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
            if depth:
                raise ValueError("unclosed leading Lean comment")
        else:
            break
    module = re.match(r"module\b[^\n]*(?:\n|$)", source[i:])
    position = i + module.end() if module else i
    prefix = "public meta import " if module else "import "
    addition = "".join(prefix + valid_name(name) + "\n" for name in imports)
    if position and source[position - 1] != "\n":
        addition = "\n" + addition
    return source[:position] + addition + source[position:], len(addition.encode())


def package_directory(project, manifest, package):
    if package["type"] == "path":
        root = project / package["dir"]
    else:
        directory = package["name"].replace("«", "").replace("»", "")
        root = project / manifest.get("packagesDir", ".lake/packages") / directory
    root = root / (package.get("subDir") or "")
    if not root.is_dir():
        raise ValueError(f"missing dependency source directory: {root}; run lake update")
    return root


def project_info(project):
    source_hashes = {}
    for directory, dirs, files in os.walk(project):
        directory = Path(directory)
        dirs[:] = sorted(d for d in dirs if d not in {
            ".git", ".lake", ".venv", "__pycache__", "cache", "artifacts", "runs"}
            and not any((directory / d / marker).exists() for marker in
                        [".jevbench-output", ".jevselector-output"]))
        for name in sorted(files):
            path = directory / name
            if path.suffix in {".lean", ".py"} or name in {"lakefile.toml", "lake-manifest.json", "lean-toolchain"}:
                source_hashes[str(path.relative_to(project))] = digest(path.read_bytes())
    manifest = read_json(project / "lake-manifest.json")
    dependency_hashes = {}
    for package in manifest["packages"]:
        root = package_directory(project, manifest, package)
        files = {}
        for folder, children, names in os.walk(root):
            children[:] = sorted(n for n in children if n not in {".lake", ".git"})
            for name in sorted(names):
                path = Path(folder) / name
                if path.suffix == ".lean":
                    files[str(path.relative_to(root))] = digest(path.read_bytes())
        dependency_hashes[package["name"]] = digest(json.dumps(files, sort_keys=True).encode())
    runner_hashes = {p.name: digest(p.read_bytes()) for p in Path(__file__).parent.glob("*.py")}
    return {"sources": source_hashes, "dependencySources": dependency_hashes,
            "runner": runner_hashes,
            "toolchain": (project / "lean-toolchain").read_text().strip(),
            "dependencies": read_json(project / "lake-manifest.json")}


def source_path(project, module):
    relative = Path(*valid_name(module).split(".")).with_suffix(".lean")
    candidates = [project / relative]
    manifest = read_json(project / "lake-manifest.json")
    for package in manifest["packages"]:
        root = package_directory(project, manifest, package)
        candidates.append(root / relative)
    available = [p for p in candidates if p.is_file()]
    if len(available) != 1:
        raise ValueError(f"expected one source for {module}, found {len(available)}; use --source MODULE=PATH")
    return available[0]


def fresh_output(path):
    path = path.absolute()
    path.mkdir(parents=True, exist_ok=False)
    (path / ".jevbench-output").touch()
    for name in ["settings", "logs", "sources", "work"]:
        (path / name).mkdir()
    return path


def process(command, project, log, env=None, timeout=600):
    with Path(log).open("w") as handle:
        child = subprocess.Popen(command, cwd=project, env=env, stdout=handle,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = child.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            raise
    if code:
        raise RuntimeError(f"command failed ({code}); see {log}")
    # Lean's panic! can return a default value and leave the process exit code
    # at zero. Such a run is not a clean measurement even if certificates replay.
    with Path(log).open(errors="replace") as handle:
        if any(line.startswith("PANIC at ") for line in handle):
            raise RuntimeError(f"Lean runtime panic; see {log}")


def lean_file(project, source, log, env=None, timeout=600, options=(), module_name="JevBenchImports"):
    # `lake env lean` alone does not load precompiled dependency plugins.
    # Lake's external-file setup supplies them; preserve the real source module
    # name so private declarations and generated auxiliaries retain their owner.
    setup_log = log.with_suffix(".setup.log")
    process(["lake", "setup-file", str(source)], project, setup_log, env, timeout)
    lines = [line for line in setup_log.read_text().splitlines() if line.startswith("{")]
    if not lines:
        raise RuntimeError(f"missing Lake module setup; see {setup_log}")
    setup = json.loads(lines[-1])
    setup["name"] = module_name
    for option in options:
        if option.startswith("-D"):
            setup.get("options", {}).pop(option[2:].split("=", 1)[0], None)
    setup_file = log.with_suffix(".setup.json")
    write_json(setup_file, setup)
    process(["lake", "env", "lean", "--setup", str(setup_file), *options, str(source)],
            project, log, env, timeout)


def build(project, output, imports):
    process(["lake", "build", "JevHammerBenchmark", *imports], project,
            output / "logs/build.log")


def imported_modules(project, output, imports):
    probe = output / "settings" / "InspectImports.lean"
    probe.write_text("".join("import " + valid_name(m) + "\n" for m in imports) +
        'open Lean Elab Command\nrun_cmd do\n  IO.println ("JEVBENCH_IMPORTS:" ++ (toJson ((← getEnv).header.moduleNames.map Name.toString)).compress)\n')
    log = output / "logs" / "imports.log"
    lean_file(project, probe, log)
    for line in log.read_text().splitlines():
        if line.startswith("JEVBENCH_IMPORTS:"):
            return set(json.loads(line.split(":", 1)[1]))
    raise RuntimeError("could not inspect benchmark imports")


def prepare_sources(project, output, sources, imports):
    for module, info in sources.items():
        path = project / info["path"]
        content = path.read_bytes()
        if digest(content) != info["sha256"]:
            raise ValueError(f"source changed: {module}")
        relative = Path(*module.split(".")).with_suffix(".lean")
        for folder in ["sources", "work"]:
            (output / folder / relative).parent.mkdir(parents=True, exist_ok=True)
        (output / "sources" / relative).write_bytes(content)
        instrumented, offset = inject(content.decode(), imports)
        (output / "work" / relative).write_text(instrumented)
        info["injectedBytes"] = offset


def phase(project, output, dataset, name, *, methods=(), overrides=None, mock=True,
          max_requests=0, max_tokens=0, heartbeats=200000, timeout=600, threads=2,
          certificates="", lean_options=()):
    failures = {}
    for module, source in dataset["sources"].items():
        sites = [r["site"] for r in dataset.get("sites", []) if r["module"] == module]
        if name != "discover" and not sites:
            continue
        print(f"{name}: {module} ({len(sites)} selected)", flush=True)
        settings = dict(phase=name, moduleName=module, outputDir=str(output),
                        injectedBytes=source["injectedBytes"], sites=sites,
                        owners=sorted({r["declaration"] for r in dataset.get("sites", [])}),
                        methods=list(methods), overrides=overrides or {}, mock=mock,
                        maxRequests=max_requests, maxInputTokens=max_tokens,
                        outerHeartbeats=heartbeats, certificates=str(certificates))
        config = output / "settings" / f"{name}-{module}.json"
        write_json(config, settings)
        env = dict(os.environ, JEVHAMMER_BENCH_CONFIG=str(config))
        if name != "run" or mock:
            env.pop("TYPESAFE_API_KEY", None)
        try:
            lean_file(project,
                      output / "work" / Path(*module.split(".")).with_suffix(".lean"),
                      output / "logs" / f"{name}-{module}.log", env, timeout,
                      [f"-j{threads}", "-M0", "--root", str(output / "work"),
                       "-DElab.async=false", "-DmaxHeartbeats=0",
                       "-Dlinter.tacticAnalysis.jevHammerBenchmark=true",
                       *["-D" + option for option in lean_options]], module)
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            failures[module] = str(error)
    return failures


def select_sites(discovered, count, seed):
    groups = defaultdict(list)
    for row in discovered:
        if row["eligible"]:
            groups[row["module"]].append(row)
    for group in groups.values():
        group.sort(key=lambda r: digest(f"{seed}:{r['site']}".encode()))
    selected = []
    while len(selected) < count and any(groups.values()):
        for module in sorted(groups):
            if groups[module] and len(selected) < count:
                selected.append(groups[module].pop(0))
    return selected


def discover(args):
    resources = ensure_bounded(args)
    project, output = args.project.absolute(), fresh_output(args.output)
    imports = list(dict.fromkeys(["JevHammerBenchmark", *map(valid_name, args.imports)]))
    build(project, output, args.imports)
    modules = list(args.modules)
    if args.modules_file:
        modules.extend(json.loads(args.modules_file.read_text()))
    sources = {name: source_path(project, name) for name in modules}
    for entry in args.source:
        name, path = entry.split("=", 1)
        sources[valid_name(name)] = project / path
    if not sources:
        raise ValueError("supply --modules, --modules-file, or --source")
    imported = imported_modules(project, output, imports)
    blocked = sorted(set(sources) & imported)
    if blocked:
        raise ValueError("source modules already imported by the harness/tactic set: " +
                         ", ".join(blocked) + "; choose modules outside that import closure")
    sources = {name: {"path": os.path.relpath(path, project), "sha256": digest(path.read_bytes())}
               for name, path in sources.items()}
    dataset = {"schema": SCHEMA, "project": project_info(project), "sources": sources,
               "imports": imports, "seed": args.seed, "leanOptions": args.lean_option}
    prepare_sources(project, output, sources, imports)
    failures = phase(project, output, dataset, "discover", threads=args.threads,
                     timeout=args.timeout, lean_options=args.lean_option)
    discovered = rows(output / "discovery.jsonl")
    dataset["sites"] = select_sites(discovered, args.count, args.seed)
    dataset["discovered"] = len(discovered)
    dataset["eligible"] = sum(r["eligible"] for r in discovered)
    dataset["failures"] = failures
    dataset["resources"] = {"initial": resources, "final": resource_snapshot()}
    dataset["status"] = "complete" if not failures and dataset["sites"] else "incomplete"
    write_json(output / "dataset.json", dataset)
    print(f"Selected {len(dataset['sites'])} of {dataset['eligible']} eligible locations")
    if dataset["status"] != "complete":
        raise RuntimeError(f"discovery incomplete; see {output / 'dataset.json'}")


def validate_dataset(dataset):
    if dataset.get("schema") != SCHEMA or dataset.get("status") != "complete":
        raise ValueError("expected a complete schema-1 dataset")
    ids = [r["site"] for r in dataset["sites"]]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("dataset sites must be nonempty and unique")


def validate_visits(dataset, visits):
    expected = {r["site"]: r for r in dataset["sites"]}
    observed = Counter(r["site"] for r in visits)
    if observed != Counter({key: 1 for key in expected}):
        raise ValueError("selected source locations were missing, duplicated, or changed")
    for row in visits:
        for key in ["module", "declaration", "goal", "byteStart", "byteEnd", "goalCount"]:
            if row[key] != expected[row["site"]][key]:
                raise ValueError(f"source context changed for {row['site']}: {key}")


def replay_run(project, directory, dataset, timeout=600, threads=2):
    successful = [r for r in rows(directory / "trials.jsonl") if r["solved"]]
    certfile = directory / "certificates.json"
    write_json(certfile, successful)
    attempt = 1
    while (directory / f"replay-{attempt}").exists():
        attempt += 1
    replay_dir = fresh_output(directory / f"replay-{attempt}")
    write_json(directory / "verification.json", {"directory": replay_dir.name, "status": "running"})
    prepare_sources(project, replay_dir, dataset["sources"], dataset["imports"])
    failures = phase(project, replay_dir, dataset, "replay", certificates=certfile,
                     timeout=timeout, threads=threads, lean_options=dataset.get("leanOptions", []))
    validate_visits(dataset, rows(replay_dir / "visited.jsonl"))
    checks = rows(replay_dir / "replay.jsonl")
    expected = Counter((r["site"], r["method"]) for r in successful)
    observed = Counter((r["site"], r["method"]) for r in checks)
    if failures or expected != observed or any(not r["verified"] for r in checks):
        raise RuntimeError("independent certificate replay failed or is incomplete")
    write_json(directory / "verification.json", {"directory": replay_dir.name, "status": "complete"})
    return checks


def run(args):
    resources = ensure_bounded(args)
    project, output = args.project.absolute(), fresh_output(args.output)
    dataset = read_json(args.dataset)
    validate_dataset(dataset)
    methods = list(dict.fromkeys(map(valid_name, args.methods)))
    overrides = json.loads(args.config)
    if not isinstance(overrides, dict) or set(overrides) - CONFIG_KEYS:
        raise ValueError("--config contains unknown JevHammer fields")
    if not args.mock and (not os.environ.get("TYPESAFE_API_KEY") or
                          args.max_requests <= 0 or args.max_input_tokens <= 0):
        raise ValueError("live runs require TYPESAFE_API_KEY and positive request/token budgets")
    build(project, output, dataset["imports"][1:])
    if project_info(project) != dataset["project"]:
        raise ValueError("project sources/dependencies changed since discovery; rediscover the dataset")
    prepare_sources(project, output, dataset["sources"], dataset["imports"])
    write_json(output / "dataset.json", dataset)
    write_json(output / "usage.json", {"attempts": 0, "inputTokens": 0, "outputTokens": 0, "unknownUsage": 0})
    manifest = {"schema": SCHEMA, "status": "running", "methods": methods,
                "configOverrides": overrides, "guidance": "mock" if args.mock else "jev",
                "datasetSha256": digest(Path(args.dataset).read_bytes()),
                "maxRequests": args.max_requests, "maxInputTokens": args.max_input_tokens,
                "outerHeartbeats": args.heartbeats, "threads": args.threads,
                "resources": {"initial": resources}, "startedAt": time.time()}
    write_json(output / "run.json", manifest)
    try:
        failures = phase(project, output, dataset, "run", methods=methods, overrides=overrides,
                         mock=args.mock, max_requests=args.max_requests, max_tokens=args.max_input_tokens,
                         heartbeats=args.heartbeats, timeout=args.timeout, threads=args.threads,
                         lean_options=dataset.get("leanOptions", []))
        manifest["failures"] = failures
        validate_visits(dataset, rows(output / "visited.jsonl"))
        expected = Counter((r["site"], m) for r in dataset["sites"] for m in methods)
        actual = Counter((r["site"], r["method"]) for r in rows(output / "trials.jsonl"))
        if failures or expected != actual:
            raise RuntimeError("collection incomplete; retained all partial records")
        replay_run(project, output, dataset, args.timeout, args.threads)
        manifest["status"] = "complete"
    except BaseException as error:
        manifest.update(status="incomplete", error=str(error))
        raise
    finally:
        manifest["resources"]["final"] = resource_snapshot()
        manifest["finishedAt"] = time.time()
        write_json(output / "run.json", manifest)
        report(output)


def report(directory):
    directory = Path(directory)
    manifest, dataset = read_json(directory / "run.json"), read_json(directory / "dataset.json")
    data = rows(directory / "trials.jsonl")
    verification = read_json(directory / "verification.json") if (directory / "verification.json").exists() else {}
    checks = rows(directory / verification["directory"] / "replay.jsonl") if verification.get("status") == "complete" else []
    verified = {(r["site"], r["method"]) for r in checks if r["verified"]}
    status = manifest["status"] if verification.get("status") == "complete" else "incomplete"
    successes, summaries = {}, {}
    for method in manifest["methods"]:
        trials = [r for r in data if r["method"] == method]
        raw = {r["site"] for r in trials if r["solved"] and (r["site"], method) in verified}
        ontime = {r["site"] for r in trials if r["onTime"] and r["site"] in raw}
        successes[method] = ontime
        summaries[method] = {"sites": len(dataset["sites"]), "recorded": len(trials),
                             "onTimeVerified": len(ontime), "rawVerified": len(raw),
                             "lateVerified": len(raw - ontime),
                             "elapsedMs": sum(r["elapsedMs"] for r in trials),
                             "budgetBlocked": sum(r.get("budgetBlocked", False) for r in trials),
                             "rankFailures": sum(r["stats"]["rankFailures"] for r in trials)}
    paired = []
    owners = defaultdict(list)
    for row in dataset["sites"]:
        owners[row["declaration"]].append(row["site"])
    for i, a in enumerate(manifest["methods"]):
        for b in manifest["methods"][i + 1:]:
            if status != "complete":
                continue
            gains, losses = successes[a] - successes[b], successes[b] - successes[a]
            rng, distribution = random.Random(0), []
            groups = list(owners.values())
            for _ in range(1000):
                sample = [site for group in rng.choices(groups, k=len(groups)) for site in group]
                distribution.append(sum((site in gains) - (site in losses) for site in sample) / len(sample))
            distribution.sort()
            paired.append({"a": a, "b": b, "gained": len(gains), "lost": len(losses),
                           "declarationBootstrap95": [distribution[25], distribution[974]]})
    result = {"schema": SCHEMA, "status": status, "guidance": manifest["guidance"],
              "methods": summaries, "paired": paired, "usage": read_json(directory / "usage.json")}
    write_json(directory / "summary.json", result)
    lines = ["# JevHammer benchmark", "", f"Status: **{status}**.", ""]
    if manifest["guidance"] == "mock":
        lines += ["**Offline mock ranking: infrastructure results, not measured Jev performance.**", ""]
    lines += ["| Method | On-time verified | Raw verified | Recorded trials | Goal time (s) |",
              "|---|---:|---:|---:|---:|"]
    for name, value in summaries.items():
        lines.append(f"| `{name}` | {value['onTimeVerified']}/{value['sites']} | {value['rawVerified']} | "
                     f"{value['recorded']} | {value['elapsedMs'] / 1000:.3f} |")
    lines += ["", "Successful proofs count only after source-bound offline replay.",
              "See summary.json for paired gains/losses, declaration-bootstrap intervals, and usage.",
              "Missing trials and replay failures remain visible in the run status and denominators."]
    (directory / "REPORT.md").write_text("\n".join(lines) + "\n")
    return result


def holdouts(args):
    dataset = read_json(args.dataset)
    validate_dataset(dataset)
    owners = sorted({r["declaration"] for r in dataset["sites"]})
    if args.output.exists():
        raise ValueError("refusing to overwrite a holdout manifest")
    write_json(args.output, {"schema": 1, "declarations": owners, "modules": [],
                             "datasetSha256": digest(Path(args.dataset).read_bytes())})


def split(args):
    dataset = read_json(args.dataset)
    validate_dataset(dataset)
    if not 0 < args.test_fraction < 1:
        raise ValueError("test fraction must be strictly between zero and one")
    owners = sorted({r["declaration"] for r in dataset["sites"]},
                    key=lambda n: digest(f"{args.seed}:{n}".encode()))
    if len(owners) < 2:
        raise ValueError("splitting requires at least two declarations")
    count = max(1, min(len(owners) - 1, round(len(owners) * args.test_fraction)))
    test = set(owners[:count])
    output = fresh_output(args.output)
    for name in ["development", "test"]:
        part = dict(dataset)
        part["sites"] = [r for r in dataset["sites"] if (r["declaration"] in test) == (name == "test")]
        part["partition"] = {"name": name, "seed": args.seed,
                             "parentSha256": digest(Path(args.dataset).read_bytes())}
        write_json(output / f"{name}.json", part)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    for name in ["discover", "run", "replay"]:
        p = sub.add_parser(name)
        p.add_argument("--project", type=Path, default=Path.cwd())
        p.add_argument("--memory-limit", type=int, default=DEFAULT_LIMIT)
        p.add_argument("--external-memory-limit", action="store_true",
                       help="memory already bounded by your container/job; recorded as externally managed")
        p.add_argument("--threads", type=int, default=2)
        p.add_argument("--timeout", type=int, default=600, help="per-module process timeout in seconds")
        if name != "replay":
            p.add_argument("--output", type=Path, required=True)
        if name == "discover":
            p.add_argument("--modules", nargs="*", default=[])
            p.add_argument("--modules-file", type=Path, help="JSON array of module names")
            p.add_argument("--source", action="append", default=[], help="MODULE=PATH relative to the project")
            p.add_argument("--import", dest="imports", action="append", default=[])
            p.add_argument("--lean-option", action="append", default=[], help="name=value, never credentials")
            p.add_argument("--count", type=int, default=32)
            p.add_argument("--seed", type=int, default=0)
        elif name == "run":
            p.add_argument("--dataset", type=Path, required=True)
            p.add_argument("--methods", nargs="+", default=["JevHammerBenchmark.Methods.sine"])
            p.add_argument("--config", default="{}", help="JSON JevHammer.Config overrides")
            p.add_argument("--mock", action="store_true", help="offline ranking for infrastructure tests only")
            p.add_argument("--max-requests", type=int, default=0)
            p.add_argument("--max-input-tokens", type=int, default=0)
            p.add_argument("--heartbeats", type=int, default=200000)
        else:
            p.add_argument("directory", type=Path)
    sub.add_parser("report").add_argument("directory", type=Path)
    p = sub.add_parser("holdouts")
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("split")
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--test-fraction", type=float, default=0.25)
    return result


def main():
    args = parser().parse_args()
    try:
        if args.command == "discover":
            discover(args)
        elif args.command == "run":
            run(args)
        elif args.command == "report":
            report(args.directory)
        elif args.command == "holdouts":
            holdouts(args)
        elif args.command == "split":
            split(args)
        else:
            ensure_bounded(args)
            directory, project = args.directory.absolute(), args.project.absolute()
            dataset = read_json(directory / "dataset.json")
            validate_dataset(dataset)
            if project_info(project) != dataset["project"]:
                raise ValueError("project changed since collection")
            try:
                replay_run(project, directory, dataset, args.timeout, args.threads)
            finally:
                report(directory)
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"jevbench: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
