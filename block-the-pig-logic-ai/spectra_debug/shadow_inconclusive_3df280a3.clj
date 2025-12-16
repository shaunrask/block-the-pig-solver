{:name "BTP Move Certification (Grounded)"
 :description "ShadowProver certifies PlaceWall legality for ONE concrete cell (with needed negatives)"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_1_m4)
  A2 (HasWall C_m1_m1)
  A3 (HasWall C_m2_1)
  A4 (HasWall C_1_2)
  A5 (HasWall C_2_3)
  A6 (HasWall C_m2_2)
  A7 (HasWall C_m2_m4)
  A8 (HasWall C_0_m2)
  A9 (HasWall C_1_3)
  A10 (HasWall C_m1_3)
  A11 (HasWall C_0_m5)
  A12 (HasWall C_2_0)
  A13 (HasWall C_2_4)
  A14 (HasWall C_1_m1)
  A15 (not (OccupiedByPig c_1_0))
  A16 (not (HasWall c_1_0))
  A17 (if (and (not (OccupiedByPig c_1_0)) (not (HasWall c_1_0))) (CanPlaceWall c_1_0))
 }
 :goal (CanPlaceWall c_1_0)
}