{:name "BTP Move Certification (Grounded)"
 :description "ShadowProver certifies PlaceWall legality for ONE concrete cell (no forall)"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_m1_0)
  A2 (HasWall C_1_2)
  A3 (HasWall C_0_m1)
  A4 (HasWall C_m1_m1)
  A5 (HasWall C_m1_m3)
  A6 (HasWall C_m1_m5)
  A7 (HasWall C_1_0)
  A8 (HasWall C_m2_2)
  A9 (HasWall C_0_m2)
  A10 (if (OccupiedByPig c_1_m1) (not (CanPlaceWall c_1_m1)))
  A11 (if (HasWall c_1_m1) (not (CanPlaceWall c_1_m1)))
  A12 (if (and (not (OccupiedByPig c_1_m1)) (not (HasWall c_1_m1))) (CanPlaceWall c_1_m1))
 }
 :goal (CanPlaceWall c_1_m1)
}