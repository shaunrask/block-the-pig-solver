{:name "BTP Move Certification"
 :description "ShadowProver certifies PlaceWall legality"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_0_m2)
  A2 (HasWall C_0_5)
  A3 (HasWall C_m2_m3)
  A4 (HasWall C_0_m5)
  A5 (HasWall C_1_2)
  A6 (HasWall C_2_1)
  A7 (HasWall C_0_2)
  A8 (HasWall C_1_0)
  A9 (HasWall C_2_m1)
  A10 (HasWall C_m1_2)
  A11 (HasWall C_m2_4)
  A12 (HasWall C_m2_2)
  A13 (HasWall C_m2_5)
  A14 (HasWall C_2_m4)
  A15 (forall (c) (if (OccupiedByPig c) (not (CanPlaceWall c))))
  A16 (forall (c) (if (HasWall c) (not (CanPlaceWall c))))
  A17 (forall (c) (if (and (not (OccupiedByPig c)) (not (HasWall c))) (CanPlaceWall c)))
 }
 :goal (CanPlaceWall c_m1_0)
}