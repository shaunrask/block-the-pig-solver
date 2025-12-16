%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% domain_axioms.p — Block the Pig (Spectra/ShadowProver)
%% Purpose:
%%   - Bridge NextPigCell to Adjacent (your .spc uses NextPigCell)
%%   - Enforce core invariants (no pig-on-wall, no wall-on-escape)
%%   - Define Trapped (local trap definition, matches your .clj)
%%   - Keep Free consistent with HasWall / OccupiedByPig
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% 1) Movement relation used by the Spectra model:
%%    Your .spc action PigMove uses NextPigCell(a,b),
%%    but your .clj uses Adjacent. This axiom equates them.
forall a:Cell, b:Cell. NextPigCell(a,b) <-> Adjacent(a,b).

%% 2) Core legality invariants (state consistency)
%% Pig cannot occupy a cell that has a wall.
forall c:Cell. OccupiedByPig(c) -> ~HasWall(c).

%% Walls cannot be on escape cells (matches your .clj background constraint).
forall c:Cell. HasWall(c) -> ~Escape(c).

%% A cell cannot be both Free and HasWall.
forall c:Cell. HasWall(c) -> ~Free(c).

%% The pig’s occupied cell is not Free.
forall c:Cell. OccupiedByPig(c) -> ~Free(c).

%% 3) Trap definition (local trap: all adjacent neighbors are walled)
%% Matches your .clj:
%%   (iff Trapped (forall (c1) (if (OccupiedByPig c1)
%%       (forall (c2) (if (Adjacent c1 c2) (HasWall c2))))))
Trapped <->
  forall c1:Cell.
    (OccupiedByPig(c1) -> forall c2:Cell. (Adjacent(c1,c2) -> HasWall(c2))).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Optional (enable if you want tighter modeling):
%% If you don’t explicitly maintain Free as a fluent, you can
%% force it to be the complement of walls and pig position.
%%
%% Uncomment ONLY if it matches how your includes treat Free.
%%
%% forall c:Cell. Free(c) <-> (~HasWall(c) & ~OccupiedByPig(c)).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
