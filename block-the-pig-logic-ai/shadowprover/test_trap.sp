;; Test file for Block the Pig logic

include "block_the_pig.sp".

;; Scenario: Pig is at C_0_0 (Center)
;; Walls are at all 6 neighbors: C_1_0, C_1_m1, C_0_m1, C_m1_0, C_m1_1, C_0_1

assumption OccupiedByPig(C_0_0).

assumption HasWall(C_1_0).
assumption HasWall(C_1_m1).
assumption HasWall(C_0_m1).
assumption HasWall(C_m1_0).
assumption HasWall(C_m1_1).
assumption HasWall(C_0_1).

;; Goal: Prove Trapped
goal Trapped.
