"""Recompute published coverage and paired statistics without Lean or API calls.

This checks recorded replay flags; it does not independently replay certificates.
For fresh proof verification, rerun the experiment using the reproduction guide.
"""
import argparse
import json
from pathlib import Path

from confirmation_services import ROOT, read, sha
from confirmation_statistics import holm, paired


def analyze(root=ROOT, study="full-leanhammer-confirmation-v1"):
    if study not in {"full-leanhammer-confirmation-v1", "available-premises-v1"}:
        raise ValueError("unknown published study")
    report = read(root / "docs" / (study + ".json"))
    dataset = root / "datasets" / study / "dataset.json"
    arms = ["strict", "cpu", "neural", "full"] if study == "available-premises-v1" else ["cpu", "neural", "full"]
    comparisons = [("strict", "cpu", "primary"), ("strict", "neural", "secondary"),
                   ("strict", "full", "secondary")] if study == "available-premises-v1" else [
                       ("cpu", "full", "primary"), ("neural", "full", "secondary"),
                       ("cpu", "neural", "secondary")]
    trials = root / "docs" / report["publicTrials"]["path"]
    if sha(trials) != report["publicTrials"]["sha256"] or sha(dataset) != report["datasetSha256"]:
        raise ValueError("published trial or dataset checksum changed")
    sites, records = read(dataset)["sites"], [json.loads(s) for s in trials.read_text().splitlines()]
    expected = {s["site"] for s in sites}
    if len(expected) != 1024 or len(records) != 1024 * len(arms) or len({(r["method"], r["site"]) for r in records}) != 1024 * len(arms):
        raise ValueError("missing or duplicate trial records")
    success = {}
    for arm in arms:
        rows = [r for r in records if r["method"] == "LeanHammerComparison." + arm]
        if len(rows) != 1024 or {r["site"] for r in rows} != expected:
            raise ValueError("method does not cover the frozen cohort")
        if any(r["onTimeVerified"] and not (r["rawSolved"] and r["independentlyReplayed"] and r["elapsedMs"] <= 6000) for r in rows):
            raise ValueError("invalid on-time verified flag")
        success[arm] = {r["site"] for r in rows if r["onTimeVerified"]}
        if len(success[arm]) != report["metrics"][arm]["onTimeVerified"]:
            raise ValueError("coverage differs from the report")
    pairs = [{"a": a, "b": b, "role": role, **paired(sites, success[a], success[b])}
             for a, b, role in comparisons]
    for row, p in zip(pairs[1:], holm([r["exactMcNemarP"] for r in pairs[1:]])):
        row["secondaryHolmMcNemarP"] = p
    if pairs != report["paired"]:
        raise ValueError("recomputed statistics differ from the report")
    return {"verified": True, "coverage": {a: len(s) for a, s in success.items()}, "paired": pairs}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", default="full-leanhammer-confirmation-v1",
                        choices=["full-leanhammer-confirmation-v1", "available-premises-v1"])
    print(json.dumps(analyze(study=parser.parse_args().study), indent=2))
