module
public meta import JevHammerBenchmark.RerankStudy
public meta import JevSelector.DependencyGraph
public meta section
namespace JevHammerBenchmark.GraphStudy
open Lean Meta LibrarySuggestions

initialize graphCache : IO.Ref (Option JevSelector.DependencyGraph) ← IO.mkRef none

def graphIndex : MetaM JevSelector.DependencyGraph := do
  if let some graph ← graphCache.get then
    unless graph.importedModules == (← getEnv).header.moduleNames do
      throwError "graph study imports changed during a run"
    return graph
  let graph ← JevSelector.DependencyGraph.create
  graphCache.set (some graph)
  return graph

def graphOptions : JevSelector.GraphConfig := {}

def graphFactory : JevHammer.SelectorFactory := fun rank base goal cfg => do
  (← graphIndex).guided graphOptions rank base goal cfg

def cpuControl : Method := RerankStudy.cpuNative

def guided : Method := {
  cpuControl with
  selector := JevSelector.fuse #[Research.publicTarget.selector,
    Research.structuralSelector "graph-guided-cpu"] {}
  selectorFactory := some graphFactory
  selectorName := "Public sparse + conclusion fusion + Jev signature graph: rounds=1, frontier=8, forward=256, edges=32, visited=128, chars=1200, heartbeats=10000"
  warmup := do
    Research.publicTarget.warmup
    discard <| Research.structuralIndex "graph-guided-cpu"
    discard <| graphIndex
  validate := fun owners => do
    return Json.mkObj [("base", ← cpuControl.validate owners),
      ("graph", Json.mkObj [("kind", toJson "available-signature-dependencies"),
        ("proofTraining", toJson "none"), ("rounds", toJson graphOptions.maxRounds),
        ("frontier", toJson graphOptions.maxFrontier),
        ("forwardCandidates", toJson graphOptions.maxForwardCandidates),
        ("edges", toJson graphOptions.maxEdgesPerNode),
        ("visited", toJson graphOptions.maxVisited),
        ("typeChars", toJson graphOptions.maxTypeChars),
        ("heartbeats", toJson graphOptions.heartbeats),
        ("rankOffset", toJson graphOptions.rankOffset),
        ("rankingBudget", toJson "shared with Jev proof-state search")])] }

def neuralNative : Method := RerankStudy.neuralNative

def neuralReranked : Method := RerankStudy.neuralReranked

end JevHammerBenchmark.GraphStudy
