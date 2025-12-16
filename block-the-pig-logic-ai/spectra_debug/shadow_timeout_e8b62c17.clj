{:name "BTP Move Certification (Grounded)"
 :description "ShadowProver certifies PlaceWall legality for ONE concrete cell (with needed negatives)"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_0_2)
  A2 (HasWall C_0_m1)
  A3 (HasWall C_0_m5)
  A4 (HasWall C_1_5)
  A5 (HasWall C_1_m3)
  A6 (HasWall C_2_1)
  A7 (HasWall C_m1_1)
  A8 (HasWall C_m1_3)
  A9 (HasWall C_m1_m3)
  A10 (HasWall C_m2_0)
  A11 (HasWall C_m2_3)
  A12 (not (OccupiedByPig C_1_0))
  A13 (not (HasWall C_1_0))
  A14 (if (and (not (OccupiedByPig C_1_0)) (not (HasWall C_1_0))) (CanPlaceWall C_1_0))
 }
 :goal (CanPlaceWall C_1_0)
}