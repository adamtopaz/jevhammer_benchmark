import collections
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from available_premises_study import ORDERS, REFERENCE, check_plan, freeze
import available_premises_study as study


class AvailableStudyTests(unittest.TestCase):
    def test_driver_completes_or_retains_failed_arm_without_retry(self):
        for fail_at in (None, 3):
            with self.subTest(fail_at=fail_at), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                plan = root / "plan"
                plan.mkdir()
                data = json.loads((REFERENCE / "dataset.json").read_text())
                freeze(data, plan)
                index = root / "index.json"
                index.write_text("fixture")
                args = argparse.Namespace(project=root, plan=plan, index=index, output=root / "run")
                calls, stopped = [], []

                @contextlib.contextmanager
                def fake_services(_args, output):
                    try:
                        yield {}
                    finally:
                        stopped.append(output)

                def fake_run(command, **_kwargs):
                    calls.append(command)
                    if len(calls) == fail_at:
                        raise RuntimeError("failed trial process")
                    out = Path(command[command.index("--output") + 1])
                    out.mkdir()
                    (out / "summary.json").write_text(json.dumps({"status": "complete", "usage": {"attempts": 0}}))
                    (out / "verification.json").write_text(json.dumps({"status": "complete"}))

                with mock.patch.object(study, "project_info", return_value=data["project"]), \
                        mock.patch.object(study, "preflight"), \
                        mock.patch.object(study, "services", side_effect=fake_services), \
                        mock.patch.object(study, "resource_snapshot", return_value={"memoryMax": 16000000000, "swapMax": "0"}), \
                        mock.patch.object(study.subprocess, "check_output", return_value="test-commit"), \
                        mock.patch.object(study.subprocess, "run", side_effect=fake_run), \
                        mock.patch.dict(study.os.environ, {"TYPESAFE_API_KEY": "test-only"}), \
                        contextlib.redirect_stdout(io.StringIO()):
                    if fail_at:
                        with self.assertRaisesRegex(RuntimeError, "failed trial process"):
                            study.run(args)
                    else:
                        study.run(args)
                audit = json.loads((args.output / "deployment.json").read_text())
                self.assertEqual(len(calls), 3 if fail_at else 16)
                self.assertEqual(len(stopped), len(calls))
                self.assertEqual(audit["status"], "incomplete" if fail_at else "complete")
                order = [(i, arm) for i, batch in enumerate(ORDERS) for arm in batch]
                self.assertEqual([(r["batch"], r["arm"]) for r in audit["completedArms"]],
                                 order[:2] if fail_at else order)

    def test_schedule_balances_positions_and_predecessors(self):
        arms = set(ORDERS[0])
        self.assertEqual(arms, {"strict", "cpu", "neural", "full"})
        for position in range(4):
            self.assertEqual({order[position] for order in ORDERS}, arms)
        pairs = collections.Counter((a, b) for order in ORDERS for a, b in zip(order, order[1:]))
        self.assertEqual(pairs, collections.Counter({(a, b): 1 for a in arms for b in arms if a != b}))

    def test_plan_retains_all_goals_and_rejects_tampering(self):
        data = json.loads((REFERENCE / "dataset.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory)
            freeze(data, plan)
            checked, schedule = check_plan(plan)
            self.assertEqual(checked["sites"], data["sites"])
            self.assertEqual(sum(b["sites"] for b in schedule["batches"]), 1024)
            for mutate in (
                    lambda d: d["batches"][0]["order"].reverse(),
                    lambda d: d["batches"][0].update(maxRequestsPerJevArm=99999)):
                changed = copy.deepcopy(schedule)
                mutate(changed)
                (plan / "schedule.json").write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, "schedule or budget"):
                    check_plan(plan)
            (plan / "schedule.json").write_text(json.dumps(schedule))
            changed = copy.deepcopy(data)
            changed["sites"][0]["goal"] += " changed"
            (plan / "dataset.json").write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "original goals"):
                check_plan(plan)


if __name__ == "__main__":
    unittest.main()
