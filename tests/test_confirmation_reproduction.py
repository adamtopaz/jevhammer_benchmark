import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import confirmation_services as service
import reproduce_confirmation as reproduction
from reproduce_confirmation import REFERENCE, check_plan


class ReproductionTests(unittest.TestCase):
    def test_driver_finishes_all_arms_or_retains_incomplete_evidence(self):
        for fail_at in (None, 3):
            with self.subTest(fail_at=fail_at), tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / "run"
                args = argparse.Namespace(project=Path(directory), plan=REFERENCE,
                                          index=Path(directory) / "index.json", output=out, execute=True)
                args.index.write_text("fixture")
                calls, stopped = [], []

                @contextlib.contextmanager
                def fake_services(_args, path):
                    try:
                        yield {}
                    finally:
                        stopped.append(path)

                def fake_run(command, **kwargs):
                    calls.append(command)
                    if len(calls) == fail_at:
                        raise RuntimeError("trial process failed")
                    path = Path(command[command.index("--output") + 1])
                    path.mkdir()
                    (path / "summary.json").write_text(json.dumps({"status": "complete", "usage": {"attempts": 0}}))
                    (path / "verification.json").write_text(json.dumps({"status": "complete"}))

                with mock.patch.object(reproduction.argparse.ArgumentParser, "parse_args", return_value=args), \
                        mock.patch.object(reproduction, "require_bound"), \
                        mock.patch.object(reproduction, "project_info", return_value=service.read(REFERENCE / "dataset.json")["project"]), \
                        mock.patch.object(reproduction, "preflight"), \
                        mock.patch.object(reproduction, "services", side_effect=fake_services), \
                        mock.patch.object(reproduction, "resource_snapshot", return_value={"memoryMax": 16000000000, "swapMax": "0"}), \
                        mock.patch.object(reproduction.subprocess, "check_output", return_value="test-commit"), \
                        mock.patch.object(reproduction.subprocess, "run", side_effect=fake_run), \
                        mock.patch.dict(reproduction.os.environ, {"TYPESAFE_API_KEY": "test-only"}), \
                        contextlib.redirect_stdout(io.StringIO()):
                    if fail_at:
                        with self.assertRaisesRegex(RuntimeError, "trial process failed"):
                            reproduction.main()
                    else:
                        reproduction.main()
                audit = service.read(out / "deployment.json")
                self.assertEqual(len(calls), 3 if fail_at else 18)
                self.assertEqual(len(stopped), len(calls))
                self.assertEqual(audit["status"], "incomplete" if fail_at else "complete")
                order = [(b["batch"], a) for b in service.read(REFERENCE / "schedule.json")["batches"] for a in b["order"]]
                self.assertEqual([(r["batch"], r["arm"]) for r in audit["completedArms"]], order[:2] if fail_at else order)

    def test_resource_guard_rejects_unbounded_and_swap(self):
        for limits in (None, {"memoryMax": 17000000000, "swapMax": "0"},
                       {"memoryMax": 16000000000, "swapMax": "max"}):
            with mock.patch.object(service, "cgroup_limits", return_value=limits):
                with self.assertRaises(ValueError):
                    service.require_bound()

    def test_services_strip_credentials_and_cleanup_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = argparse.Namespace(upstream=root, validation=root / "validation.json", python=sys.executable)
            meta = service.read(service.NEURAL / "provenance.example.json")
            validation = {"passed": True, "model": meta["model"], "corpus": meta["corpus"],
                          "cpuEmbedSha256": service.sha(service.NEURAL / "cpu_embed.py")}
            args.validation.write_text(json.dumps(validation))
            first, second = mock.Mock(), mock.Mock()
            with mock.patch.object(service, "environment", return_value={"TYPESAFE_API_KEY": "test-only"}), \
                    mock.patch.object(service.socket, "socket") as socket, \
                    mock.patch.object(service.subprocess, "Popen", side_effect=[first, second]) as spawn, \
                    mock.patch.object(service, "wait_ready"), mock.patch.object(service, "stop") as stop:
                socket.return_value.__enter__.return_value.connect_ex.return_value = 1
                with self.assertRaisesRegex(RuntimeError, "trial failure"):
                    with service.services(args, root / "logs") as env:
                        self.assertEqual(env["TYPESAFE_API_KEY"], "test-only")
                        for call in spawn.call_args_list:
                            self.assertNotIn("TYPESAFE_API_KEY", call.kwargs["env"])
                        raise RuntimeError("trial failure")
                self.assertEqual(stop.call_args_list, [mock.call(second), mock.call(first)])
                for call in spawn.call_args_list:
                    self.assertTrue(call.kwargs["stdout"].closed)

    def test_frozen_plan_and_tamper_rejection(self):
        check_plan(REFERENCE)
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / "plan"
            shutil.copytree(REFERENCE, plan)
            schedule = json.loads((plan / "schedule.json").read_text())
            changed = copy.deepcopy(schedule)
            changed["batches"][0]["maxRequestsPerJevArm"] += 1
            (plan / "schedule.json").write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "schedule field"):
                check_plan(plan)
            (plan / "schedule.json").write_text(json.dumps(schedule))
            data = json.loads((plan / "dataset.json").read_text())
            data["sites"][0]["goal"] += " changed"
            (plan / "dataset.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "exact frozen sites"):
                check_plan(plan)
            data["sites"][0]["goal"] = json.loads((REFERENCE / "dataset.json").read_text())["sites"][0]["goal"]
            data["imports"].append("UnapprovedImports")
            (plan / "dataset.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "discovery field"):
                check_plan(plan)


if __name__ == "__main__":
    unittest.main()
