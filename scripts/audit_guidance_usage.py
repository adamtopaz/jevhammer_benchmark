"""Count model use in published whole-tactic results; this is not an ablation."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIES = ("full-leanhammer-confirmation-v1", "available-premises-v1")


def audit(root=ROOT):
    result = {"schema": 1, "interpretation": "Request use is descriptive, not causal attribution.",
              "studies": {}}
    for study in STUDIES:
        report = json.loads((root / "docs" / (study + ".json")).read_text())
        path = root / "docs" / report["publicTrials"]["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == report["publicTrials"]["sha256"]
        methods = defaultdict(list)
        for line in path.read_text().splitlines():
            row = json.loads(line)
            methods[row["method"].rsplit(".", 1)[1]].append(row)
        counts = {}
        for method, rows in sorted(methods.items()):
            assert len(rows) == len({r["site"] for r in rows}) == 1024
            solved = [r for r in rows if r["onTimeVerified"]]
            assert all(r["independentlyReplayed"] for r in solved)
            assert len(solved) == report["metrics"][method]["onTimeVerified"]
            assert all(r["stats"]["rankCalls"] == r["stats"]["stateRankCalls"] and
                       r["stats"]["premiseRankCalls"] == 0 for r in rows)
            called = [r for r in solved if r["stats"]["stateRankCalls"] > 0]
            counts[method] = {
                "sites": len(rows), "onTimeVerified": len(solved),
                "solvesWithoutStateRanking": len(solved) - len(called),
                "solvesAfterStateRankingAttempt": len(called),
                "solvesWithAllRankingAttemptsFailed": sum(
                    r["stats"]["rankFailures"] == r["stats"]["rankCalls"] for r in called),
                "trialsWithStateRankingAttempt": sum(r["stats"]["stateRankCalls"] > 0 for r in rows)}
        result["studies"][study] = {"trialSha256": digest, "methods": counts}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path, help="verify a published audit instead of writing one")
    args = parser.parse_args()
    result = audit()
    if args.check:
        assert result == json.loads(args.check.read_text()), "published usage audit changed"
        print("Published guidance-usage audit verified.")
    else:
        print(json.dumps(result, indent=2))
