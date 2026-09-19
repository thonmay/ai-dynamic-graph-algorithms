import Mathlib

/-!
# Strategy H2: a generic greedy abstraction, instantiated to dynamic MCS

MCS is one instance of "greedily pick the unchosen vertex maximizing a score,
ties broken by lowest index, append, repeat."  We formalize that pattern once
over a generic vertex type `V` with a generic `score : Finset V -> V -> Nat`,
prove the greedy builder correct and prove that a score which agrees on the
unchosen vertices yields the same legal picks, and then instantiate at
`score = G.neigh` to recover the dynamic-MCS correctness theorem.
-/

noncomputable section
open Classical
open scoped BigOperators

namespace Greedy

variable {V : Type*} [Fintype V] [DecidableEq V] [LinearOrder V]

/-- A legal greedy step given the already-chosen set `chosen`: `w` is unchosen,
its score is maximal among the unchosen vertices, and it is the least-index
vertex achieving that maximum. -/
def IsScoreNext (score : Finset V -> V -> Nat) (chosen : Finset V) (w : V) : Prop :=
  w ∈ (Finset.univ : Finset V) \ chosen ∧
  (∀ x : V, x ∈ (Finset.univ : Finset V) \ chosen → score chosen x ≤ score chosen w) ∧
  (∀ x : V, x ∈ (Finset.univ : Finset V) \ chosen → score chosen x = score chosen w → w ≤ x)

/-- Existence of a legal greedy pick whenever not every vertex is chosen. -/
theorem exists_IsScoreNext (score : Finset V -> V -> Nat) (chosen : Finset V) :
    chosen ≠ (Finset.univ : Finset V) -> ∃ w : V, IsScoreNext score chosen w := by
  classical
  intro hneq
  let U : Finset V := (Finset.univ : Finset V) \ chosen
  have hUnonempty : U.Nonempty := by
    apply Finset.nonempty_iff_ne_empty.mpr
    intro hUempty
    apply hneq
    apply Finset.ext
    intro x
    constructor
    · intro _; exact Finset.mem_univ x
    · intro _hxuniv
      by_contra hx
      have hxU : x ∈ U := Finset.mem_sdiff.mpr ⟨Finset.mem_univ x, hx⟩
      have hxempty : x ∈ (∅ : Finset V) := by simpa [U, hUempty] using hxU
      exact (Finset.notMem_empty x) hxempty
  rcases Finset.exists_max_image U (fun x => score chosen x) hUnonempty with
    ⟨w0, hw0U, hw0max⟩
  let M : Finset V := U.filter (fun x => score chosen x = score chosen w0)
  have hw0M : w0 ∈ M := Finset.mem_filter.mpr ⟨hw0U, rfl⟩
  have hMnonempty : M.Nonempty := ⟨w0, hw0M⟩
  let w : V := M.min' hMnonempty
  refine ⟨w, ?_⟩
  have hwM : w ∈ M := Finset.min'_mem M hMnonempty
  have hwU : w ∈ U := (Finset.mem_filter.mp hwM).1
  have hwcard : score chosen w = score chosen w0 := (Finset.mem_filter.mp hwM).2
  unfold IsScoreNext
  constructor
  · simpa [U] using hwU
  constructor
  · intro x hx
    have hxmax : score chosen x ≤ score chosen w0 := hw0max x hx
    rw [hwcard]; exact hxmax
  · intro x hx hc
    have hxM : x ∈ M := Finset.mem_filter.mpr ⟨hx, by rw [hc, hwcard]⟩
    change M.min' hMnonempty ≤ x
    exact Finset.min'_le M x hxM

