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
    (OccupiedByPig C_0_0)
    (HasWall C_0_2)
    (HasWall C_0_m4)
    (HasWall C_0_m5)
    (HasWall C_1_0)
    (HasWall C_1_1)
    (HasWall C_1_3)
    (HasWall C_1_m1)
    (HasWall C_1_m3)
    (HasWall C_1_m5)
    (HasWall C_2_0)
    (HasWall C_m1_1)
    (HasWall C_m1_m1)
    (HasWall C_m2_4)
    (HasWall C_m2_m2)
    (HasWall C_m2_m4)
    (Free C_0_1)
    (Free C_0_3)
    (Free C_0_4)
    (Free C_0_5)
    (Free C_0_m1)
    (Free C_0_m2)
    (Free C_0_m3)
    (Free C_1_2)
    (Free C_1_4)
    (Free C_1_5)
    (Free C_1_m2)
    (Free C_1_m4)
    (Free C_2_1)
    (Free C_2_2)
    (Free C_2_3)
    (Free C_2_4)
    (Free C_2_5)
    (Free C_2_m1)
    (Free C_2_m2)
    (Free C_2_m3)
    (Free C_2_m4)
    (Free C_2_m5)
    (Free C_m1_0)
    (Free C_m1_2)
    (Free C_m1_3)
    (Free C_m1_4)
    (Free C_m1_5)
    (Free C_m1_m2)
    (Free C_m1_m3)
    (Free C_m1_m4)
    (Free C_m1_m5)
    (Free C_m2_0)
    (Free C_m2_1)
    (Free C_m2_2)
    (Free C_m2_3)
    (Free C_m2_5)
    (Free C_m2_m1)
    (Free C_m2_m3)
    (Free C_m2_m5)
 ]
:goal [
    (HasWall C_m2_0)
 ]
}
