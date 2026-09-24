import argparse
from collections import Counter
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
import guidance_ablation as study
from analyze_guidance_ablation import difference


class GuidanceAblationTests(unittest.TestCase):
    def test_bootstrap_preserves_cluster_and_fractional_outcomes(self):
        sites = [{"site": str(i), "module": f"Mathlib.Algebra.M{i // 4}"} for i in range(8)]
        balanced = {str(i): 1 / 3 if i % 2 else -1 / 3 for i in range(8)}
        result = difference(sites, balanced, resamples=200)
        self.assertEqual(result["moduleStratifiedBootstrap95"], [0, 0])
        self.assertEqual(result, difference(sites, dict(reversed(list(balanced.items()))), resamples=200))
        clustered = {str(i): 1 / 3 if i < 4 else -1 / 3 for i in range(8)}
        result = difference(sites, clustered, resamples=200)
        self.assertEqual(result["moduleStratifiedBootstrap95"], [-1 / 3, 1 / 3])
        self.assertLessEqual(result["moduleStratifiedBootstrap97_5"][0], result["moduleStratifiedBootstrap95"][0])
        with self.assertRaises(ValueError):
            difference(sites, {"unknown": 0}, resamples=200)

    def test_selection_and_counterbalance(self):
        data = study.selection()
        self.assertEqual(len(data["sites"]), 256)
        self.assertEqual(len({s["declaration"] for s in data["sites"]}), 256)
        self.assertEqual(len(data["sources"]), 33)
        self.assertEqual(len({m.split(".")[1] for m in data["sources"]}), 17)
        for position in range(5):
            self.assertEqual(Counter(o[position] for o in study.ORDERS), Counter({a: 2 for a in study.ARMS}))
        self.assertEqual(Counter((a, b) for o in study.ORDERS for a, b in zip(o, o[1:])),
                         Counter({(a, b): 2 for a in study.ARMS for b in study.ARMS if a != b}))
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp)
            study.freeze(data, plan)
            _, schedule = study.check_plan(plan)
            self.assertEqual(sum(b["sites"] for b in schedule["batches"]), 256)
            changed = copy.deepcopy(schedule)
            changed["batches"][0]["order"].reverse()
            study.write_json(plan / "schedule.json", changed)
            with self.assertRaisesRegex(ValueError, "schedule"):
                study.check_plan(plan)
            study.write_json(plan / "schedule.json", schedule)
            changed = copy.deepcopy(data)
            changed["sites"][0]["goal"] += " tampered"
            study.write_json(plan / "dataset.json", changed)
            with self.assertRaisesRegex(ValueError, "selected goals"):
                study.check_plan(plan)

    def test_driver_completes_or_retains_failure_and_strips_baseline_credentials(self):
        for fail_at in (None, 3):
            with self.subTest(fail_at=fail_at), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                plan = root / "plan"
                plan.mkdir()
                data = study.selection()
                study.freeze(data, plan)
                args = argparse.Namespace(project=root, plan=plan, output=root / "run")
                calls = []

                def fake_run(command, **kwargs):
                    calls.append(command)
                    policy = command[command.index("--ranking-policy") + 1]
                    self.assertEqual("TYPESAFE_API_KEY" in kwargs["env"], policy == "jev")
                    self.assertNotIn("JEVSELECTOR_PUBLIC_INDEX", kwargs["env"])
                    self.assertNotIn("JEVBENCH_NEURAL_URL", kwargs["env"])
                    if len(calls) == fail_at:
                        raise RuntimeError("failed trial")
                    out = Path(command[command.index("--output") + 1])
                    out.mkdir()
                    study.write_json(out / "summary.json", {"status": "complete", "usage": {"attempts": 0},
                        "methods": {study.METHOD: {"onTimeVerified": 0}}})
                    study.write_json(out / "verification.json", {"status": "complete"})

                with mock.patch.object(study, "project_info", return_value=data["project"]), \
                        mock.patch.object(study, "resource_snapshot", return_value={}), \
                        mock.patch.object(study.subprocess, "check_output", return_value="test"), \
                        mock.patch.object(study.subprocess, "run", side_effect=fake_run), \
                        mock.patch.dict(study.os.environ, {"TYPESAFE_API_KEY": "test-only", "JEVBENCH_NEURAL_URL": "unused",
                                                          "JEVSELECTOR_PUBLIC_INDEX": "unused"}), \
                        contextlib.redirect_stdout(io.StringIO()):
                    if fail_at:
                        with self.assertRaisesRegex(RuntimeError, "failed trial"):
                            study.run(args)
                    else:
                        study.run(args)
                audit = study.read(args.output / "deployment.json")
                self.assertEqual(len(calls), 3 if fail_at else 50)
                self.assertEqual(audit["status"], "incomplete" if fail_at else "complete")
                expected = [(i, a) for i, order in enumerate(study.ORDERS) for a in order]
                self.assertEqual([(r["batch"], r["arm"]) for r in audit["completedArms"]],
                                 expected[:2] if fail_at else expected)


if __name__ == "__main__":
    unittest.main()
