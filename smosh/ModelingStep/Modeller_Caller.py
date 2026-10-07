import os
import subprocess
import sys


def get_modeller_env():
    """Retorna ambiente com todos os caminhos necessários para o Modeller 10.7 no Python 3."""
    env = os.environ.copy()
    env.setdefault("KEY_MODELLER", "MODELIRANJE")

    mod_install = os.environ.get("MODINSTALL10v7", "/usr/lib/modeller10.7")
    mod_lib = os.path.join(mod_install, "lib", "x86_64-intel8")
    mod_py33 = os.path.join(mod_lib, "python3.3")
    mod_modlib = os.path.join(mod_install, "modlib")

    # Para Python 3, precisamos do _modeller.so compilado para Python 3 (em python3.3/)
    # e do pacote modeller (em modlib/). O diretório lib/x86_64-intel8 contém o _modeller.so
    # legado do Python 2 (PyClass_Type) e NÃO deve ser incluído no PYTHONPATH.
    curr_pp = env.get("PYTHONPATH", "")
    pp_parts = [p for p in [mod_py33, mod_modlib] if os.path.isdir(p)]
    if curr_pp:
        filtered_old = [p for p in curr_pp.split(":") if p and p != mod_lib]
        pp_parts.extend(filtered_old)
    env["PYTHONPATH"] = ":".join(pp_parts)

    # LD_LIBRARY_PATH deve apontar para as bibliotecas C compartilhadas do Modeller (libmodeller.so, etc.)
    curr_ld = env.get("LD_LIBRARY_PATH", "")
    ld_parts = [p for p in [mod_lib] if os.path.isdir(p)]
    if curr_ld:
        ld_parts.extend([p for p in curr_ld.split(":") if p and p != mod_lib])
    env["LD_LIBRARY_PATH"] = ":".join(ld_parts)

    return env


class Modeller_Caller:
    def __init__(self):
        os.environ.setdefault("KEY_MODELLER", "MODELIRANJE")
        env_exe = os.environ.get("SMOSH_MODELLER_PYTHON")
        if env_exe and "mod10." not in os.path.basename(env_exe) and os.path.exists(env_exe):
            self.modeller_executable = env_exe
        else:
            self.modeller_executable = sys.executable
        self.process = None

    def run(self, script):
        env = get_modeller_env()
        process = subprocess.Popen([self.modeller_executable, script], env=env)
        return process.wait()
