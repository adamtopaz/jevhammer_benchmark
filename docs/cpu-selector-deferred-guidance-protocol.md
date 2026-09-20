# Deferred premise guidance: matched development pilot

The completed preview screen solved 16/34 with CPU control, 14/34 with each
graph variant, 13/34 with neural native and 14/34 with neural reranking. Both
graph arms spent 49 calls on premise guidance and made 24 proof-state calls,
versus CPU's 42 state calls. This motivates trying the base-premise finisher
before spending those calls. It is a scheduling hypothesis; the preview
selector itself was not promoted by the preceding experiment.

Freeze this protocol, adapters and re-admitted dataset before live calls. Use
the same 34 exposed development locations, unchanged source/goal identities,
and CPU preparation excluding all 188 broad-cohort owners. All 122 reserved
evaluation locations remain unused. No individual failed-goal analysis or
goal-specific changes are allowed.

| Method in `JevHammerBenchmark.DeferredGuidanceStudy` | Premise selection |
|---|---|
| `cpuControl` | Sparse + conclusion, native order |
| `cpuReranked` | Same CPU source; Jev reranking after failed base finish |
| `graphPreview` | Same CPU source; preview graph after failed base finish |
| `neuralNative` | Neural + conclusion, native order |
| `neuralReranked` | Same neural source; Jev reranking after failed base finish |

Every arm sets `deferPremiseGuidance := true`. Native methods have no premise
guidance and keep their original execution path. Guided methods first retrieve
from their own base selector and try the unchanged configured premise finisher.
Success skips guidance. Failure restores Lean state, then runs normal guided
selection and proof-state search. The second base query is deliberately timed;
there is no implicit ranking cache. Both stages share the original clock,
statistics, tactics and call limit. Jev proof-state guidance stays enabled.

Use identical Mathlib tactics, six seconds per goal, three shared calls,
200,000 outer heartbeats, 100 retrieved names, eight initial injected names
(the existing finisher also tries sixteen), and unchanged search/refresh
settings. CPU and neural reranked methods set `guidePremises`; only graphPreview
has a selector factory. Graph bounds remain one round, eight frontier nodes,
128 visited names, 256 forward candidates, 32 followed edges, seed types capped
at 1,200 characters, three destination examples capped at 480 characters,
10,000 extra query heartbeats and rank offset 16. Do not change these after
seeing partial results.

JevHammer pin: `bf848e36e2f70f5ca745e0f88f6953279e7d00a6`.
Selector pin: `397bef6d03d6ef4c7cda8ada8f3f92fb567863e1`.
Public index SHA-256:
`e388078b747f85320c672a78570d3831bb4ce6b754d3df493ed7095afe4cd7f5`.
Use Jev `jev-1.13.0` and the unchanged pinned CPU neural model/corpus. Both neural
services start fresh in CPU float32 mode with two threads. Training overlap of
that third-party model remains unknown. These are selectors within JevHammer,
not the full LeanHammer tactic.

Each arm owns its existing independent mutable structural query cache. Fixed
synthetic structural warmup and imported/earlier current-file neural statement
embeddings remain outside goal timing. Actual goal embedding is timed. The
imported signature graph is immutable and shared; live current-file signatures
are rebuilt. Report initialization separately with the existing five-million
heartbeat warmup budget; shared-cache timing attribution remains order-dependent.

Collect all **170 trials**, capped at **510 Jev requests** and **5,000,000
reported input tokens**. Run one heavy job containing all services and Lean
workers in a **16,000,000,000-byte, zero-swap scope**, using two CPU threads.
Retain all failures, late proofs and blocked trials. No selective API retries.
Independently replay every successful proof before reporting verified coverage.

Report paired coverage and declaration-grouped 95% intervals, all goal and
retrieval times, initialization, requests, failures, tokens, memory, and the new
`unguidedPremiseAttempts` / `unguidedPremiseFinishes` counters. Model calls avoided
by early finishes are a mechanism check, not by themselves a proof-quality gain.
Compare candidates against both fresh neural controls with the same schedule.
Historical old-schedule runs do not isolate a causal scheduling effect.

Advance a CPU candidate to 134 development locations only if it beats CPU
control and both neural arms on on-time independently replayed pilot coverage.
If both qualify, prefer higher coverage, then lower total goal time. The pilot
cannot establish final superiority; substantial held-out gain and a fresh Jev
repeat remain required. Do not touch reserved evaluation in this screen.

With both CPU neural services configured in the same bounded scope:

```sh
python -m jevhammer_benchmark run \
  --dataset datasets/sparse-jev-v1/research-deferred-guidance-v1.json \
  --methods JevHammerBenchmark.DeferredGuidanceStudy.cpuControl \
    JevHammerBenchmark.DeferredGuidanceStudy.cpuReranked \
    JevHammerBenchmark.DeferredGuidanceStudy.graphPreview \
    JevHammerBenchmark.DeferredGuidanceStudy.neuralNative \
    JevHammerBenchmark.DeferredGuidanceStudy.neuralReranked \
  --config '{}' --max-requests 510 --max-input-tokens 5000000 \
  --memory-limit 16000000000 --threads 2 \
  --output runs/cpu-selector-deferred-guidance-v1
```
