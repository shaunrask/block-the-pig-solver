{:name "BTP Move Certification (Grounded)"
 :description "ShadowProver certifies PlaceWall legality for ONE concrete cell (with needed negatives)"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_1_m5)
  A2 (HasWall C_m2_m4)
  A3 (HasWall C_m1_m1)
  A4 (HasWall C_m1_1)
  A5 (HasWall C_m2_1)
  A6 (HasWall C_0_3)
  A7 (HasWall C_m2_m1)
  A8 (HasWall C_1_3)
  A9 (HasWall C_m1_m5)
  A10 (not (OccupiedByPig c_1_0))
  A11 (not (HasWall c_1_0))
  A12 (if (and (not (OccupiedByPig c_1_0)) (not (HasWall c_1_0))) (CanPlaceWall c_1_0))
 }
 :goal (CanPlaceWall c_1_0)
}