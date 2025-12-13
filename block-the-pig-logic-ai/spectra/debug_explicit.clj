{:name "Explicit Goal Test"
 :background [
    (Adjacent C_0_0 C_0_1)
    (Adjacent C_0_1 C_0_0)
    (Adjacent C_0_0 C_1_0)
    (Adjacent C_1_0 C_0_0)
    (Adjacent C_0_0 C_1_m1)
    (Adjacent C_1_m1 C_0_0)
    (Adjacent C_0_0 C_0_m1)
    (Adjacent C_0_m1 C_0_0)
    (Adjacent C_0_0 C_m1_0)
    (Adjacent C_m1_0 C_0_0)
    (Adjacent C_0_0 C_m1_1)
    (Adjacent C_m1_1 C_0_0)
    
    (HasWall C_1_0)
    (HasWall C_1_m1)
    (HasWall C_0_m1)
    (HasWall C_m1_0)
    (HasWall C_m1_1)
    
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
    (HasWall C_1_0)
    (HasWall C_1_m1)
    (HasWall C_0_m1)
    (HasWall C_m1_0)
    (HasWall C_m1_1)
 ]
 :goal [
    (forall (c1) (if (OccupiedByPig c1) (forall (c2) (if (Adjacent c1 c2) (HasWall c2)))))
 ]
}