/-- The deterministic greedy pick, carried with its legality proof. -/
noncomputable def greedyPick (score : Finset V -> V -> Nat) (chosen : Finset V)
    (h : chosen ≠ (Finset.univ : Finset V)) : { w : V // IsScoreNext score chosen w } :=
  ⟨Classical.choose (exists_IsScoreNext score chosen h),
   Classical.choose_spec (exists_IsScoreNext score chosen h)⟩

/-- Greedy loop: extend `chosen` with the greedy pick until full, one step per
unit of the counter `k`; `chosen.card + k = Fintype.card V` certifies progress. -/
noncomputable def greedyLoop (score : Finset V -> V -> Nat) (chosen : Finset V) (k : ℕ)
    (hk : chosen.card + k = Fintype.card V) : List V :=
  match k with
  | 0 => []
  | km + 1 =>
      have hchosen : chosen ≠ (Finset.univ : Finset V) := by
        intro hc
        have hcard : chosen.card = Fintype.card V := by simp [hc]
        omega
      let p := (greedyPick score chosen hchosen).1
      have hp : p ∉ chosen :=
        (Finset.mem_sdiff.mp (greedyPick score chosen hchosen).2.1).2
      have hins : (insert p chosen).card = chosen.card + 1 :=
        Finset.card_insert_of_notMem hp
      p :: greedyLoop score (insert p chosen) km (by omega)
termination_by k
decreasing_by
  all_goals simp_wf

/-- Greedy continuation of an already-chosen set. -/
noncomputable def greedyRemainder (score : Finset V -> V -> Nat) (chosen : Finset V) : List V :=
  greedyLoop score chosen (Fintype.card V - chosen.card) (by
    have hcard : chosen.card ≤ Fintype.card V := by simpa using Finset.card_le_univ chosen
    omega)

/-- Valid greedy ordering: every vertex once, each position a legal pick given
its prefix. -/
def IsValid (score : Finset V -> V -> Nat) (order : List V) : Prop :=
  order.Nodup ∧ order.length = Fintype.card V ∧
  ∀ (i : ℕ) (hi : i < order.length), IsScoreNext score (order.take i).toFinset (order.get ⟨i, hi⟩)

/-- Greedy continuation of a prefix. -/
noncomputable def greedySuffix (score : Finset V -> V -> Nat) (pref : List V) : List V :=
  pref ++ greedyRemainder score pref.toFinset

/-- Extending a valid greedy prefix by one legal pick yields a valid prefix. -/
lemma prefix_valid_append (score : Finset V -> V -> Nat) (pref : List V) (p : V)
    (hpref : ∀ (i : ℕ) (hi : i < pref.length),
      IsScoreNext score (pref.take i).toFinset (pref.get ⟨i, hi⟩))
    (hp : IsScoreNext score pref.toFinset p) :
    ∀ (i : ℕ) (hi : i < (pref ++ [p]).length),
      IsScoreNext score ((pref ++ [p]).take i).toFinset ((pref ++ [p]).get ⟨i, hi⟩) := by
  intro i hi
  by_cases hlt : i < pref.length
  · have htake : (pref ++ [p]).take i = pref.take i := by
      rw [List.take_append]
      have h0 : i - pref.length = 0 := Nat.sub_eq_zero_of_le (le_of_lt hlt)
      simp [h0]
    have hget : (pref ++ [p]).get ⟨i, hi⟩ = pref.get ⟨i, hlt⟩ := by
      apply List.getElem_append_left
    rw [htake, hget]; exact hpref i hlt
  · have hi_eq : i = pref.length := by
      have hle : pref.length ≤ i := le_of_not_gt hlt
      have hlt2 : i < pref.length + 1 := by
        have : (pref ++ [p]).length = pref.length + 1 := by simp
        rwa [this] at hi
      omega
    subst i
    have htake : (pref ++ [p]).take pref.length = pref := by rw [List.take_append]; simp
    have hget : (pref ++ [p]).get ⟨pref.length, hi⟩ = p := by
      simp [List.get_eq_getElem, List.getElem_append_right (le_refl pref.length)]
    rw [htake, hget]; exact hp

/-- Loop invariant: a valid greedy prefix whose chosen set is `chosen`, extended
by `greedyLoop`, is a valid greedy ordering. -/
lemma greedyLoop_valid (score : Finset V -> V -> Nat) (chosen : Finset V) (k : ℕ)
    (hk : chosen.card + k = Fintype.card V) :
    ∀ (pref : List V), pref.toFinset = chosen -> pref.Nodup ->
      (∀ (i : ℕ) (hi : i < pref.length),
        IsScoreNext score (pref.take i).toFinset (pref.get ⟨i, hi⟩)) ->
      IsValid score (pref ++ greedyLoop score chosen k hk) := by
  revert hk
  induction k generalizing chosen with
  | zero =>
      intro hk pref hprefF hprefNodup hpref
      unfold greedyLoop
      rw [List.append_nil]
      refine ⟨hprefNodup, ?_, hpref⟩
      have hcard : chosen.card = Fintype.card V := by rw [add_zero] at hk; exact hk
      calc pref.length = pref.toFinset.card := (List.toFinset_card_of_nodup hprefNodup).symm
        _ = chosen.card := by rw [hprefF]
        _ = Fintype.card V := hcard
  | succ km ih =>
      intro hk pref hprefF hprefNodup hpref
      have hchosen : chosen ≠ (Finset.univ : Finset V) := by
        intro hc
        have hcard : chosen.card = Fintype.card V := by simp [hc]
        omega
      set p := (greedyPick score chosen hchosen).1 with hpdef
      have hp : p ∉ chosen := (Finset.mem_sdiff.mp (greedyPick score chosen hchosen).2.1).2
      have hrec : (insert p chosen).card + km = Fintype.card V := by
        have hins : (insert p chosen).card = chosen.card + 1 := Finset.card_insert_of_notMem hp
        omega
      have hstep : pref ++ greedyLoop score chosen (km + 1) hk
          = (pref ++ [p]) ++ greedyLoop score (insert p chosen) km hrec := by
        rw [greedyLoop.eq_2, ← List.singleton_append, ← List.append_assoc]
      rw [hstep]
      refine ih (insert p chosen) hrec (pref ++ [p]) ?F ?N ?S
      · apply Finset.ext
        intro x
        rw [List.mem_toFinset, List.mem_append, List.mem_singleton, Finset.mem_insert,
          ← hprefF, ← List.mem_toFinset]
        apply Iff.intro
        · intro h; exact h.elim Or.inr Or.inl
        · intro h; exact h.elim Or.inr Or.inl
      · rw [List.nodup_append]
        refine ⟨hprefNodup, List.nodup_singleton p, ?_⟩
        intro a ha b hb
        rw [List.mem_singleton] at hb
        subst hb
        intro heq
        exact hp (by rw [← hprefF]; exact List.mem_toFinset.mpr (heq ▸ ha))
      · refine prefix_valid_append score pref p hpref ?_
        rw [hprefF]
        exact (greedyPick score chosen hchosen).2

/-- Recombining a valid greedy prefix with the greedy suffix yields a valid
greedy ordering. -/
lemma greedySuffix_valid (score : Finset V -> V -> Nat) (pref : List V) (hnodup : pref.Nodup)
    (hstep : ∀ (i : ℕ) (hi : i < pref.length),
      IsScoreNext score (pref.take i).toFinset (pref.get ⟨i, hi⟩)) :
    IsValid score (greedySuffix score pref) := by
  unfold greedySuffix greedyRemainder
  refine greedyLoop_valid score pref.toFinset (Fintype.card V - pref.toFinset.card) ?_ pref rfl
    hnodup hstep

/-- Two scores agreeing on all unchosen vertices yield the same legal picks. -/
lemma IsScoreNext_of_eq_score (score score' : Finset V -> V -> Nat) (chosen : Finset V) (w : V)
    (hscore : ∀ z : V, score chosen z = score' chosen z)
    (hnext : IsScoreNext score chosen w) : IsScoreNext score' chosen w := by
  classical
  rcases hnext with ⟨hwU, hwmax, hwmin⟩
  unfold IsScoreNext
  constructor
  · exact hwU
  constructor
  · intro x hx
    rw [← hscore x, ← hscore w]; exact hwmax x hx
  · intro x hx hc
    have hcw : score chosen x = score chosen w := by rw [hscore x, hscore w, hc]
    exact hwmin x hx hcw

/-- A valid greedy ordering contains every vertex. -/
lemma mem_of_IsValid (score : Finset V -> V -> Nat) (order : List V) (hvalid : IsValid score order) :
    ∀ z : V, z ∈ order := by
  classical
  intro z
  rcases hvalid with ⟨hnodup, hlen, _⟩
  have hcard : order.toFinset.card = Fintype.card V := by
    rw [List.toFinset_card_of_nodup hnodup, hlen]
  have htofinset : order.toFinset = (Finset.univ : Finset V) :=
    Finset.eq_univ_of_card order.toFinset hcard
  exact List.mem_toFinset.mp (by rw [htofinset]; exact Finset.mem_univ z)

/-- Position (in `order`) of the earlier of `u` and `v`. -/
def earlierPos (order : List V) (u v : V) : ℕ := min (List.idxOf u order) (List.idxOf v order)

/-- `earlierPos` is at most the position of each endpoint. -/
lemma le_idxOf_of_le_earlierPos (u v : V) (order : List V) {i : ℕ}
    (hi : i ≤ earlierPos order u v) : i ≤ List.idxOf u order ∧ i ≤ List.idxOf v order := by
  unfold earlierPos at hi
  exact ⟨le_trans hi (Nat.min_le_left _ _), le_trans hi (Nat.min_le_right _ _)⟩

/-- Before the earlier endpoint is chosen, neither endpoint is in the prefix. -/
lemma endpoints_not_in_prefix (order : List V) (u v : V)
    (hmu : u ∈ order) (hmv : v ∈ order) {i : ℕ} (hi : i ≤ earlierPos order u v) :
    u ∉ order.take i ∧ v ∉ order.take i := by
  rcases le_idxOf_of_le_earlierPos u v order hi with ⟨hu, hv⟩
  exact ⟨by rw [List.mem_take_iff_idxOf_lt hmu]; omega, by rw [List.mem_take_iff_idxOf_lt hmv]; omega⟩

/-- The greedy prefix up to the earlier of `u`, `v` is preserved by any score
change that does not touch the prefix's chosen set. -/
lemma prefix_preserved (score score' : Finset V -> V -> Nat) (order : List V) (u v : V)
    (hvalid : IsValid score order)
    (hagree : ∀ (i : ℕ), i ≤ earlierPos order u v → i < order.length →
      ∀ z : V, score (order.take i).toFinset z = score' (order.take i).toFinset z)
    (i : ℕ) (hi0 : i ≤ earlierPos order u v) (hi : i < order.length) :
    IsScoreNext score' (order.take i).toFinset (order.get ⟨i, hi⟩) := by
  have hmu : u ∈ order := mem_of_IsValid score order hvalid u
  have hmv : v ∈ order := mem_of_IsValid score order hvalid v
  rcases hvalid with ⟨_, _, hstep⟩
  exact IsScoreNext_of_eq_score score score' (order.take i).toFinset (order.get ⟨i, hi⟩)
    (hagree i hi0 hi) (hstep i hi)

end Greedy

/-! ## MCS instantiation -/

namespace DynamicMCS

abbrev Vert (n : ℕ) := Fin n

structure UGraph (n : ℕ) where
  adj : Vert n → Vert n → Prop
  symm : ∀ {x y : Vert n}, adj x y → adj y x
  loopless : ∀ (x : Vert n), ¬ adj x x

namespace UGraph
variable {n : ℕ} {G G' : UGraph n}

/-- MCS cardinality of `w` against the chosen set. -/
def neigh (G : UGraph n) (chosen : Finset (Vert n)) (w : Vert n) : ℕ := by
  classical
  exact chosen.card - (chosen.filter (fun x => ¬ G.adj w x)).card

/-- `G'` differs from `G` only by flipping the undirected edge `{u, v}`. -/
def FlipOf (G G' : UGraph n) (u v : Vert n) : Prop :=
  u ≠ v ∧
  ∀ (x y : Vert n), G'.adj x y = G.adj x y ∨ (x = u ∧ y = v) ∨ (x = v ∧ y = u)

-- The MCS ordering predicate is *definitionally* the generic greedy predicate on
-- the cardinality score.
abbrev IsMCSNext (G : UGraph n) (chosen : Finset (Vert n)) (w : Vert n) : Prop :=
  Greedy.IsScoreNext (G.neigh) chosen w
abbrev IsMCSOrdering (G : UGraph n) (order : List (Vert n)) : Prop :=
  Greedy.IsValid (G.neigh) order
def ValidMCSState (G : UGraph n) (order : List (Vert n)) : Prop := IsMCSOrdering G order

/-- An edge flip does not change any vertex's cardinality while neither endpoint
is chosen. -/
lemma neigh_eq_of_flip (chosen : Finset (Vert n)) (u v : Vert n)
    (hflip : FlipOf G G' u v) (hu : u ∉ chosen) (hv : v ∉ chosen) :
    ∀ z : Vert n, G.neigh chosen z = G'.neigh chosen z := by
  classical
  intro z
  unfold neigh
  have hfilter : chosen.filter (fun x => ¬ G.adj z x) = chosen.filter (fun x => ¬ G'.adj z x) := by
    apply Finset.filter_congr
    intro x hxchosen
    constructor
    · intro hnot hadj
      apply hnot
      rcases hflip with ⟨huv, hflipadj⟩
      have heq : G.adj z x = G'.adj z x := by
        rcases hflipadj z x with h | h' | h'
        · exact h.symm
        · rcases h' with ⟨rfl, rfl⟩; exfalso; exact hv hxchosen
        · rcases h' with ⟨rfl, rfl⟩; exfalso; exact hu hxchosen
      exact heq ▸ hadj
    · intro hnot hadj
      apply hnot
      rcases hflip with ⟨huv, hflipadj⟩
      have heq : G'.adj z x = G.adj z x := by
        rcases hflipadj z x with h | h' | h'
        · exact h
        · rcases h' with ⟨rfl, rfl⟩; exfalso; exact hv hxchosen
        · rcases h' with ⟨rfl, rfl⟩; exfalso; exact hu hxchosen
      exact heq ▸ hadj
  rw [hfilter]

noncomputable def greedySuffix (G : UGraph n) (pref : List (Vert n)) : List (Vert n) :=
  Greedy.greedySuffix (G.neigh) pref

noncomputable def mcsUpdate (G : UGraph n) (u v : Vert n) (order : List (Vert n)) :
    List (Vert n) :=
  if h : u = v then order else greedySuffix G (order.take (Greedy.earlierPos order u v + 1))

/-- The dynamic update preserves the MCS-ordering invariant under a single
edge flip. -/
theorem mcsUpdate_preserves_invariant (u v : Vert n) (order : List (Vert n))
    (hflip : FlipOf G G' u v) (hvalid : IsMCSOrdering G order) :
    IsMCSOrdering G' (mcsUpdate G' u v order) := by
  classical
  have huv : u ≠ v := hflip.1
  have hmemu : u ∈ order := Greedy.mem_of_IsValid (G.neigh) order hvalid u
  have hmemv : v ∈ order := Greedy.mem_of_IsValid (G.neigh) order hvalid v
  rw [mcsUpdate, dite_eq_right huv]
  have hbound : Greedy.earlierPos order u v + 1 ≤ order.length := by
    have hpos : List.idxOf u order < order.length := List.idxOf_lt_length_of_mem hmemu
    have : min (List.idxOf u order) (List.idxOf v order) ≤ List.idxOf u order := Nat.min_le_left _ _
    unfold Greedy.earlierPos at *
    omega
  refine Greedy.greedySuffix_valid (G'.neigh) (order.take (Greedy.earlierPos order u v + 1))
    (List.Pairwise.take hvalid.1) ?S
  intro i hi
  have hlt : i < order.length :=
    Nat.lt_of_lt_of_le (Nat.lt_of_lt_of_le hi (List.length_take_le _ _)) hbound
  have hi0 : i ≤ Greedy.earlierPos order u v :=
    Nat.lt_succ_iff.mp (Nat.lt_of_lt_of_le hi (List.length_take_le _ _))
  have htake : (order.take (Greedy.earlierPos order u v + 1)).take i = order.take i := by
    rw [List.take_take, Nat.min_eq_left (Nat.le_succ_of_le hi0)]
  have hget : (order.take (Greedy.earlierPos order u v + 1)).get ⟨i, hi⟩ = order.get ⟨i, hlt⟩ := by
    rw [List.get_eq_getElem, List.get_eq_getElem, List.getElem_take]
  rw [htake, hget]
  refine Greedy.prefix_preserved (G.neigh) (G'.neigh) order u v hvalid ?_ i hi0 hlt
  intro j hj0 hjl z
  rcases Greedy.endpoints_not_in_prefix order u v hmemu hmemv hj0 with ⟨huF, hvF⟩
  exact neigh_eq_of_flip (order.take j).toFinset u v hflip
    (fun h => huF (List.mem_toFinset.mp h)) (fun h => hvF (List.mem_toFinset.mp h)) z

theorem insert_edge_valid (u v : Vert n) (order : List (Vert n))
    (hflip : FlipOf G G' u v) (hvalid : IsMCSOrdering G order) :
    ValidMCSState G' (mcsUpdate G' u v order) :=
  mcsUpdate_preserves_invariant u v order hflip hvalid

theorem delete_edge_valid (u v : Vert n) (order : List (Vert n))
    (hflip : FlipOf G G' u v) (hvalid : IsMCSOrdering G order) :
    ValidMCSState G' (mcsUpdate G' u v order) :=
  mcsUpdate_preserves_invariant u v order hflip hvalid

theorem init_valid (G : UGraph n) : ValidMCSState G (greedySuffix G []) := by
  unfold ValidMCSState greedySuffix
  refine Greedy.greedySuffix_valid (G.neigh) [] List.nodup_nil ?_
  intro i hi
  rw [List.length_nil] at hi
  exact absurd hi (Nat.not_lt_zero i)

end UGraph
end DynamicMCS

#print axioms DynamicMCS.UGraph.mcsUpdate_preserves_invariant
#print axioms DynamicMCS.UGraph.init_valid
#print axioms DynamicMCS.UGraph.insert_edge_valid
