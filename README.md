# block-the-pig-solver

# How to Run

## Prerequisites
- **Java (Verified on Java 23)**
- **Python 3** with Flask  
  Install Flask:
  ```bash
  pip install flask
  ```
- The `snark/` directory must be inside `block-the-pig-logic-ai/`  
  *(This is already included.)*

---

## 1. Run the Web Game (Recommended)

```bash
cd block-the-pig-logic-ai
python src/app.py
```

Then open your browser at:

**http://127.0.0.1:5000**

This runs the interactive web version of Block the Pig.

---

## 2. Run ShadowProver (Logic Verification)

Verify logic on a **small, tractable grid** (Radius 1):

```bash
cd block-the-pig-logic-ai
java -cp tools/Shadow-Prover.jar org.rairlab.shadow.prover.Runner shadowprover/test_trap_small.clj
```

---

## 3. Run Spectra (Planning)

Generate a wall-placement plan using Spectra:

```bash
cd block-the-pig-logic-ai
java -jar tools/Spectra.jar spectra/block_the_pig.clj
```

---
