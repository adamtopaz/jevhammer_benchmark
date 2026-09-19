import copy
import sys
import tempfile
from pathlib import Path
import unittest
from jevhammer_benchmark.cli import inject, select_sites, validate_visits, split, read_json, write_json, package_directory, process, load_exclusions
from types import SimpleNamespace


class Driver(unittest.TestCase):
    def test_zero_exit_panic_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "process.log"
            process([sys.executable, "-c", "print('ordinary output')"], root, log)
            with self.assertRaisesRegex(RuntimeError, "Lean runtime panic"):
                process([sys.executable, "-c", "print('PANIC at example: bad offset')"], root, log)

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

    def test_sampling_exclusions_and_owner_cap(self):
        data = [dict(site=f"{m}.{i}", eligible=True, module=m,
                     declaration=f"{m}.t{i // 5}")
                for m in ["A", "B", "C"] for i in range(20)]
        data.append(dict(site="helper", eligible=True, module="A", declaration="A.t0.helper"))
        options = dict(excluded_declarations={"A.t0"}, excluded_modules={"C"}, max_per_declaration=2)
        result = select_sites(data, 100, 1, **options)
        self.assertEqual(result, select_sites(list(reversed(data)), 100, 1, **options))
        self.assertEqual(len(result), 14)
        self.assertTrue(all(r["module"] != "C" and not r["declaration"].startswith("A.t0") for r in result))
        from collections import Counter
        self.assertTrue(all(n <= 2 for n in Counter(r["declaration"] for r in result).values()))
        with self.assertRaises(ValueError):
            select_sites(data, 0, 1)
        with self.assertRaises(ValueError):
            select_sites(data, 10, 1, max_per_declaration=-1)

    def test_exclusion_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "exclude.json"
            write_json(path, {"schema": 1, "declarations": ["M.t"], "modules": ["M.N"]})
            declarations, modules, records = load_exclusions([path])
            self.assertEqual(declarations, {"M.t"})
            self.assertEqual(modules, {"M.N"})
            self.assertEqual(records[0]["name"], "exclude.json")
            self.assertEqual(len(records[0]["sha256"]), 64)
            write_json(path, {"schema": 1, "declarations": "M.t"})
            with self.assertRaises(ValueError):
                load_exclusions([path])

    def test_module_stratified_split(self):
        sites = [dict(site=f"{m}.{i}.{j}", declaration=f"{m}.t{i}", module=m)
                 for m in ["A", "B"] for i in range(4) for j in range(2)]
        sites.append(dict(site="single", declaration="C.t", module="C"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "dataset.json", {"schema": 1, "status": "complete", "sites": sites})
            split(SimpleNamespace(dataset=root / "dataset.json", output=root / "split", seed=7,
                                  test_fraction=.5, stratify_by_module=True))
            dev, test = [read_json(root / "split" / f"{n}.json") for n in ["development", "test"]]
            self.assertEqual({r["module"] for r in test["sites"]}, {"A", "B"})
            self.assertEqual(len(test["sites"]), 8)
            self.assertEqual(len(dev["sites"]), 9)
            self.assertFalse({r["declaration"] for r in dev["sites"]} & {r["declaration"] for r in test["sites"]})
            self.assertEqual(test["partition"]["singleOwnerModulesInDevelopment"], ["C"])

if __name__ == "__main__":
    unittest.main()
