{:name "Simple Wall Test"
 :background [
    (Adjacent C_0_0 C_0_1)
    (Adjacent C_0_1 C_0_0)
    (Free C_0_1)
    (OccupiedByPig C_0_0)
    (forall (c) (if (OccupiedByPig c) (not (HasWall c))))
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
    (Free C_0_1)
 ]
 :goal [
    (HasWall C_0_1)
 ]
}