module

public meta import JevHammerBenchmark.Method
public meta import Lean.LibrarySuggestions.Default
public meta import Aesop
public meta import Mathlib.Tactic.Contrapose
public meta import Mathlib.Tactic.Ext
public meta import Mathlib.Tactic.Ring
public meta import Mathlib.Tactic.Linarith
public meta import Mathlib.Tactic.NormNum

public meta section
namespace JevHammerBenchmark.Methods
open Lean Meta LibrarySuggestions JevHammer

def sineSelector : Selector := (sineQuaNonSelector 1.5).intersperse currentFile

def mathlibTactics : TacticSet := {
  defaultTactics with
  close := defaultTactics.close.append (.fixed #["ring", "linarith", "norm_num"])
  steps := .interleave #[defaultTactics.steps, .fixed #["ring_nf at *"]] }

def sine : Method := {
  selector := sineSelector
  selectorName := "Sine Qua Non + current file"
  warmup := do discard <| SineQuaNon.sineQuaNonTheorems ``True }

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
