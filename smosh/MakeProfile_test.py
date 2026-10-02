import unittest
from smosh.ModelingStep.MakeProfile import MakeProfile
from should_dsl import should, should_not
import os

smosh_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

class ModelingStepTests(unittest.TestCase):
	def setUp(self):
		self.makeProfileExample = MakeProfile(smosh_path + 'files/TvLDH.B99990005.pdb')
		# try:
		# 	os.remove('files/ali.pap')
		# 	os.remove('files/ali.ali')
		# except Exception, e:
		# 	pass

	def test_findTemplateExample_has_a_input_file(self):
		pdb_file = self.makeProfileExample.pdb_file
		os.path.exists(pdb_file) |should| equal_to(True)

	def test_makeProfileExample_output_folder_is_equal_to_father_directory_of_input_file(self):
		output_dir = self.makeProfileExample.output_dir
		pdb_file = self.makeProfileExample.pdb_file
		output_dir |should| equal_to(os.path.dirname(pdb_file))

	def test_get_script_output_is_a_text(self):
		self.makeProfileExample.__get_script__() |should| be_kind_of(str)

	def test_if_workdir_contains_the_input_file(self):
		workdir = self.makeProfileExample.workdir
		basename_of_input_file = os.path.basename(self.makeProfileExample.pdb_file)
		input_file_in_workdir = workdir + basename_of_input_file
		os.path.exists(input_file_in_workdir) |should| equal_to(True)

	def test_if_workdir_contain_script(self):
		self.makeProfileExample.make_script()
		workdir = self.makeProfileExample.workdir
		# print workdir
		script_path = workdir + "step.py"
		os.path.exists(script_path) |should| equal_to(True)

# 	def test_if_script_contain_the_right_content(self):

# 		workdir = self.makeProfileExample.workdir
# 		self.makeProfileExample.make_script()
# 		pdb_file = self.makeProfileExample.pdb_file
# 		script_path = self.makeProfileExample.workdir + "step.py"
# 		script_file = file(script_path, "r")
# 		content = script_file.read()
# 		content |should| equal_to("""from modeller import *
# from modeller.scripts import complete_pdb
# import os

# os.chdir('""" + workdir + """')
# log.verbose()    # request verbose output
# env = environ()
# env.libs.topology.read(file='$(LIB)/top_heav.lib') # read topology
# env.libs.parameters.read(file='$(LIB)/par.lib') # read parameters

# # directories for input atom files
# env.io.atom_files_directory = './:../atom_files'

# # read model file
# mdl = complete_pdb(env, '""" + os.path.basename(pdb_file) + """')

# s = selection(mdl)
# s.assess_dope(output='ENERGY_PROFILE NO_REPORT', file='""" + os.path.basename(pdb_file)[0:-4] + """.profile',
#               normalize_profile=True, smoothing_window=15)
# """
# )

	def test_makeProfileExample_output_file_exists_in_workdir(self):
		self.makeProfileExample.execute()
		workdir = self.makeProfileExample.workdir
		out_files = workdir + "TvLDH.B99990005.profile"		
		os.path.exists(out_files) |should| equal_to(True)

if __name__ == '__main__':
	unittest.main()

