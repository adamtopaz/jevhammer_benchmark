module

public meta import JevHammerBenchmark.Method
public meta import Lean.LibrarySuggestions.Default
public meta import JevSelector.SineQuaNon
public meta import Aesop
public meta import Mathlib.Tactic.Contrapose
public meta import Mathlib.Tactic.Ext
public meta import Mathlib.Tactic.Ring
public meta import Mathlib.Tactic.Linarith
public meta import Mathlib.Tactic.NormNum

public meta section
namespace JevHammerBenchmark.Methods
open Lean Meta LibrarySuggestions JevHammer

def sineConfig : JevSelector.SineQuaNon.Config := {}

def sineSelector : Selector := JevSelector.SineQuaNon.selector sineConfig

def mathlibTactics : TacticSet := {
  defaultTactics with
  close := defaultTactics.close.append (.fixed #["ring", "linarith", "norm_num"])
  steps := .interleave #[defaultTactics.steps, .fixed #["ring_nf at *"]] }

def sine : Method := {
  selector := sineSelector
  selectorName := "Sine Qua Non + current file"
  warmup := JevSelector.SineQuaNon.warmup
  validate := fun _ => pure <| Json.mkObj [
    ("algorithm", toJson "Lean.LibrarySuggestions.sineQuaNonSelector"),
    ("wrapper", toJson "JevSelector.SineQuaNon.selector"),
    ("config", toJson sineConfig), ("leanVersion", toJson Lean.versionString),
    ("statistics", toJson "compiled imported theorem statements"),
    ("proofInformation", toJson "none"), ("externalTrainingArtifact", Json.null)] }

def sineReranked : Method := {
  sine with
  config := { guidePremises := true } }

def expanded : Method := {
  sine with
  tactics := mathlibTactics
  tacticSetName := "JevHammerBenchmark.Methods.mathlibTactics" }

def expandedReranked : Method := {
  expanded with
  config := { guidePremises := true } }

def localOnly : Method := {
  selector := currentFile
  selectorName := "current file" }

end JevHammerBenchmark.Methods
