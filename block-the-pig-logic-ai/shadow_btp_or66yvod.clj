{:name "BTP Move Certification"
 :description "ShadowProver certifies PlaceWall legality"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_2_m2)
  A2 (HasWall C_m1_m4)
  A3 (HasWall C_m1_5)
  A4 (HasWall C_1_m2)
  A5 (HasWall C_1_0)
  A6 (HasWall C_1_3)
  A7 (HasWall C_1_m4)
  A8 (HasWall C_m1_1)
  A9 (HasWall C_2_0)
  A10 (HasWall C_0_3)
  A11 (HasWall C_2_m3)
  A12 (HasWall C_m1_m1)
  A13 (HasWall C_m2_0)
  A14 (HasWall C_0_m5)
  A15 (forall (c) (if (OccupiedByPig c) (not (CanPlaceWall c))))
  A16 (forall (c) (if (HasWall c) (not (CanPlaceWall c))))
  A17 (forall (c) (if (and (not (OccupiedByPig c)) (not (HasWall c))) (CanPlaceWall c)))
 }
 :goal (CanPlaceWall c_1_m1)
}