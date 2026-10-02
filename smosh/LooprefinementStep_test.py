import unittest
from smosh.ModelingStep.LoopRefinementStep import LoopRefinementStep
from should_dsl import should, should_not
import os

smosh_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

class ModelingStepTests(unittest.TestCase):
	def setUp(self):
		self.loopRefinementStepExample = LoopRefinementStep(smosh_path + 'files/TvLDH.B99990005.pdb', "1:A", "10:A")
		try:
			filenames = ["TvLDH.B99990001.pdb", "TvLDH.B99990002.pdb", "TvLDH.B99990003.pdb", "TvLDH.B99990004.pdb"]
			for eachFile in filenames:
				os.remove(smosh_path + 'files/' + eachFile)
			# os.remove('files/ali.ali')
		except Exception as e:
			pass

	def test_loopRefinementStepExample_has_input_files(self):
			input_file  = smosh_path + 'files/TvLDH.B99990005.pdb'
			os.path.exists(input_file) |should| equal_to(True)


	def test_loopRefinementStepExample_output_folder_is_equal_to_father_directory_of_input_file(self):
		output_dir = self.loopRefinementStepExample.output_dir
		initial_model_file_path = self.loopRefinementStepExample.initial_model_file_path
		output_dir |should| equal_to(os.path.dirname(initial_model_file_path))

	def test_get_script_output_is_a_text(self):
		self.loopRefinementStepExample.__get_script__() |should| be_kind_of(str)

	def test_if_workdir_contains_the_input_file(self):
		workdir = self.loopRefinementStepExample.workdir
		basename_of_input_file = os.path.basename(self.loopRefinementStepExample.initial_model_file_path)
		input_file_in_workdir = workdir + basename_of_input_file
		os.path.exists(input_file_in_workdir) |should| equal_to(True)

	def test_if_workdir_contain_script(self):
		self.loopRefinementStepExample.make_script()
		workdir = self.loopRefinementStepExample.workdir
		# print workdir
		script_path = workdir + "step.py"
		os.path.exists(script_path) |should| equal_to(True)

# 	def test_if_script_contain_the_right_content(self):

# 		workdir = self.loopRefinementStepExample.workdir
# 		self.loopRefinementStepExample.make_script()
# 		initial_model_file_path = self.loopRefinementStepExample.initial_model_file_path
# 		script_path = self.loopRefinementStepExample.workdir + "step.py"
# 		script_file = file(script_path, "r")
# 		content = script_file.read()
# 		content |should| equal_to("""from modeller import *
# from modeller.automodel import *
# import os

# os.chdir('""" + workdir + """')
# env = environ()
# env.io.atom_files_directory = ['""" + workdir + """']
# a = automodel(env, alnfile='""" + workdir + os.path.basename(initial_model_file_path) + """',
#               knowns='1bdmA', sequence='TvLDH',
#               assess_methods=(assess.DOPE,
#                               assess.GA341))
# a.starting_model = 1
# a.ending_model = 5
# a.make()"""
# )

	def test_loopRefinementStepExample_output_file_exists_in_workdir(self):
		self.loopRefinementStepExample.execute()
		out_files = [self.loopRefinementStepExample.workdir + "TvLDH.BL00050001.pdb", self.loopRefinementStepExample.workdir + "TvLDH.BL00040001.pdb",
		 self.loopRefinementStepExample.workdir + "TvLDH.BL00030001.pdb",
		 self.loopRefinementStepExample.workdir + "TvLDH.BL00020001.pdb" ]
		flag = True
		for eachFile in out_files:
			flag = flag and os.path.exists(eachFile)
		flag |should| equal_to(True)


	def test_if_output_files_are_in_father_folder(self):
		self.loopRefinementStepExample.execute()
		output_dir = self.loopRefinementStepExample.output_dir
		filenames = [ "TvLDH.BL00050001.pdb",  "TvLDH.BL00040001.pdb",
		  "TvLDH.BL00030001.pdb",
		  "TvLDH.BL00020001.pdb" ]
		flag = True
		for eachFile in filenames:
			flag = flag and os.path.exists(output_dir + os.sep + eachFile)
		flag |should| equal_to(True)

if __name__ == '__main__':
	unittest.main()
