import os
from smosh.ModelingStep.ModelingStep import ModelingStep


class GetSequenceFromPDBStep(ModelingStep):
	"""docstring for GetSequenceFromPDBStep"""
	def __init__(self, pdb_file_path, first_chain, last_chain):
		self.pdb_file_path = pdb_file_path
		self.first_chain = first_chain
		self.last_chain = last_chain
		self.str_name = os.path.basename(self.pdb_file_path)[:-4]
		self.output_dir = os.path.dirname(pdb_file_path)
		self.__input_files__ = [self.pdb_file_path]
		self.__output_files__ = [self.str_name + '.pir']
		super(GetSequenceFromPDBStep, self).__init__()
		
	def __get_script__(self):
		return """\
from modeller import *
import os
os.chdir('""" + self.workdir + """')
env = environ()
env.io.hetatm = env.io.water = True
env.io.atom_files_directory = './:../atom_files'

code = '""" + self.str_name + """'   #   estrutura a ser lida#
mdl = model(env, file=code, model_segment=('FIRST:""" + self.first_chain +"""','LAST:""" + self.last_chain + """'))

aln = alignment(env)
aln.append_model(mdl, align_codes=code)
aln.write(file='""" + self.workdir + self.str_name + """.pir', alignment_format = 'PIR')
"""




