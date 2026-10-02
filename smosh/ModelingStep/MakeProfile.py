from smosh.ModelingStep.ModelingStep import ModelingStep
import os

class MakeProfile(ModelingStep):
	"""docstring for MakeProfile"""
		

	def __init__(self, pdb_file):

		self.pdb_file = pdb_file
		self.output_dir = os.path.dirname(pdb_file)
		self.__input_files__ = [pdb_file]
		self.__output_files__ = []
		super(MakeProfile, self).__init__()
		
	def __get_script__(self):


		return """from modeller import *
from modeller.scripts import complete_pdb
import os

os.chdir('""" + self.workdir + """')
# log.verbose()    # request verbose output
env = environ()
env.libs.topology.read(file='$(LIB)/top_heav.lib') # read topology
env.libs.parameters.read(file='$(LIB)/par.lib') # read parameters

# directories for input atom files
env.io.atom_files_directory = './:../atom_files'

# read model file
mdl = complete_pdb(env, '""" + os.path.basename(self.pdb_file) + """')

s = selection(mdl)
s.assess_dope(output='ENERGY_PROFILE NO_REPORT', file='""" + os.path.basename(self.pdb_file)[0:-4] + """.profile',
              normalize_profile=True, smoothing_window=15)
"""

	def pos_execution(self):
		# print self.workdir
		output_profile = os.path.basename(self.pdb_file)[0:-4] + ".profile"
		# print output_profile
		self.__output_files__.append(output_profile)
		super(MakeProfile, self).pos_execution()
