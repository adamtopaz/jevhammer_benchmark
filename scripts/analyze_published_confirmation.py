"""Recompute published coverage and paired statistics without Lean or API calls.

This checks recorded replay flags; it does not independently replay certificates.
For fresh proof verification, rerun the experiment using the reproduction guide.
"""
import json
from pathlib import Path

from confirmation_services import ROOT, read, sha
from confirmation_statistics import holm, paired


def analyze(root=ROOT):
    report = read(root / "docs/full-leanhammer-confirmation-v1.json")
    dataset = root / "datasets/full-leanhammer-confirmation-v1/dataset.json"
    trials = root / "docs" / report["publicTrials"]["path"]
    if sha(trials) != report["publicTrials"]["sha256"] or sha(dataset) != report["datasetSha256"]:
        raise ValueError("published trial or dataset checksum changed")
    sites, records = read(dataset)["sites"], [json.loads(s) for s in trials.read_text().splitlines()]
    expected = {s["site"] for s in sites}
    if len(records) != 3072 or len({(r["method"], r["site"]) for r in records}) != 3072:
        raise ValueError("missing or duplicate trial records")
    success = {}
    for arm in ["cpu", "neural", "full"]:
        rows = [r for r in records if r["method"] == "LeanHammerComparison." + arm]
        if len(rows) != 1024 or {r["site"] for r in rows} != expected:
            raise ValueError("method does not cover the frozen cohort")
        if any(r["onTimeVerified"] and not (r["rawSolved"] and r["independentlyReplayed"] and r["elapsedMs"] <= 6000) for r in rows):
            raise ValueError("invalid on-time verified flag")
        success[arm] = {r["site"] for r in rows if r["onTimeVerified"]}
        if len(success[arm]) != report["metrics"][arm]["onTimeVerified"]:
            raise ValueError("coverage differs from the report")
    pairs = [{"a": a, "b": b, "role": role, **paired(sites, success[a], success[b])}
             for a, b, role in [("cpu", "full", "primary"), ("neural", "full", "secondary"),
                                ("cpu", "neural", "secondary")]]
    for row, p in zip(pairs[1:], holm([r["exactMcNemarP"] for r in pairs[1:]])):
        row["secondaryHolmMcNemarP"] = p
    if pairs != report["paired"]:
        raise ValueError("recomputed statistics differ from the report")
    return {"verified": True, "coverage": {a: len(s) for a, s in success.items()}, "paired": pairs}


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2))
