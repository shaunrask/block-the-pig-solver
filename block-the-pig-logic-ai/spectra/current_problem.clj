{:name       "Block the Pig"
 :background [
    (AdjacentToPig C_2_5)
    (AdjacentToPig C_1_4)
    (AdjacentToPig C_0_5)
    (AdjacentToPig C_1_6)
    (AdjacentToPig C_2_6)
 ]
 :actions    [
    (define-action PlaceWall [?c] {
        :preconditions [(Free ?c) (AdjacentToPig ?c)]
        :additions     [(Blocked ?c)]
        :deletions     [(Free ?c)]
    })
 ]
 :start      [
    (Free C_2_5)
    (Free C_1_4)
    (Free C_0_5)
    (Free C_1_6)
    (Free C_2_6)
 ]
 :goal       [(exists (?x) (Blocked ?x))]
}