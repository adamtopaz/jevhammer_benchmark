module
public meta import JevHammerBenchmark.BayesStudy
public meta section
namespace JevHammerBenchmark.BayesExactStudy
open Lean Meta LibrarySuggestions

/-- Same fixed controls and search budgets as the completed Bayes screen. -/
def cpuControl : Method := BayesStudy.cpuControl
def neuralControl : Method := BayesStudy.neuralControl

def sampled : Method := BayesStudy.bayes

def exhaustiveOptions : JevSelector.BayesQueryConfig := { maxPostingsPerSymbol := 0 }

def exhaustiveSelector : Selector := fun goal cfg => do
  (← BayesStudy.bayesIndex).selector exhaustiveOptions goal cfg

/-- Only query-time posting sampling changes. The stored top-64 model is fixed. -/
def exhaustive : Method := {
  sampled with
  selector := exhaustiveSelector
  selectorName := "Sparse Bayes: exhaustive stored postings, fixed top64 features" }

def sampledTarget : Method := BayesStudy.bayesTarget

def exhaustiveTarget : Method := {
  sampledTarget with
  selector := JevSelector.fuse #[Research.publicTarget.selector, exhaustiveSelector] {}
  selectorName := "Public sparse + Bayes with exhaustive stored postings, native premise order" }

end JevHammerBenchmark.BayesExactStudy
