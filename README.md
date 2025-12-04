# block-the-pig-solver

How to Run
Requirements

Java 23 (or Java 17+)

The snark/ directory must be inside block-the-pig-logic-ai/

1. Run ShadowProver (Check Logic)
cd block-the-pig-logic-ai
java -cp tools/Shadow-Prover.jar org.rairlab.shadow.prover.Runner shadowprover/test_trap.clj

2. Run Spectra (Generate Plan)
cd block-the-pig-logic-ai
java -jar tools/Spectra.jar spectra/block_the_pig.clj

3. Run Game (Python)
cd block-the-pig-logic-ai
python src/game.py
