
{:name "Connectivity Check"
 :description "Verifying move 3,5 is valid relative to 2,5"
 :assumptions {
   (Adjacent C_2_5 C_3_5)
   (Adjacent C_2_5 C_3_4)
   (Adjacent C_2_5 C_2_4)
   (Adjacent C_2_5 C_1_5)
   (Adjacent C_2_5 C_2_6)
   (Adjacent C_2_5 C_3_6)
   (OccupiedByPig C_2_5)
   (Target C_3_5)
 }
 :goal (Adjacent C_2_5 C_3_5)
}
