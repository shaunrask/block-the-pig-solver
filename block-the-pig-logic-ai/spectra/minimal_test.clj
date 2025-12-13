{:name "Minimal PlaceWall Test"
 :background []
 :actions [
    (define-action PlaceWall [?c] {
        :preconditions [(Free ?c)]
        :additions [(HasWall ?c)]
        :deletions [(Free ?c)]
    })
 ]
 :start [
    (Free C_3_4)
 ]
 :goal [
    (HasWall C_3_4)
 ]
}
