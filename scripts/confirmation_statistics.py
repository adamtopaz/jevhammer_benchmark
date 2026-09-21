"""Paired binary outcomes with prespecified stratified module uncertainty."""
from collections import defaultdict
from math import comb
import random


def exact_mcnemar(gained, lost):
    """Two-sided exact sign/binomial test, conditional on discordant pairs."""
    if min(gained, lost) < 0:
        raise ValueError("counts must be nonnegative")
    n = gained + lost
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(gained, lost) + 1)) / 2**n)


def holm(pvalues):
    result, previous = [0.0] * len(pvalues), 0.0
    for rank, index in enumerate(sorted(range(len(pvalues)), key=pvalues.__getitem__)):
        previous = max(previous, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        result[index] = previous
    return result


def paired(sites, success_a, success_b, *, resamples=20000, seed=20260921):
    expected = {s["site"] for s in sites}
    if len(expected) != len(sites) or not sites or resamples < 40:
        raise ValueError("nonempty unique sites and at least 40 resamples required")
    if not success_a <= expected or not success_b <= expected:
        raise ValueError("unknown outcome site")
    if len({s["declaration"] for s in sites}) != len(sites):
        raise ValueError("confirmation requires one location per declaration")
    gains, losses = success_a - success_b, success_b - success_a
    modules = defaultdict(list)
    for s in sites:
        modules[s["module"]].append((s["site"] in gains) - (s["site"] in losses))
    strata = defaultdict(list)
    for module, values in sorted(modules.items()):
        strata[module.split(".")[1]].append((sum(values), len(values)))
    rng, clustered = random.Random(seed), []
    for _ in range(resamples):
        total, count = 0, 0
        for group in strata.values():
            for delta, n in rng.choices(group, k=len(group)):
                total += delta
                count += n
        clustered.append(total / count)
    rng, independent = random.Random(seed), []
    weights = [len(losses), len(expected) - len(gains) - len(losses), len(gains)]
    for _ in range(resamples):
        independent.append(sum(rng.choices([-1, 0, 1], weights=weights, k=len(expected))) / len(expected))

    def interval(values):
        values.sort()
        return [values[int(.025 * resamples)], values[int(.975 * resamples) - 1]]

    return {"gained": len(gains), "lost": len(losses),
            "bothSolved": len(success_a & success_b),
            "neitherSolved": len(expected - success_a - success_b),
            "difference": (len(gains) - len(losses)) / len(expected),
            "moduleStratifiedBootstrap95": interval(clustered),
            "declarationBootstrap95": interval(independent),
            "exactMcNemarP": exact_mcnemar(len(gains), len(losses)),
            "resamples": resamples, "seed": seed, "modules": len(modules),
            "areas": len(strata)}
