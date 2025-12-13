{:name       "Block the Pig Planning"
 :background []
 :actions    [
    (define-action PlaceWall [?c] {
        :preconditions [(Free ?c)]
        :additions     [(HasWall ?c)]
        :deletions     [(Free ?c)]
    })
 ]
 :start      [
    (Free C_3_5)
 ]
 :goal       [(HasWall C_3_5)]
}
