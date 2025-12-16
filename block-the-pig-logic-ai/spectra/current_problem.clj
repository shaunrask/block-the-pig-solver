{:name "Block the Pig - Reachability"
 :background [
    (Adjacent C_0_7 C_1_6)
    (Adjacent C_0_7 C_0_6)
    (Adjacent C_1_6 C_0_6)
    (Adjacent C_1_6 C_0_7)
    (Adjacent C_0_6 C_1_6)
    (Adjacent C_0_6 C_0_7)
    (Escape C_0_7)
    (Escape C_0_6)
    (PigAt C_1_6)
    (forall (?c) (if (PigAt ?c) (Reachable ?c)))
    (forall (?c1 ?c2) (if (and (Reachable ?c1) (Adjacent ?c1 ?c2) (Free ?c2)) (Reachable ?c2)))
 ]
 :actions [
    (define-action PlaceWall [?c] {
        :preconditions [(Free ?c)]
        :additions     [(Blocked ?c)]
        :deletions     [(Free ?c)]
    })
 ]
 :start [
    (Free C_0_7)
    (Free C_0_6)
 ]
 :goal [
    (not (exists (?e) (and (Escape ?e) (Reachable ?e))))
 ]
}