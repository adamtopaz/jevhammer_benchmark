module
public meta import JevHammerBenchmark.GraphStudy
public meta section
namespace JevHammerBenchmark.GraphPreviewStudy
open Lean Meta

/-- The representation-only ablation retains all original traversal bounds. -/
def previewOptions : JevSelector.GraphConfig := {
  GraphStudy.graphOptions with
  maxPreviewCandidates := 3
  maxPreviewTypeChars := 480 }

def previewFactory : JevHammer.SelectorFactory := fun rank base goal cfg => do
  (← GraphStudy.graphIndex).guided previewOptions rank base goal cfg

def cpuControl : Method := GraphStudy.cpuControl
def original : Method := GraphStudy.guided

/-- Separate mutable structural cache; the signature graph is immutable. -/
def preview : Method := {
  original with
  selector := JevSelector.fuse #[Research.publicTarget.selector,
    Research.structuralSelector "graph-preview-cpu"] {}
  selectorFactory := some previewFactory
  selectorName := "Public sparse + conclusion fusion + Jev signature graph; destination previews=3, type chars=480"
  warmup := do
    Research.publicTarget.warmup
    discard <| Research.structuralIndex "graph-preview-cpu"
    discard <| GraphStudy.graphIndex
  validate := fun owners => do
    return (← original.validate owners).mergeObj <| Json.mkObj [
      ("destinationPreviews", Json.mkObj [
        ("candidates", toJson previewOptions.maxPreviewCandidates),
        ("typeChars", toJson previewOptions.maxPreviewTypeChars),
        ("neighborhoodOrdering", toJson "unchanged base-rank then seed-overlap"),
        ("rankingBudget", toJson "shared with Jev proof-state search")])] }

def neuralNative : Method := GraphStudy.neuralNative
def neuralReranked : Method := GraphStudy.neuralReranked

end JevHammerBenchmark.GraphPreviewStudy
