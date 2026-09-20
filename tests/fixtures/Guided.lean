import JevHammerBenchmark.Method

namespace GuidedFixture
open Lean Meta JevHammerBenchmark

def method : Method := {
  selector := LibrarySuggestions.empty
  selectorName := "offline budgeted selector fixture"
  selectorFactory := some fun rank base goal cfg => do
    discard <| rank "Which supplied direction is useful?" goal #[.str "none", .str "forward"]
    base goal cfg
  -- Force selector retrieval before the elementary finish tactic.
  tactics := { finish := .fixed #["exact True.intro"] }
  config := { maxMillis := 30000, maxCalls := 1 } }

theorem checkGuidance : True := by trivial

end GuidedFixture
