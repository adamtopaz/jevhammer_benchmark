"""Analytic and clustered examples for confirmation inference; no Lean/API calls."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from confirmation_statistics import exact_mcnemar, holm, paired


class ConfirmationStatisticsTests(unittest.TestCase):
    def test_exact_discordant_pairs(self):
        self.assertEqual(exact_mcnemar(0, 0), 1)
        self.assertEqual(exact_mcnemar(4, 4), 1)
        self.assertEqual(exact_mcnemar(6, 2), 0.2890625)
        self.assertEqual(exact_mcnemar(2, 6), 0.2890625)
        self.assertEqual(exact_mcnemar(10, 0), 1 / 512)
        self.assertEqual(exact_mcnemar(0, 1024), 2 ** -1023)

    def test_holm_keeps_original_order(self):
        self.assertEqual(holm([.04, .001]), [.04, .002])
        self.assertEqual(holm([.04, .03]), [.06, .06])
        self.assertEqual(holm([]), [])

    def test_modules_are_not_independent_locations(self):
        sites, a, b = [], set(), set()
        for area in range(4):
            for module in range(2):
                for i in range(16):
                    key = f"{area}-{module}-{i}"
                    sites.append({"site": key, "declaration": key,
                                  "module": f"Mathlib.Area{area}.Module{module}"})
                    (a if module else b).add(key)
        result = paired(sites, a, b, resamples=1000)
        self.assertEqual(result['difference'], 0)
        self.assertEqual(result['gained'], result['lost'])
        clustered = result['moduleStratifiedBootstrap95']
        independent = result['declarationBootstrap95']
        self.assertLess(clustered[0], independent[0])
        self.assertGreater(clustered[1], independent[1])
        self.assertEqual(paired(sites, a, b, resamples=1000), result)

    def test_identical_and_duplicate_outcomes(self):
        sites = [{"site": "one", "declaration": "decl", "module": "Mathlib.Area.Module"}]
        result = paired(sites, {"one"}, {"one"}, resamples=40)
        self.assertEqual(result['moduleStratifiedBootstrap95'], [0, 0])
        self.assertEqual(result['bothSolved'], 1)
        self.assertEqual(paired(sites, {"one"}, set(), resamples=40)['moduleStratifiedBootstrap95'], [1, 1])
        with self.assertRaises(ValueError):
            paired(sites, {"unknown"}, set(), resamples=40)
        with self.assertRaises(ValueError):
            paired(sites + [dict(sites[0], site="two")], set(), set(), resamples=40)


if __name__ == "__main__":
    unittest.main()
