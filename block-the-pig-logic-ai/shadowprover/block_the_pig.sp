;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Block the Pig — ShadowProver Domain
;; Modeled after spectra-examples formatting conventions
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; --- SORTS ----------------------------------------------------------

sort Cell.
sort Pig.
sort Wall.

; --- PREDICATES -----------------------------------------------------

pred Adjacent(Cell, Cell).           ; Hex-grid adjacency
pred OccupiedByPig(Cell).           ; Pig location
pred HasWall(Cell).                 ; Wall placement
pred Free(Cell).                    ; A cell is free (no wall, not pig)
pred Escape(Cell).                  ; An exit cell on perimeter
pred NextPigCell(Cell, Cell).       ; Pig moves from A to B

; --- AXIOMS ---------------------------------------------------------

; A cell is free if and only if it is not a wall and not the pig.
axiom forall c:Cell. Free(c) <-> (¬HasWall(c) ∧ ¬OccupiedByPig(c)).

; Escape cells are free by definition (Wait, if it has a wall it's not free. Escape is a property of the cell location)
; Actually, Escape(c) means "c is an escape cell". It doesn't mean it's currently usable if blocked.
; The user said: "Escape cells are free by definition".
; But also "HasWall(c) -> ¬Escape(c)".
; Let's clarify: Escape(c) is a static property "is on the edge".
; Free(c) is a dynamic property "is available".
; So Escape(c) does NOT imply Free(c) if there is a wall.
; But the user's snippet said: "axiom forall c:Cell. Escape(c) -> Free(c)."
; This implies you CANNOT place a wall on an escape cell?
; If I add "HasWall(c) -> ¬Escape(c)", then yes, you can't place a wall there.
; So if it is Escape, it must be Free (assuming no pig there).
; Let's stick to the user's constraints.

axiom forall c:Cell. OccupiedByPig(c) -> ¬HasWall(c).
axiom forall c:Cell. HasWall(c) -> ¬Escape(c).

; Pig moves only to adjacent free cells
axiom forall a,b:Cell. NextPigCell(a,b) ->
    (Adjacent(a,b) ∧ Free(b)).

; Add hex-grid adjacency from imported file
include "hexgrid.sp".

; --- TRAP CONDITION -------------------------------------------------

; The pig is trapped if ALL adjacent cells are blocked by walls
pred Trapped.

axiom Trapped <->
  forall c1:Cell (
    OccupiedByPig(c1) ->
       forall c2:Cell (
           Adjacent(c1,c2) ->
             HasWall(c2)
       )
  ).

; End File
