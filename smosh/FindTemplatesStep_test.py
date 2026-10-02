import unittest
from smosh.ModelingStep.FindTemplatesStep import FindTemplatesStep
from should_dsl import should, should_not
import os

smosh_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

class ModelingStepTests(unittest.TestCase):
	def setUp(self):
		self.findTemplateExample = FindTemplatesStep(smosh_path + 'files/TvLDH.pir', "FASTA")
		try:
			os.remove(smosh_path + 'files/build_profilePAP.ali')
			os.remove(smosh_path + 'files/build_profilePIR.ali')
		except Exception as e:
			pass

		# self.findTemplateExample.execute()

	def test_findTemplateExample_has_a_input_file(self):
		sequence_input_file = self.findTemplateExample.sequence_file_path
		os.path.exists(sequence_input_file) |should| equal_to(True)

	def test_findTemplateExample_output_folder_is_equal_to_father_directory_of_input_file(self):
		output_dir = self.findTemplateExample.output_dir
		sequence_input_file = self.findTemplateExample.sequence_file_path
		output_dir |should| equal_to(os.path.dirname(sequence_input_file))

	def test_get_script_output_is_a_text(self):
		self.findTemplateExample.__get_script__() |should| be_kind_of(str)

	def test_if_workdir_contains_the_input_file(self):
		workdir = self.findTemplateExample.workdir
		basename_of_input_file = os.path.basename(self.findTemplateExample.sequence_file_path)
		input_file_in_workdir = workdir + basename_of_input_file
		os.path.exists(input_file_in_workdir) |should| equal_to(True)

	def test_if_workdir_contain_script(self):
		self.findTemplateExample.make_script()
		workdir = self.findTemplateExample.workdir
		script_path = workdir + "step.py"
		os.path.exists(script_path) |should| equal_to(True)

# 	def test_if_script_contain_the_right_content(self):

# 		workdir = self.findTemplateExample.workdir
# 		self.findTemplateExample.make_script()
# 		script_path = self.findTemplateExample.workdir + "step.py"
# 		script_file = file(script_path, "r")
# 		content = script_file.read()
# 		content |should| equal_to("""\
# from modeller import *


# env = environ()

# #-- Prepare the input files

# #-- Read in the sequence database
# sdb = sequence_db(env)
# sdb.read(seq_database_file='""" + self.findTemplateExample.__installfolder__() + """/pdb/pdb_95.pir', seq_database_format='PIR', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True)

# #-- Write the sequence database in binary form
# #sdb.write(seq_database_file='""" + self.findTemplateExample.__installfolder__() + """/pdb/pdb_95.bin', seq_database_format='BINARY', chains_list='ALL')

# #-- Now, read in the binary database
# sdb.read(seq_database_file='""" + self.findTemplateExample.__installfolder__() + """/pdb/pdb_95.bin', seq_database_format='BINARY', chains_list='ALL')

# #-- Read in the target sequence/alignment
# aln = alignment(env)
# aln.append(file='""" + self.findTemplateExample.workdir + os.path.basename(self.findTemplateExample.sequence_file_path) + """', alignment_format='PIR', align_codes='ALL')

# #-- Convert the input sequence/alignment into
# #   profile format
# prf = aln.to_profile()

# #-- Scan sequence database to pick up homologous sequences
# prf.build(sdb, matrix_offset=-450, rr_file='${LIB}/blosum62.sim.mat', gap_penalties_1d=(-500, -50), n_prof_iterations=1, check_profile=False, max_aln_evalue=0.01)

# #-- Write out the profile in text format
# prf.write(file='""" + self.findTemplateExample.workdir + '/build_profile.prf'"""', profile_format='TEXT')

# #-- Convert the profile back to alignment format
# aln = prf.to_alignment()

# #-- Write out the alignment fileo
# aln.write(file='""" + self.findTemplateExample.workdir + '/build_profilePIR.ali' + """', alignment_format='PIR')
# aln.write(file='""" + self.findTemplateExample.workdir + '/build_profilePAP.ali' + """', alignment_format='PAP')
# """)

	def test_findTemplateExample_output_file_exists_in_workdir(self):
		self.findTemplateExample.execute()
		build_profilePIR = self.findTemplateExample.workdir + self.findTemplateExample.__output_files__[0]
		build_profilePAP = self.findTemplateExample.workdir + self.findTemplateExample.__output_files__[1]
		build_profilePRF = self.findTemplateExample.workdir + self.findTemplateExample.__output_files__[2]
		os.path.exists(build_profilePIR) and os.path.exists(build_profilePAP) and os.path.exists(build_profilePRF) |should| equal_to(True)



	def test_if_output_files_are_in_father_folder(self):
		self.findTemplateExample.execute()
		output_dir = self.findTemplateExample.output_dir
		output_file1 = output_dir + os.sep + self.findTemplateExample.__output_files__[0]
		output_file2 = output_dir + os.sep + self.findTemplateExample.__output_files__[1]
		output_file3 = output_dir + os.sep + self.findTemplateExample.__output_files__[2]
		os.path.exists(output_file1) and os.path.exists(output_file2)  and os.path.exists(output_file3) |should| equal_to(True)

if __name__ == '__main__':
	unittest.main()

