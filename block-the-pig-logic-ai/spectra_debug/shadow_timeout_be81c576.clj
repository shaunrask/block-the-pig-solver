{:name "BTP Move Certification"
 :description "ShadowProver certifies PlaceWall legality"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_0_5)
  A2 (HasWall C_1_3)
  A3 (HasWall C_m1_2)
  A4 (HasWall C_2_m5)
  A5 (HasWall C_m2_m1)
  A6 (HasWall C_m1_4)
  A7 (HasWall C_2_2)
  A8 (HasWall C_0_3)
  A9 (forall (c) (if (OccupiedByPig c) (not (CanPlaceWall c))))
  A10 (forall (c) (if (HasWall c) (not (CanPlaceWall c))))
  A11 (forall (c) (if (and (not (OccupiedByPig c)) (not (HasWall c))) (CanPlaceWall c)))
 }
 :goal (CanPlaceWall c_1_0)
}