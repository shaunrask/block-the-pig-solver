{:name "BTP Move Certification (Grounded)"
 :description "ShadowProver certifies PlaceWall legality for ONE concrete cell (with needed negatives)"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_m2_1)
  A2 (HasWall C_m1_0)
  A3 (HasWall C_2_0)
  A4 (HasWall C_m1_m3)
  A5 (HasWall C_m1_3)
  A6 (HasWall C_1_m4)
  A7 (HasWall C_1_m1)
  A8 (not (OccupiedByPig c_1_0))
  A9 (not (HasWall c_1_0))
  A10 (if (and (not (OccupiedByPig c_1_0)) (not (HasWall c_1_0))) (CanPlaceWall c_1_0))
 }
 :goal (CanPlaceWall c_1_0)
}