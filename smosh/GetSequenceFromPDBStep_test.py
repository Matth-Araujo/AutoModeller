import unittest
from smosh.ModelingStep.GetSequenceFromPDBStep import GetSequenceFromPDBStep
from should_dsl import should, should_not
import os

smosh_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

class ModelingStepTests(unittest.TestCase):
	def setUp(self):
		self.alignStepExample = GetSequenceFromPDBStep(smosh_path + 'files/1bdm.pdb', 'A', 'A')
		try:
			os.remove(smosh_path + 'files/1bdm.pir')
		except Exception as e:
			pass

	def test_alignStepExample_has_a_input_file(self):
		sequence_input_file = self.alignStepExample.pdb_file_path
		os.path.exists(sequence_input_file) |should| equal_to(True)

	def test_alignStepExample_has_the_corret_str_name(self):
		self.alignStepExample.str_name |should| equal_to('1bdm')

	def test_alignStepExample_output_folder_is_equal_to_father_directory_of_input_file(self):
		output_dir = self.alignStepExample.output_dir
		sequence_input_file = self.alignStepExample.pdb_file_path
		output_dir |should| equal_to(os.path.dirname(sequence_input_file))

	def test_get_script_output_is_a_text(self):
		self.alignStepExample.__get_script__() |should| be_kind_of(str)

	def test_if_workdir_contains_the_input_file(self):
		workdir = self.alignStepExample.workdir
		basename_of_input_file = os.path.basename(self.alignStepExample.pdb_file_path)
		input_file_in_workdir = workdir + basename_of_input_file
		os.path.exists(input_file_in_workdir) |should| equal_to(True)

	def test_if_workdir_contain_script(self):
		self.alignStepExample.make_script()
		workdir = self.alignStepExample.workdir
		script_path = workdir + "step.py"
		os.path.exists(script_path) |should| equal_to(True)

# 	def test_if_script_contain_the_right_content(self):

# 		workdir = self.alignStepExample.workdir
# 		self.alignStepExample.make_script()
# 		script_path = self.alignStepExample.workdir + "step.py"
# 		script_file = file(script_path, "r")
# 		content = script_file.read()
# 		content |should| equal_to("""\
# from modeller import *

# env = environ()
# aln = alignment(env)
# aln.append(file='""" + workdir + os.path.basename(self.alignStepExample.sequences_file_path) + """', align_codes='all', alignment_format ="FASTA")
# aln.align2d()
# aln.write(file='""" + workdir + """ali.ali', alignment_format='PIR')
# aln.write(file='""" + workdir + """ali.pap', alignment_format='PAP')""")

	def test_alignStepExample_output_file_exists_in_workdir(self):
		self.alignStepExample.execute()
		aliali = self.alignStepExample.workdir + self.alignStepExample.__output_files__[0]
		os.path.exists(aliali) |should| equal_to(True)


	def test_if_output_files_are_in_father_folder(self):
		self.alignStepExample.execute()
		output_dir = self.alignStepExample.output_dir
		output_file1 = output_dir + os.sep + self.alignStepExample.__output_files__[0]
		os.path.exists(output_file1) |should| equal_to(True)

if __name__ == '__main__':
	unittest.main()

