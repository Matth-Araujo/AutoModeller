from smosh.ModelingStep.ModelingStep import ModelingStep
import os, glob

class LoopRefinementStep(ModelingStep):
	def __init__(self, initial_model_file_path, start_residue, end_residue):
		self.output_dir = os.path.dirname(initial_model_file_path)
		self.initial_model_file_path = initial_model_file_path
		self.start_residue = str(start_residue)
		self.end_residue = str(end_residue)
		self.__input_files__ = [self.initial_model_file_path]
		self.__output_files__ = []
		super(LoopRefinementStep, self).__init__()

	def __get_script__(self):
		return """# Loop refinement of an existing model
from modeller import *
from modeller.automodel import *
import os

log.verbose()
env = environ()
os.chdir('""" + self.workdir + """')

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
           inimodel='""" + os.path.basename(self.initial_model_file_path)[:-4] + """', # initial model of the target
           sequence='""" + os.path.basename(self.initial_model_file_path)[:-4].split(".")[0] + """')          # code of the target

m.loop.starting_model= 1           # index of the first loop model 
m.loop.ending_model  = 5          # index of the last loop model
m.loop.md_level = refine.very_fast # loop refinement method; this yields
                                   # models quickly but of low quality;
                                   # use refine.slow for better models

m.make()
"""

	def pos_execution(self):
		for filename in glob.glob(self.workdir + "*.BL*.pdb"):
			self.__output_files__.append(os.path.basename(filename))

		super(LoopRefinementStep, self).pos_execution()

		
		
