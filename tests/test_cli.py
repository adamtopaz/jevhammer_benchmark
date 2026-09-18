import copy
import tempfile
from pathlib import Path
import unittest
from jevhammer_benchmark.cli import inject, select_sites, validate_visits, split, read_json, write_json, package_directory
from types import SimpleNamespace


class Driver(unittest.TestCase):
    def test_import_injection(self):
        for text, marker in [("/- a /- b -/ -/\nmodule\npublic import Foo\n", "module\npublic meta import Bar\n"),
                             ("-- comment\nimport Foo\n", "import Bar\nimport Foo")]:
            result, offset = inject(text, ["Bar"])
            self.assertIn(marker, result)
            self.assertEqual(offset, len(result.encode()) - len(text.encode()))
        with self.assertRaises(ValueError):
            inject("/- unfinished", ["Bar"])

    def test_missing_duplicate_changed_locations(self):
        row = dict(site="s", module="M", declaration="M.x", goal="goal", byteStart=1, byteEnd=2, goalCount=2)
        dataset = {"sites": [row]}
        validate_visits(dataset, [row])
        for visits in [[], [row, row], [dict(row, goal="different")]]:
            with self.assertRaises(ValueError):
                validate_visits(dataset, visits)

    def test_grouped_split(self):
        dataset = {"schema": 1, "status": "complete", "sites": [
            {"site": str(i), "declaration": f"M.t{i // 2}"} for i in range(12)]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "dataset.json", dataset)
            split(SimpleNamespace(dataset=root / "dataset.json", output=root / "split", seed=1, test_fraction=.3))
            a, b = [read_json(root / "split" / f"{n}.json")["sites"] for n in ["development", "test"]]
            self.assertFalse({r["declaration"] for r in a} & {r["declaration"] for r in b})
            self.assertEqual(len(a) + len(b), 12)

    def test_quoted_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            expected = root / ".lake/packages/premise-selection"
            expected.mkdir(parents=True)
            self.assertEqual(package_directory(root, {}, {"type": "git", "name": "«premise-selection»"}), expected)
            with self.assertRaises(ValueError):
                package_directory(root, {}, {"type": "git", "name": "missing"})

    def test_sampling_deterministic(self):
        data = [dict(site=str(i), eligible=i != 0, module=f"M{i % 3}") for i in range(30)]
        self.assertEqual(select_sites(data, 10, 1), select_sites(list(reversed(data)), 10, 1))
        self.assertEqual(len(select_sites(data, 10, 1)), 10)

if __name__ == "__main__":
    unittest.main()
