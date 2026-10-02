import os, sys, shutil, tempfile
from smosh.ModelingStep.ModelingStep import ModelingStep
from smosh.ModelingStep.Modeller_Caller import Modeller_Caller

class FindTemplatesStep(ModelingStep):
	def __init__(self, sequence_file_path, input_sequence_type):
		self.input_sequence_type = input_sequence_type
		self.sequence_file_path = sequence_file_path
		self.output_dir = os.path.dirname(sequence_file_path)
		self.sequence_file_name = os.path.basename(self.sequence_file_path)
		self.__input_files__ = [sequence_file_path]
		self.__output_files__ = ['build_profilePIR.ali', 'build_profilePAP.ali', 'build_profile.prf']
		super(FindTemplatesStep, self).__init__()

	def __get_script__(self):
		return """\
from modeller import *

env = environ()

#-- Prepare the input files

#-- Read in the sequence database
sdb = sequence_db(env)
sdb.read(seq_database_file='""" + self.__installfolder__() + """/pdb/pdb_95.pir', seq_database_format='PIR', chains_list='ALL', minmax_db_seq_len=(30, 4000), clean_sequences=True)

#-- Write the sequence database in binary form
#sdb.write(seq_database_file='""" + self.__installfolder__() + """/pdb/pdb_95.bin', seq_database_format='BINARY', chains_list='ALL')

#-- Now, read in the binary database
sdb.read(seq_database_file='""" + self.__installfolder__() + """/pdb/pdb_95.bin', seq_database_format='BINARY', chains_list='ALL')

#-- Read in the target sequence/alignment
aln = alignment(env)
aln.append(file='""" + self.workdir + os.path.basename(self.sequence_file_path) + """', alignment_format='""" + self.input_sequence_type + """', align_codes='ALL')

#-- Convert the input sequence/alignment into
#   profile format
prf = aln.to_profile()

#-- Scan sequence database to pick up homologous sequences
prf.build(sdb, matrix_offset=-450, rr_file='${LIB}/blosum62.sim.mat', gap_penalties_1d=(-500, -50), n_prof_iterations=1, check_profile=False, max_aln_evalue=0.01)

#-- Write out the profile in text format
prf.write(file='""" + self.workdir + '/build_profile.prf'"""', profile_format='TEXT')

#-- Convert the profile back to alignment format
aln = prf.to_alignment()

#-- Write out the alignment fileo
aln.write(file='""" + self.workdir + '/build_profilePIR.ali' + """', alignment_format='PIR')
aln.write(file='""" + self.workdir + '/build_profilePAP.ali' + """', alignment_format='PAP')
"""	
