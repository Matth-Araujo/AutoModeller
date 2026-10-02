import os
from Modeller_Caller import modeller_caller
class Loop_Refinement(object):
    """docstring for Loop_Refinement"""
    def __init__(self, initial_model, start_residue, end_residue):
            self.initial_model = initial_model
            self.start_residue = start_residue
            self.end_residue = end_residue
            self.myscript = ""
    
    def create_script_in_folder(self,path):
        script = """\
# Loop refinement of an existing model
from modeller import *
from modeller.automodel import *
import os

log.verbose()
env = environ()
os.chdir('""" + path + """')

# directories for input atom files
env.io.atom_files_directory = './:../atom_files'

# Create a new class based on 'loopmodel' so that we can redefine
# select_loop_atoms (necessary)
class MyLoop(loopmodel):
    # This routine picks the residues to be refined by loop modeling
    def select_loop_atoms(self):
        # 10 residue insertion 
        return selection(self.residue_range('""" + self.start_residue + """', ' """ + self.end_residue + """'))

m = MyLoop(env,
           inimodel='""" + self.initial_model + """', # initial model of the target
           sequence='seq.ali')          # code of the target

m.loop.starting_model= 1           # index of the first loop model 
m.loop.ending_model  = 5          # index of the last loop model
m.loop.md_level = refine.very_fast # loop refinement method; this yields
                                   # models quickly but of low quality;
                                   # use refine.slow for better models

m.make()
""" 
        script_path = path + os.sep + "loop.py"
        loop_script = file(script_path, "w")        
        loop_script.write(script)
        loop_script.close()
        self.myscript = script_path

    def __folder_of_evaluate__(self):
        pass

    def get_model(self):
        processo = modeller_caller()
        processo.run(self.myscript)
        
    def get_results(self):
        folder = os.path.dirname(self.myscript)
        mof = 0
        filemof = ""
        for files in os.listdir(folder):
            if (files.startswith('seq.ali.BL')):
                    arqr = file(folder + '/' + files, 'r')
                    arqr.readline()
                    linha = arqr.readline()
                    if (mof == 0) or (linha.partition(':      ')[2] < mof):
                            mof = linha.partition(':      ')[2]
                            filemof = folder + '/' + files
                            arqr.close()
        # if not (os.path.exists(folder + '/../loop')):
        #         os.mkdir(folder + '/../loop')
        # os.popen('cp '+ filemof +  ' ' + folder + '/../loop/')
        return filemof