;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Block the Pig — Spectra Planning Problem
;; Structured like spectra-examples
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

include "../shadowprover/block_the_pig.sp".
include "domain_axioms.p".

state {
    OccupiedByPig(c) : Cell.
    HasWall(c)       : Cell.
    Free(c)          : Cell.
    Escape(c)        : Cell.
}

action PlaceWall(c : Cell) {
    pre  Free(c).
    eff  HasWall(c).
}

action PigMove(a : Cell, b : Cell) {
    pre  (OccupiedByPig(a) ∧ NextPigCell(a,b)).
    eff  (OccupiedByPig(b) ∧ ¬OccupiedByPig(a)).
}

initial {
    ; Initial pig position at Center
    OccupiedByPig(C_0_0).
}

goal {
    Trapped.
}

constraint {
    ; Once a wall is placed, it remains
    always forall c:Cell. HasWall(c) -> next HasWall(c).
}

plan {
    ; Minimize number of wall placements required to trap the pig
    minimize steps.
}
