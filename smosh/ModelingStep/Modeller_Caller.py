import os
import subprocess

import sys

class Modeller_Caller:
    def __init__(self):
        env_exe = os.environ.get("SMOSH_MODELLER_PYTHON")
        if env_exe and "mod10." not in os.path.basename(env_exe) and os.path.exists(env_exe):
            self.modeller_executable = env_exe
        else:
            self.modeller_executable = sys.executable
        self.process = None

    def run(self, script):
        process = subprocess.Popen([self.modeller_executable, script])
        return process.wait()
