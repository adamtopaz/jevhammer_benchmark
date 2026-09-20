# Exhaustive Bayes posting ablation

Freeze this protocol and the re-admitted dataset before any proof calls. The
completed Bayes pilot selected sparse/Bayes as its strongest learned fusion
(15/34), but it did not beat the CPU control (16/34). Standalone Bayes is included
because it met the provisional CPU query-cost target. The three-source fusion
scored 13/34 and had higher cost; it is not selected for this proof screen.
No individual failed goal informs any change.

This screen changes exactly one retrieval option within each matched Bayes
pair: `maxPostingsPerSymbol` is 20,000 or zero (exhaustive). The unchanged stored
model still retains at most 64 features per label; exhaustive here does not
mean an unpruned training artifact. Keep signature prior 20, observed weight
10, missing log weight −15, unit-weight query constants, and 10,000 retrieval
heartbeats. The statement index, theorem dependencies, and Bayes model are the
same bytes as in the completed pilot, with all 188 cohort owners excluded.

| Method | Premise source | Posting cap |
|---|---|---:|
| `BayesExactStudy.cpuControl` | Public sparse + conclusion patterns | n/a |
| `BayesExactStudy.sampled` | Bayes | 20,000 |
| `BayesExactStudy.exhaustive` | Bayes | 0 |
| `BayesExactStudy.sampledTarget` | Public sparse + Bayes | 20,000 |
| `BayesExactStudy.exhaustiveTarget` | Public sparse + Bayes | 0 |
| `BayesExactStudy.neuralControl` | Warmed neural + conclusion patterns | n/a |

All arms use Jev proof-state guidance with the same Mathlib tactic set, six
seconds, 200,000 outer heartbeats, three shared Jev calls, 100 retrieved names,
eight injected premises, and unchanged premise refresh. CPU arms use native
premise order; the neural control uses the previously selected Jev premise
reranking. Fusion is flat reciprocal-rank fusion (offset 16, pool factor 2,
maximum pool 256). The finite five-million-heartbeat initialization budget is
separate from proof search. Report loading and warmup costs separately.

Prepared immutable arrays may be shared; CPU and neural conclusion caches stay
independent. Start fresh CPU neural services and warm imported and earlier
current-file statement embeddings outside goal timing. Actual goal embeddings
remain timed. Use the same fixed model/corpus/provenance as the prior reference.

Re-admit all 34 original pilot locations, owners, and goal hashes unchanged,
with zero model calls. Collect every arm at every location: **204 trials**,
maximum **612 Jev requests** and **6,000,000 reported input tokens**. Use two
threads and serial modules in one aggregate **16,000,000,000-byte, zero-swap**
scope for services, Lean workers, and independent replay. No other heavy job
runs concurrently. Do not selectively retry failures or adjust search settings.

Replay every claimed proof against the original source context. Report all
on-time and late outcomes, API errors, blocked budgets, premise/state calls,
tokens, query/goal/warmup costs, paired declaration-grouped intervals, code and
artifact identities, and memory events. Select between the two exhaustive
candidates by on-time replayed coverage, then total goal time, then method name.
Promote to a larger development comparison only if the selected candidate beats
the CPU control; paired sampled/exhaustive results separately test the cap's
contribution. A larger comparison must retain both neural guidance modes because
the strongest broader reference used native order. This exposed pilot cannot
establish final superiority; leave all 122 reserved evaluation locations unopened.

## Artifacts, costs, and reproduction

Selector revision: `e793bad2e447f5b5aa96efd92979e074d6dfa142`.
Statement index SHA-256: `e388078b747f85320c672a78570d3831bb4ce6b754d3df493ed7095afe4cd7f5`.
Bayes model SHA-256: `e6c60bf2da82c61296da74a36797cfe799e07d5c5fb07a1a719bba353d8642f4`.
Use the artifact preparation and CPU neural-service setup in the
[original protocol](cpu-selector-bayes-protocol.md). The
[matched CPU profiles](cpu-selector-profile-bayes-postings-v1.json) completed
all 576 retrievals without errors: exhaustive p95 was 131.80 ms standalone,
353.41 ms for sparse/Bayes, and 460.66 ms for triple fusion. Mean top-eight
agreement with sampling was 62.50%, 78.91%, and 80.86%, respectively. Those are
ranking changes on fixed public statement types, not proof-quality gains.

Check the adapters with `lake build JevHammerBenchmark.BayesExactStudy` and
`lake env lean BayesExactStudyTests.lean`. With the artifact paths and CPU neural
endpoint configured, run this command inside the same bounded scope as the
services:

```sh
python -m jevhammer_benchmark run \
  --dataset datasets/sparse-jev-v1/research-bayes-exact-v1.json \
  --methods JevHammerBenchmark.BayesExactStudy.cpuControl \
    JevHammerBenchmark.BayesExactStudy.sampled \
    JevHammerBenchmark.BayesExactStudy.exhaustive \
    JevHammerBenchmark.BayesExactStudy.sampledTarget \
    JevHammerBenchmark.BayesExactStudy.exhaustiveTarget \
    JevHammerBenchmark.BayesExactStudy.neuralControl \
  --config '{}' --max-requests 612 --max-input-tokens 6000000 \
  --memory-limit 16000000000 --threads 2 \
  --output runs/cpu-selector-bayes-exact-v1
```
