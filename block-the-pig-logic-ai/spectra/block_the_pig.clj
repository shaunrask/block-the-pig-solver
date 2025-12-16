{:name "Block the Pig Planning (One-Step Wall Planner)"
 :background [
    ; Intentionally empty for speed.
    ; For one-step wall planning, adjacency/escape facts are not needed.
 ]

 :actions [
    (define-action PlaceWall [?c] {
        :preconditions [(Free ?c)]
        :additions [(HasWall ?c)]
        :deletions [(Free ?c)]
    })
 ]

 :start [
    ; NOTE: app.py overwrites this entire :start block at runtime.
    (OccupiedByPig C_0_0)
 ]

 :goal [
    ; NOTE: app.py overwrites this entire :goal block at runtime.
    (HasWall C_0_1)
 ]
}
