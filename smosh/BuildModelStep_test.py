import unittest
from smosh.ModelingStep.BuildModelStep import BuildModelStep
from should_dsl import should, should_not
import os

smosh_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

class ModelingStepTests(unittest.TestCase):
	def setUp(self):
		self.buildModelStepExample = BuildModelStep(smosh_path + 'files/TvLDH-1bdmA.ali',smosh_path + 'files/1bdm.pdb')
		try:
			filenames = ["TvLDH.B99990001.pdb", "TvLDH.B99990002.pdb", "TvLDH.B99990003.pdb", "TvLDH.B99990004.pdb"]
			for eachFile in filenames:
				os.remove(smosh_path + 'files/' + eachFile)
			# os.remove('files/ali.ali')
		except Exception as e:
			pass

	def test_buildModelStepExample_has_input_files(self):
		input_files  = [smosh_path + 'files/TvLDH-1bdmA.ali',smosh_path + 'files/1bdm.pdb']
		flag = True
		for eachFile in input_files:
			flag = flag and os.path.exists(eachFile)
		flag |should| equal_to(True)

	def test_buildModelStepExample_output_folder_is_equal_to_father_directory_of_input_file(self):
		output_dir = self.buildModelStepExample.output_dir
		sequence_input_file = self.buildModelStepExample.alignment_file_path
		output_dir |should| equal_to(os.path.dirname(sequence_input_file))

	def test_get_script_output_is_a_text(self):
		self.buildModelStepExample.__get_script__() |should| be_kind_of(str)

	def test_if_workdir_contains_the_input_file(self):
		workdir = self.buildModelStepExample.workdir
		basename_of_input_file = os.path.basename(self.buildModelStepExample.alignment_file_path)
		input_file_in_workdir = workdir + basename_of_input_file
		os.path.exists(input_file_in_workdir) |should| equal_to(True)

	def test_if_workdir_contain_script(self):
		self.buildModelStepExample.make_script()
		workdir = self.buildModelStepExample.workdir
		# print workdir
		script_path = workdir + "step.py"
		os.path.exists(script_path) |should| equal_to(True)

# 	def test_if_script_contain_the_right_content(self):

# 		workdir = self.buildModelStepExample.workdir
# 		self.buildModelStepExample.make_script()
# 		alignment_file_path = self.buildModelStepExample.alignment_file_path
# 		script_path = self.buildModelStepExample.workdir + "step.py"
# 		script_file = file(script_path, "r")
# 		content = script_file.read()
# 		content |should| equal_to("""from modeller import *
# from modeller.automodel import *
# import os

# os.chdir('""" + workdir + """')
# env = environ()
# env.io.atom_files_directory = ['""" + workdir + """']
# a = automodel(env, alnfile='""" + workdir + os.path.basename(alignment_file_path) + """',
#               knowns='1bdmA', sequence='TvLDH',
#               assess_methods=(assess.DOPE,
#                               assess.GA341))
# a.starting_model = 1
# a.ending_model = 5
# a.make()"""
# )

	def test_buildModelStepExample_output_file_exists_in_workdir(self):
		self.buildModelStepExample.execute()
		out_files = [self.buildModelStepExample.workdir + "TvLDH.B99990001.pdb", self.buildModelStepExample.workdir + "TvLDH.B99990002.pdb",
		 self.buildModelStepExample.workdir + "TvLDH.B99990003.pdb",
		 self.buildModelStepExample.workdir + "TvLDH.B99990004.pdb" ]
		flag = True
		for eachFile in out_files:
			flag = flag and os.path.exists(eachFile)
		flag |should| equal_to(True)


	def test_if_output_files_are_in_father_folder(self):
		self.buildModelStepExample.execute()
		output_dir = self.buildModelStepExample.output_dir
		filenames = ["TvLDH.B99990001.pdb", "TvLDH.B99990002.pdb", "TvLDH.B99990003.pdb", "TvLDH.B99990004.pdb", "TvLDH.B99990005.pdb"]
		flag = True
		for eachFile in filenames:
			flag = flag and os.path.exists(output_dir + os.sep + eachFile)
		flag |should| equal_to(True)

if __name__ == '__main__':
	unittest.main()

