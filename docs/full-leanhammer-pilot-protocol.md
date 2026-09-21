# Current JevHammer configurations versus full LeanHammer

Requested on 2026-09-21. The existing 134-location comparison substituted
selectors inside JevHammer: CPU sparse/conclusion 63, neural 63, neural/conclusion
64. It does not compare full tactics. This new pilot compares the two strongest
current package configurations with full upstream LeanHammer.

Freeze the optional integration, dataset admission and this protocol before
Mathlib proof trials. Use the same previously exposed 34 locations, unchanged
source-goal hashes, and the CPU artifact excluding all 188 broad-cohort owners.
Do not use any of the 122 reserved evaluation locations. No manual failed-goal
analysis, per-theorem changes or selective API retries.

| Arm | Configuration |
|---|---|
| CPU | JevHammer + target-weighted public sparse/conclusion fusion; Jev state guidance |
| Neural | JevHammer + neural/conclusion fusion; Jev state guidance |
| Full LeanHammer | Upstream neural selector with its ordinary Sine fallback; all proof engines |

Both JevHammer arms preserve native premise order and use the same Mathlib tactic
collection, six-second soft clock, depth 3, 12 nodes, beam 4, 24 successor
candidates, 100 retrieved premises, 8/16 finishing prefixes, one allowed premise
refresh, three Jev calls and 15,000 heartbeats per individual tactic attempt.
Premise guidance and deferred guidance remain disabled. Jev uses `jev-1.13.0`.

Full LeanHammer uses default parallelism, Aesop, grind, Lean-auto/Zipperposition/
Duper and Lean-SMT/cvc5, with upstream premise counts and timeouts. No engine is
disabled and no additional Jev search is added. Its complete invocation receives
200,000 heartbeats, the common outer allowance; treating an entire hammer call
as a 15,000-heartbeat small tactic would handicap it. Its default five-second
solver timeout excludes premise retrieval. Primary coverage is therefore
**independently verified proofs finished within six seconds end to end**, including
retrieval, reconstruction and certificate generation. Retain/replay late proofs
and report their count separately.

All methods use Lean 4.33.0, Mathlib
`db584cd6d46c92f209a44c0f1c829460d327499d`, eight Lean workers, and synchronous
elaboration. Eight workers permit full LeanHammer's parallel engines to run;
this differs from the earlier two-worker selector pilots, so fresh controls are
required. Run one method per source process to avoid retaining CPU-selector
caches in the full-LeanHammer process. Collect CPU, neural and full arms in that
fixed order. Start fresh CPU neural service processes for the full-LeanHammer
arm, separate from those used by the neural/JevHammer arm. Model/corpus disk
caches persist. Imported and earlier current-file statement embeddings are
warmed outside goal timing; goal queries are timed. Initialization is reported.

Pins:

- Base benchmark runner: `bb2b1861f665c3854d49b3f115d6a413aab2611f`.
- JevHammer: `bf848e36e2f70f5ca745e0f88f6953279e7d00a6`.
- JevSelector: `397bef6d03d6ef4c7cda8ada8f3f92fb567863e1`.
- Full LeanHammer: `21886b7ffbdf32017655a9d6e699f98779046533`, also upstream HEAD
  when checked before setup.
- Public index SHA-256:
  `e388078b747f85320c672a78570d3831bb4ce6b754d3df493ed7095afe4cd7f5`.
- Neural client/model/corpus/server: unchanged pinned deployment recorded by the
  neural integration; CPU float32, two embedding threads, training overlap unknown.

The host's pre-existing cvc5/GMP link adjustment and Zipperposition loader
adaptation remain in use. Record their patches and native binary hashes. The
exact missing Python runtime was restored from the Nix binary cache; model,
dependency lock and runtime versions were unchanged. Each external engine must
pass an isolated smoke test; all three methods must pass source-context fixture
tests with independent replay before real trials.

The complete job, including services, solver processes and Lean workers, shares
one **16,000,000,000-byte, zero-swap** scope. Run no other heavy task concurrently.
Collect **102 trials**. Each JevHammer arm has at most **102 Jev requests** and
**2,000,000 reported input tokens**. Full LeanHammer makes zero Jev requests.
Record all module failures, proof failures, API errors, selector fallbacks,
unavailable suggestions and memory events. Do not relabel a Sine fallback as
successful neural retrieval.

Report per-arm on-time/raw verified counts, paired gains/losses, declaration-
bootstrap 95% intervals, total goal/retrieval/warmup time, Jev usage and memory.
All successful trials must independently replay in the original source context.
This exposed pilot can guide the next comparison but cannot establish general
superiority. Historical monolithic results are not attributed to the new packages.

Use the standard CLI once per arm, with explicit service/artifact configuration,
inside the shared memory scope:

```sh
python -m jevhammer_benchmark run --project integrations/leanhammer \
  --dataset datasets/sparse-jev-v1/full-leanhammer-pilot-v1.json \
  --methods LeanHammerComparison.cpu --threads 8 --heartbeats 200000 \
  --max-requests 102 --max-input-tokens 2000000 --memory-limit 16000000000 \
  --output runs/full-leanhammer-pilot-v1/cpu
# Repeat for .neural and .full, using distinct outputs and the service policy above.
```

After every arm and its proof replay completes, regenerate the paired report
with `python scripts/compare_full_leanhammer.py runs/full-leanhammer-pilot-v1
docs/full-leanhammer-pilot-v1.json`. The exporter rejects incomplete or mismatched
runs. The deployment launcher records its source, environment identities and
per-arm completion status in the run parent.
