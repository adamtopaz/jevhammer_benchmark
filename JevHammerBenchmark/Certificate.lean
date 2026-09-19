module

public meta import Lean

public meta section
namespace JevHammerBenchmark.Certificate
open Lean Meta Elab Command

private def nameJson : Name → Json
  | .anonymous => .arr #[]
  | .str p s => .arr #[nameJson p, .str s]
  | .num p n => .arr #[nameJson p, toJson n]

private partial def readName (j : Json) : Except String Name := do
  let xs ← j.getArr?
  if xs.isEmpty then return .anonymous
  unless xs.size == 2 do throw "invalid name"
  let p ← readName xs[0]!
  match xs[1]! with
  | .str s => do pure <| .str p s
  | n => do pure <| .num p (← fromJson? n)

private def levelJson : Level → Json
  | .zero => .arr #[.str "zero"]
  | .succ u => .arr #[.str "succ", levelJson u]
  | .max u v => .arr #[.str "max", levelJson u, levelJson v]
  | .imax u v => .arr #[.str "imax", levelJson u, levelJson v]
  | .param n => .arr #[.str "param", nameJson n]
  | .mvar _ => .arr #[.str "invalid_mvar"]

private partial def readLevel (j : Json) : Except String Level := do
  let xs ← j.getArr?
  match ← xs[0]!.getStr? with
  | "zero" => do pure <| .zero
  | "succ" => do pure <| .succ (← readLevel xs[1]!)
  | "max" => do pure <| .max (← readLevel xs[1]!) (← readLevel xs[2]!)
  | "imax" => do pure <| .imax (← readLevel xs[1]!) (← readLevel xs[2]!)
  | "param" => do pure <| .param (← readName xs[1]!)
  | _ => throw "invalid certificate level"

private def binderNat : BinderInfo → Nat
  | .default => 0 | .implicit => 1 | .strictImplicit => 2 | .instImplicit => 3

private def readBinder (j : Json) : Except String BinderInfo := do
  match ← j.getNat? with
  | 0 => do pure <| .default | 1 => do pure <| .implicit
  | 2 => do pure <| .strictImplicit | 3 => do pure <| .instImplicit
  | _ => throw "invalid binder"

private structure EncodeState where
  nodes : Array Json := #[]
  memo : Std.HashMap Expr Nat := {}

private partial def encodeExpr (e : Expr) : StateM EncodeState Nat := do
  if let some i := (← get).memo[e]? then return i
  if let .mdata _ body := e then
    let i ← encodeExpr body
    modify fun s => { s with memo := s.memo.insert e i }
    return i
  let node : Json ← match e with
    | .bvar n => pure <| .arr #[.str "bvar", toJson n]
    | .sort u => pure <| .arr #[.str "sort", levelJson u]
    | .const n us => pure <| .arr #[.str "const", nameJson n, toJson (us.map levelJson)]
    | .app f a => do pure <| .arr #[.str "app", toJson (← encodeExpr f), toJson (← encodeExpr a)]
    | .lam n t b bi => do pure <| .arr #[.str "lam", nameJson n, toJson (← encodeExpr t),
        toJson (← encodeExpr b), toJson (binderNat bi)]
    | .forallE n t b bi => do pure <| .arr #[.str "forall", nameJson n, toJson (← encodeExpr t),
        toJson (← encodeExpr b), toJson (binderNat bi)]
    | .letE n t v b nd => do pure <| .arr #[.str "let", nameJson n, toJson (← encodeExpr t),
        toJson (← encodeExpr v), toJson (← encodeExpr b), toJson nd]
    | .lit (.natVal n) => pure <| .arr #[.str "nat", toJson n]
    | .lit (.strVal s) => pure <| .arr #[.str "str", toJson s]
    | .proj n i e => do pure <| .arr #[.str "proj", nameJson n, toJson i, toJson (← encodeExpr e)]
    | _ => pure <| .arr #[.str "invalid_open_expression"]
  let i := (← get).nodes.size
  modify fun s => { nodes := s.nodes.push node, memo := s.memo.insert e i }
  return i

/-- Lossless logical expression DAG. Metadata used only for pretty-printing is
removed. Names, universe levels, binder modes, and every term argument are exact. -/
def encode (proof type : Expr) : Json := Id.run do
  let ((p, t), s) := (do
    let p ← encodeExpr proof
    let t ← encodeExpr type
    pure (p, t)).run {}
  return Json.mkObj [("version", toJson (1 : Nat)), ("nodes", .arr s.nodes),
    ("proof", toJson p), ("type", toJson t)]

