
{:name "Connectivity Check"
 :description "Verifying move 2,5 is valid relative to 3,6"
 :assumptions {
   (Adjacent C_3_6 C_4_6)
   (Adjacent C_3_6 C_3_5)
   (Adjacent C_3_6 C_2_5)
   (Adjacent C_3_6 C_2_6)
   (Adjacent C_3_6 C_2_7)
   (Adjacent C_3_6 C_3_7)
   (OccupiedByPig C_3_6)
   (Target C_2_5)
 }
 :goal (Adjacent C_3_6 C_2_5)
}
