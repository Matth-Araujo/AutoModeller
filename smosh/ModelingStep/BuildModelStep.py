from smosh.ModelingStep.ModelingStep import ModelingStep
from ..ModelingTools.AlignFile import AlignFile
import os, glob

class BuildModelStep(ModelingStep):
	def __init__(self, alignment_file_path, template_path_pdb):
		self.output_dir = os.path.dirname(alignment_file_path)
		self.alignment_file_path = alignment_file_path
		self.alignfile = AlignFile(self.alignment_file_path)
		self.template_path_pdb = template_path_pdb
		self.__input_files__ = [self.alignment_file_path, template_path_pdb]
		self.__output_files__ = []
		super(BuildModelStep, self).__init__()

	def __get_script__(self):
		return """from modeller import *
from modeller.automodel import *
import os

os.chdir('""" + self.workdir + """')
env = environ()
env.io.hetatm = env.io.water = True
env.io.atom_files_directory = ['""" + self.workdir + """']
a = automodel(env, alnfile='""" + self.workdir + os.path.basename(self.alignment_file_path) + """',
              knowns='""" + self.alignfile.my_ali_file[self.__get_id_of_structure__()].name() + """', sequence='""" + self.alignfile.my_ali_file[self.__get_id_of_sequence__()].name() + """',
              assess_methods=(assess.DOPE,
                              assess.GA341))
a.starting_model = 1
a.ending_model = 5
a.make()
"""

	def pos_execution(self):
		for filename in glob.glob(self.workdir + "*.*.pdb"):
			self.__output_files__.append(os.path.basename(filename))

		super(BuildModelStep, self).pos_execution()

		
		
	def __get_id_of_sequence__(self):
		sequencesID = [0,1]
		for eachSequence in sequencesID:
			if self.alignfile.my_ali_file[eachSequence].type() == "sequence":
				return eachSequence

	def __get_id_of_structure__(self):
		sequencesID = [0,1]
		for eachSequence in sequencesID:
			if self.alignfile.my_ali_file[eachSequence].type() != "sequence":
				return eachSequence
