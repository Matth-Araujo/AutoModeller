import os
from smosh.ModelingStep.ModelingStep import ModelingStep


class AlignStep(ModelingStep):
	"""docstring for AlignStep"""
	def __init__(self, sequences_file_path):
		self.sequences_file_path = sequences_file_path
		self.output_dir = os.path.dirname(sequences_file_path)
		self.__input_files__ = [self.sequences_file_path]
		self.__output_files__ = ['ali.ali', 'ali.pap']
		super(AlignStep, self).__init__()
		
	def __get_script__(self):
		return """from modeller import *
env = environ()
env.io.hetatm = env.io.water = True
aln = alignment(env)
aln.append(file='""" + self.workdir + os.path.basename(self.sequences_file_path) + """', align_codes='all', alignment_format ="PIR")
aln.align2d()
aln.write(file='""" + self.workdir + """ali.ali', alignment_format='PIR')
aln.write(file='""" + self.workdir + """ali.pap', alignment_format='PAP')
"""



