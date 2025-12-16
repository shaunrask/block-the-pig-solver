{:name "BTP Move Certification (Grounded)"
 :description "ShadowProver certifies PlaceWall legality for ONE concrete cell (no forall)"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_2_4)
  A2 (HasWall C_0_2)
  A3 (HasWall C_0_1)
  A4 (HasWall C_0_m3)
  A5 (HasWall C_m2_m4)
  A6 (HasWall C_m1_4)
  A7 (HasWall C_m2_4)
  A8 (HasWall C_m1_m2)
  A9 (HasWall C_0_5)
  A10 (HasWall C_m1_1)
  A11 (HasWall C_1_5)
  A12 (if (OccupiedByPig c_1_0) (not (CanPlaceWall c_1_0)))
  A13 (if (HasWall c_1_0) (not (CanPlaceWall c_1_0)))
  A14 (if (and (not (OccupiedByPig c_1_0)) (not (HasWall c_1_0))) (CanPlaceWall c_1_0))
 }
 :goal (CanPlaceWall c_1_0)
}