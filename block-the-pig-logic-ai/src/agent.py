import subprocess

class LogicPigAgent:
    def run_spectra(self, file="spectra/block_the_pig.spc"):
        subprocess.run(["java", "-jar", "Spectra.jar", file])

    def run_prover(self):
        subprocess.run(["java", "-jar", "Shadow-Prover.jar",
                        "shadowprover/block_the_pig.sp"])
