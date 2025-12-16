{:name "ShadowCert"
 :assumptions {
  A0 (OccupiedByPig C_0_0)
  A1 (HasWall C_m1_0)
  A2 (HasWall C_1_4)
  A3 (HasWall C_2_1)
  A4 (HasWall C_1_3)
  A5 (HasWall C_0_m1)
  A6 (HasWall C_0_m5)
  A7 (HasWall C_m1_4)
  A8 (HasWall C_1_m2)
  A9 (HasWall C_m1_m2)
  A10 (HasWall C_1_5)
  A11 (HasWall C_0_2)
  A12 (HasWall C_0_m4)
  A13 (HasWall C_1_2)
  A14 (HasWall C_2_m2)
  A15 (HasWall C_m1_1)
  A16 (if (OccupiedByPig c_1_0) (not (CanPlaceWall c_1_0)))
  A17 (if (HasWall c_1_0) (not (CanPlaceWall c_1_0)))
  A18 (if (and (not (OccupiedByPig c_1_0)) (not (HasWall c_1_0))) (CanPlaceWall c_1_0))
 }
 :goal (CanPlaceWall c_1_0)
}