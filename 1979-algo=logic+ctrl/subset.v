(* This file is licensed under the GNU GPL v3. *)
(* Copyright (C) 2026 Guanyuming He. *)

(**
	In Kowalski's Algorithm = Logic + Control 1979,
	he defines the subset relation using Horn clauses as
	$x \subset y,\ arb(x,y) \in x \leftarrow$ 
	$x \subset y \leftarrow arb(x,y) \in y$ 

	Now, I am going to prove (or disprove) that
	this defn is equivalent to the usual defn
	$x \subset y := \forall a (a \in x \to a \in y)$
*)

From Stdlib Require Import Logic.Classical.

Definition subset {A: Type} (X Y: A -> Prop) :=
	forall a : A, X a -> Y a.

Lemma imply_iff_or (P Q: Prop) :
	(P -> Q) <-> (~P) \/ Q.
Proof.
	split.
	- intros Imply.
		destruct (classic P).
		+ apply Imply in H.
			right. apply H.
		+ left. apply H.
	- intros Or. destruct Or.
		+ intros HP. contradiction.
		+ intros HP. apply H.
Qed.

Lemma not_exists_to_forall {A : Type} (P : A -> Prop) :
	(~ exists a : A, ~(P a)) -> forall b : A, P(b).
Proof.
	unfold not.
	intros H b.
	destruct (classic (P b)).
	- apply H0.
	- exfalso.
		apply H.
		exists b.
		apply H0.
Qed.

(* Try to turn the defn of subset into using exists quantifier only *)
Theorem subset_exist {A: Type} (X Y: A -> Prop) :
	subset X Y <-> ~ (exists a : A, ~(~(X a) \/ Y a)).
Proof.
	split.
	- (* subset X Y -> ~exists *)
		intros H.
		unfold not.
		intros Ext.
		unfold subset in H. 
		destruct Ext as [a E].
		apply E.
		rewrite <- (imply_iff_or (X a) (Y a)).
		apply H.
	- (* ~exists -> subset X Y *)
		unfold not. intros H.
		intros a.
		rewrite -> (imply_iff_or (X a) (Y a)).
		apply (
			not_exists_to_forall 
			(fun a : A => ~(X a) \/ Y a) 
		) with (b:=a) in H.
		apply H.
Qed.

(* I don't really know what the function arb is.
	 This is written according to Wikipedia
	 https://en.wikipedia.org/wiki/Skolem_normal_form
	 But I don't know how to apply it.
*)
Axiom ARB :
	forall (A: Type) (X Y: A -> Prop),
	~(subset X Y) <->
	exists arb : ((A -> Prop) -> (A -> Prop) -> A), 
	(
		( X (arb X Y) /\ ~(Y (arb X Y)) )
	).

(*
Theorem defn_iff_clauses {A : Type} (X Y: A -> Prop) :
	(subset X Y) <-> (
		( (subset X Y) \/ X (arb X Y) )
		/\
		( Y (arb X Y) -> (subset X Y) )
	).
*)

(* OK, what if I just treat $arb(x,y) \in x$ and $arb(x,y) \in y$ as whole
 * atoms and just do this within propositional logic?
 * Let me find out.
	
	 Theorem subset_exist is like this, when treating the propotions as atoms 
	 Let 
	 A := subset X Y
	 B := X (arb X Y)
	 C := Y (arb X Y)

	 Then, we want to prove
	 A <-> ~~( ~B \/ C ) 
	 -||-
	 A \/ B && (clause 1)	 
	 A <- C		 (clause 2)
 *)

(* Just to abstract this tedious process away. Not meaningful otherwise. *)
Lemma double_negation (B C : Prop):
	(~B \/ C) <-> ~~(~B \/ C).
Proof.
	split.
	- intros H.
		unfold not.
		intros H1.
		apply H1.
		apply H.
	- apply NNPP.
Qed.

(* for contrapositive *)
From Stdlib Require Import Logic.Decidable.

(* Theorem subset_exist after atomization *)
Theorem atom_horn_clauses:
	forall (A B C : Prop),
	( A <-> ~~(~B \/ C) ) <->
	(A \/ B)
		/\
	(C -> A).
Proof.
	intros A B C.
	rewrite <- (double_negation B C).
	split.
	- intros H.
		split.
		+ destruct (classic A) as [HA|HNA].
			* left. exact HA.
			* destruct H as [L R].
				(* modus tollens *)
				rewrite <- (contrapositive A (~B \/ C)) in R.
				{ 
					assert (H1 := R HNA).
					destruct (classic B) as [HB|HNB].
					{
						right. exact HB.
				  }
					{
						exfalso.
						apply H1. left. apply HNB.
					}
				}
				{
					exact (classic A).
				}
		+ shelve. (* No. A=F, B=F, C=T. *)
	- intros [HAoB HCtoA].
		split.
		+ intros HA.
			shelve. (* No. A=T, B=T, C=F *)
		+ intros [HNB|HC].
			* destruct HAoB as [HA|HB].
				{ exact HA. }
				{ contradiction. }
			* exact (HCtoA HC).
	Unshelve.
	Abort. (* Can't complete the two shelved. *)





