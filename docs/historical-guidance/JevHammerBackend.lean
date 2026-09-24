module

public meta import JevHammer
public meta import Bench.OptionalFinisher
public meta import Bench.Competitor

public meta section
namespace JevHammerBackend
open Lean Meta JevPilot

/-- Named configurations isolate model ordering and candidate recall while
keeping the proof engines identical. Only the harness supplies live rankers. -/
def run : Bench.OptionalFinisher.Runner := fun goal mode limits ranker output => do
  if #["neural_search", "neural_search_jev"].contains mode then
    let stats ← IO.mkRef ({} : Advanced.Stats)
    try
      Advanced.solve [goal] { Advanced.experimentConfig "adaptive" with
        maxMillis := limits.maxMillis, maxNodes := limits.maxNodes,
        maxDepth := limits.maxDepth, maxCalls := limits.maxCalls,
        maxCandidates := limits.maxCandidates, maxPremises := 100 }
        ranker stats (some fun goal count => HammerFinish.retrieve goal {
          neuralPremises := count, maxPremises := count })
    finally
      output.set <| (toJson (← stats.get)).mergeObj (toJson (← Bench.Competitor.stats.get))
    return
  unless #["hammer_prefix", "hammer_rank_jev", "hammer_union", "hammer_union_jev",
      "hammer_interleave", "hammer_interleave_jev"].contains mode do
    throwError "unknown Jev Hammer experiment {mode}"
  let stats ← IO.mkRef ({} : HammerFinish.Stats)
  let config : HammerFinish.Config := {
    maxMillis := limits.maxMillis, backendHeartbeats := limits.maxHeartbeats,
    maxCalls := min 1 limits.maxCalls,
    addIndexedPremises := mode.startsWith "hammer_union" || mode.startsWith "hammer_interleave",
    interleaveIndexed := mode.startsWith "hammer_interleave" }
  try
    HammerFinish.solve [goal] config ranker stats
  finally
    output.set <| (toJson (← stats.get)).mergeObj (toJson (← Bench.Competitor.stats.get))

end JevHammerBackend