private def ref (nodes : Array Expr) (j : Json) : Except String Expr := do
  let i ← j.getNat?
  let some e := nodes[i]? | throw "invalid or forward DAG reference"
  return e

def decode (j : Json) : Except String (Expr × Expr) := do
  unless j.getObjValD "version" == toJson (1 : Nat) do throw "unknown certificate version"
  let mut nodes : Array Expr := #[]
  for node in ← (j.getObjValD "nodes").getArr? do
    let a ← node.getArr?
    let e : Expr ← match ← a[0]!.getStr? with
      | "bvar" => do pure <| .bvar (← a[1]!.getNat?)
      | "sort" => do pure <| .sort (← readLevel a[1]!)
      | "const" => do pure <| .const (← readName a[1]!) (← (← a[2]!.getArr?).toList.mapM readLevel)
      | "app" => do pure <| .app (← ref nodes a[1]!) (← ref nodes a[2]!)
      | "lam" => do pure <| .lam (← readName a[1]!) (← ref nodes a[2]!) (← ref nodes a[3]!) (← readBinder a[4]!)
      | "forall" => do pure <| .forallE (← readName a[1]!) (← ref nodes a[2]!) (← ref nodes a[3]!) (← readBinder a[4]!)
      | "let" => do pure <| .letE (← readName a[1]!) (← ref nodes a[2]!) (← ref nodes a[3]!) (← ref nodes a[4]!) (← fromJson? a[5]!)
      | "nat" => do pure <| .lit (.natVal (← a[1]!.getNat?))
      | "str" => do pure <| .lit (.strVal (← a[1]!.getStr?))
      | "proj" => do pure <| .proj (← readName a[1]!) (← a[2]!.getNat?) (← ref nodes a[3]!)
      | _ => throw "invalid or open certificate expression"
    nodes := nodes.push e
  return (← ref nodes (j.getObjValD "proof"), ← ref nodes (j.getObjValD "type"))

private def checkClosed (proof type : Expr) (excluded : String) : MetaM Unit := do
  for e in [proof, type] do
    if e.hasMVar || e.hasFVar || e.hasSorry then throwError "open or admitted certificate"
    if e.getUsedConstants.any (·.toString == excluded) then throwError "self-retrieval in certificate"

/-- Verify an exact expression certificate and optionally bind its target to
the actual source goal's closed type. No pretty-printing or proof search. -/
private def checkedProof (j : Json) (expected : Expr) (excluded : String) : MetaM Expr := do
  let (proof, type) ← ofExcept (decode j)
  checkClosed proof type excluded
  for e in [proof, type] do
    match Kernel.check (← getEnv) {} e with
    | .ok _ => pure ()
    | .error e => throwError "certificate kernel failure: {e.toMessageData (← getOptions)}"
  unless ← isDefEq (← inferType proof) type do throwError "certificate has the wrong type"
  let params := (collectLevelParams {} type).params
  let levels ← params.mapM fun _ => mkFreshLevelMVar
  let specialized := type.instantiateLevelParams params.toList levels.toList
  unless ← isDefEq specialized expected do throwError "certificate does not prove this source goal"
  let proofParams := (collectLevelParams {} proof).params
  let proofLevels := proofParams.map fun p =>
    if let some i := params.findIdx? (· == p) then levels[i]! else Level.zero
  return ← instantiateMVars (proof.instantiateLevelParams proofParams.toList proofLevels.toList)

def verify (j : Json) (expected : Expr) (excluded : String := "") : MetaM Unit := do
  discard <| checkedProof j expected excluded

/-- Replay into the actual metavariable, so a witness chosen for one goal also
constrains every dependent sibling. Checking each goal's type separately is
insufficient when the source goals share metavariables. -/
def assign (j : Json) (goal : MVarId) (excluded : String := "") : MetaM Unit := goal.withContext do
  let expected ← instantiateMVars <|
    ← mkForallFVars (← getLCtx).getFVars (← goal.getType)
  let closed ← checkedProof j expected excluded
  let mut args := #[]
  for localDecl in ← getLCtx do
    if localDecl.value?.isNone then args := args.push localDecl.toExpr
  let proof ← instantiateMVars (mkAppN closed args)
  unless ← isDefEq (← inferType proof) (← goal.getType) do
    throwError "replayed proof does not inhabit the source goal"
  if ← goal.isAssigned then
    unless ← isDefEq (.mvar goal) proof do throwError "inconsistent shared goal assignment"
  else
    goal.assign proof

end JevHammerBenchmark.Certificate
