"""Pinned, CPU-only neural services for the confirmation reproduction.

Run inside one 16 GB, zero-swap cgroup. No credentials or private checkout paths
are embedded. --validate checks inference against 32 fixed corpus vectors;
otherwise run a command after -- with fresh services and guaranteed cleanup.
"""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
NEURAL = ROOT / "integrations/neural"
sys.path.insert(0, str(ROOT))
from jevhammer_benchmark.resources import cgroup_limits


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require_bound():
    limits = cgroup_limits()
    if not limits or limits["memoryMax"] > 16000000000 or limits["swapMax"] != "0":
        raise ValueError("run inside one 16,000,000,000-byte, zero-swap cgroup")


def options(parser):
    parser.add_argument("--upstream", type=Path, required=True, help="pinned lean-premise-server checkout")
    parser.add_argument("--data", type=Path, required=True, help="persistent corpus/model cache")
    parser.add_argument("--validation", type=Path, required=True, help="embedding validation JSON")
    parser.add_argument("--python", default=sys.executable, help="CPU neural environment's Python")


def environment(args):
    require_bound()
    meta = read(NEURAL / "provenance.example.json")
    upstream = args.upstream.resolve()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=upstream)
    if revision != meta["serverRevision"] or dirty:
        raise ValueError("premise-server must be clean and at the pinned revision")
    expected = dict(line.split("==", 1) for line in
                    (NEURAL / "requirements-cpu.lock").read_text().splitlines() if line)
    probe = "import importlib.metadata as m,json,sys; print(json.dumps({n:m.version(n) for n in sys.argv[1:]}))"
    installed = json.loads(subprocess.check_output([args.python, "-c", probe, *expected], text=True))
    if installed != expected:
        raise ValueError("neural Python packages differ from requirements-cpu.lock")
    data = args.data.resolve()
    data.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(DATA_DIR=str(data), DATA_REPO=meta["corpus"]["id"],
               DATA_REVISION=meta["corpus"]["revision"], MODEL_ID=meta["model"]["id"],
               MODEL_REVISION="v4.33.0", HF_HOME=str(data / "hf"), HF_HUB_DISABLE_TELEMETRY="1",
               EMBED_SERVICE_URL="http://127.0.0.1:18081", EMBED_PORT="18081", EMBED_SERVICE_TIMEOUT="",
               EMBED_SERVICE_MAX_CONCURRENT_INPUTS="32", LRU_CACHE_SIZE="131072",
               MAX_NEW_PREMISES="2048", MAX_CLIENT_BATCH_SIZE="32", MAX_K="1024",
               DTYPE="float32", OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2",
               JEVBENCH_PREMISE_SERVER=str(upstream),
               JEVBENCH_EMBED_VALIDATION=str(args.validation.resolve()),
               JEVBENCH_NEURAL_URL="http://127.0.0.1:18080")
    return env


def validate(args):
    env = environment(args)
    env.pop("TYPESAFE_API_KEY", None)
    if args.validation.exists():
        raise ValueError("validation output exists; choose a fresh path")
    args.validation.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([args.python, str(NEURAL / "validate_embeddings.py")], env=env, check=True)


def wait_ready(process, url, seconds=300):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"service exited {process.returncode}; inspect retained logs")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        time.sleep(.2)
    raise TimeoutError(f"service startup timed out: {url}")


def stop(process):
    # Also remove owned descendants if the service leader has already exited.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


@contextlib.contextmanager
def services(args, output):
    env = environment(args)
    meta, validation = read(NEURAL / "provenance.example.json"), read(args.validation)
    if not (validation.get("passed") and validation.get("model") == meta["model"] and
            validation.get("corpus") == meta["corpus"] and
            validation.get("cpuEmbedSha256") == sha(NEURAL / "cpu_embed.py")):
        raise ValueError("run --validate for this pinned model, corpus and CPU embedding code first")
    for port in (18080, 18081):
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                raise ValueError(f"port {port} is occupied; refusing to reuse or stop another service")
    output.mkdir(parents=True, exist_ok=False)
    meta["deployment"] = {"device": "cpu", "dtype": "float32", "embeddingThreads": 2,
                          "leanThreads": 8, "embeddingValidation": validation,
                          "memoryLimitBytes": 16000000000, "swapLimitBytes": 0,
                          "cpuEmbedSha256": sha(NEURAL / "cpu_embed.py"),
                          "pythonLockSha256": sha(NEURAL / "requirements-cpu.lock")}
    provenance = output / "provenance.json"
    provenance.write_text(json.dumps(meta, indent=2) + "\n")
    env["JEVBENCH_NEURAL_PROVENANCE"] = str(provenance.resolve())
    service_env = env.copy()
    service_env.pop("TYPESAFE_API_KEY", None)
    processes, logs = [], []
    try:
        for name, command, cwd, url in [
            ("embed", [args.python, str(NEURAL / "cpu_embed.py")], ROOT,
             "http://127.0.0.1:18081/health"),
            ("premises", [args.python, "-m", "uvicorn", "main:app", "--host", "127.0.0.1",
                          "--port", "18080", "--workers", "1"], args.upstream.resolve() / "app",
             "http://127.0.0.1:18080/max-new-premises"),
        ]:
            log = (output / f"{name}.log").open("w")
            logs.append(log)
            process = subprocess.Popen(command, cwd=cwd, env=service_env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            processes.append(process)
            wait_ready(process, url)
        yield env
    finally:
        for process in reversed(processes):
            stop(process)
        for log in logs:
            log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options(parser)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--output", type=Path, help="fresh service logs/provenance directory")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.validate:
        validate(args)
        return
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not args.output:
        parser.error("supply --output and a command after --, or use --validate")
    with services(args, args.output) as env:
        subprocess.run(command, env=env, check=True)


if __name__ == "__main__":
    main()
