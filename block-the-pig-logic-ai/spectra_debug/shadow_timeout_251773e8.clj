{:name "BTP Move Certification"
 :description "ShadowProver certifies PlaceWall legality"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_1_2)
  A2 (HasWall C_1_0)
  A3 (HasWall C_m2_5)
  A4 (HasWall C_m2_m5)
  A5 (HasWall C_1_4)
  A6 (HasWall C_0_3)
  A7 (HasWall C_m1_0)
  A8 (HasWall C_2_m2)
  A9 (HasWall C_m2_2)
  A10 (HasWall C_m1_5)
  A11 (HasWall C_1_3)
  A12 (HasWall C_0_m2)
  A13 (forall (c) (if (OccupiedByPig c) (not (CanPlaceWall c))))
  A14 (forall (c) (if (HasWall c) (not (CanPlaceWall c))))
  A15 (forall (c) (if (and (not (OccupiedByPig c)) (not (HasWall c))) (CanPlaceWall c)))
 }
 :goal (CanPlaceWall c_1_m1)
}