{:name "Move Constraint Check"
 :description "ShadowProver verifying move validity"
 :assumptions {
  A0 (OccupiedByPig C_2_5)
  A1 (HasWall C_1_2)
  A2 (HasWall C_1_5)
  A3 (HasWall C_1_8)
  A4 (HasWall C_4_2)
  A5 (HasWall C_3_0)
  A6 (HasWall C_2_3)
  A7 (HasWall C_0_2)
  A8 (HasWall C_1_7)
  A9 (HasWall C_2_6)
  A10 (HasWall C_0_5)
  A11 (HasWall C_1_0)
  A12 (HasWall C_1_6)
  A13 (HasWall C_3_2)
  A14 (forall (c) (if (OccupiedByPig c) (not (CanPlaceWall c))))
  A15 (forall (c) (if (HasWall c) (not (CanPlaceWall c))))
  A16 (forall (c) (if (and (not (OccupiedByPig c)) (not (HasWall c))) (CanPlaceWall c)))
 }
 :goal (CanPlaceWall C_3_5)
}