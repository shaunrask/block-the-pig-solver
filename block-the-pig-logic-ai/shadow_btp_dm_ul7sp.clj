{:name "BTP Move Certification (Grounded)"
 :description "ShadowProver certifies PlaceWall legality for ONE concrete cell (no forall)"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_m2_4)
  A2 (HasWall C_1_4)
  A3 (HasWall C_m2_3)
  A4 (HasWall C_m2_1)
  A5 (HasWall C_2_3)
  A6 (HasWall C_0_m2)
  A7 (HasWall C_1_5)
  A8 (HasWall C_0_5)
  A9 (HasWall C_m1_5)
  A10 (HasWall C_2_m1)
  A11 (HasWall C_m1_m4)
  A12 (if (OccupiedByPig C_1_0) (not (CanPlaceWall C_1_0)))
  A13 (if (HasWall C_1_0) (not (CanPlaceWall C_1_0)))
  A14 (if (and (not (OccupiedByPig C_1_0)) (not (HasWall C_1_0))) (CanPlaceWall C_1_0))
 }
 :goal (CanPlaceWall C_1_0)
}