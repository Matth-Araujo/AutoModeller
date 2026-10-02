import unittest
from smosh.ModelingStep.EvaluateEnergy import EvaluateEnergy
from should_dsl import should, should_not
import os

smosh_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

class ModelingStepTests(unittest.TestCase):
	def setUp(self):
		self.evaluateEnergyExample = EvaluateEnergy(smosh_path + 'files/TvLDH-1bdmA.ali',smosh_path +  'files/1bdm.profile', smosh_path+ 'files/TvLDH.B99990005.profile')
		try:
			filenames = ["dope_profile_loop.png"]
			for eachFile in filenames:
				os.remove('files/' + eachFile)
			# os.remove('files/ali.ali')
		except Exception as e:
			pass

	def test_evaluateEnergyExample_has_input_files(self):
		input_files  = [smosh_path + 'files/TvLDH-1bdmA.ali',smosh_path + 'files/1bdm.profile',smosh_path + 'files/1bdm.pdb']
		flag = True
		for eachFile in input_files:
			flag = flag and os.path.exists(eachFile)
		flag |should| equal_to(True)

	def test_evaluateEnergyExample_output_folder_is_equal_to_father_directory_of_input_file(self):
		output_dir = self.evaluateEnergyExample.output_dir
		sequence_input_file = self.evaluateEnergyExample.alignment_file
		output_dir |should| equal_to(os.path.dirname(sequence_input_file))

	def test_get_script_output_is_a_text(self):
		self.evaluateEnergyExample.__get_script__() |should| be_kind_of(str)

	def test_if_workdir_contains_the_input_file(self):
		workdir = self.evaluateEnergyExample.workdir
		basename_of_input_file = os.path.basename(self.evaluateEnergyExample.alignment_file)
		input_file_in_workdir = workdir + basename_of_input_file
		os.path.exists(input_file_in_workdir) |should| equal_to(True)

	def test_if_workdir_contain_script(self):
		self.evaluateEnergyExample.make_script()
		workdir = self.evaluateEnergyExample.workdir
		# print workdir
		script_path = workdir + "step.py"
		os.path.exists(script_path) |should| equal_to(True)

# 	def test_if_script_contain_the_right_content(self):

# 		workdir = self.evaluateEnergyExample.workdir
# 		self.evaluateEnergyExample.make_script()
# 		alignment_file = self.evaluateEnergyExample.alignment_file
# 		profile_pdb = self.evaluateEnergyExample.profile_pdb
# 		profile_template = self.evaluateEnergyExample.profile_template
# 		script_path = self.evaluateEnergyExample.workdir + "step.py"
# 		script_file = file(script_path, "r")
# 		content = script_file.read()
# 		content |should| equal_to("""import matplotlib.pyplot as plt
# import numpy as np
# import modeller
# import os


# os.chdir('""" + workdir + """')
# def get_profile(profile_file, seq):
#     '''Read `profile_file` into a Python array, and add gaps corresponding to
#        the alignment sequence `seq`.'''
#     # Read all non-comment and non-blank lines from the file:
#     f = file(profile_file)
#     vals = []
#     for line in f:
#         if not line.startswith('#') and len(line) > 10:
#             spl = line.split()
#             vals.append(float(spl[-1]))
#     # Insert gaps into the profile corresponding to those in seq:
#     for n, res in enumerate(seq.residues):
#         for gap in range(res.get_leading_gaps()):
#             vals.insert(n, None)
#     # Add a gap at position '0', so that we effectively count from 1:
#     vals.insert(0, None)
#     return vals

# e = modeller.environ()
# a = modeller.alignment(e, file='""" + workdir + os.path.basename(alignment_file) + """')

# try:
# 	template = get_profile('""" + workdir + profile_template + """', a['""" + os.path.basename(profile_template)[0:-8] + """A'])
# 	model = get_profile('""" + workdir + profile_pdb + """', a['""" + os.path.basename(profile_pdb)[0:-18] + """'])

# except Exception, e:
# 	print e
# 	template = get_profile('""" + profile_template + """', a['""" + os.path.basename(profile_template)[0:-8] + """'])
# 	model = get_profile('""" + profile_pdb + """', a['""" + os.path.basename(profile_pdb)[0:-18] + """'])

# # Plot the template and model profiles in the same plot for comparison:
# fig = plt.figure(1)
# ax = fig.add_subplot(111)
# plt.xlabel('Alignment position')
# plt.ylabel('DOPE per-residue score')
# ax.plot(model, color='red', linewidth=2, label='Model')
# ax.plot(template, color='green', linewidth=2, label='Template')
# handles, labels = ax.get_legend_handles_labels()
# lgd = ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5,-0.1))
# ax.grid('on')
# fig.savefig('dope_profile_loop', bbox_extra_artists=(lgd,), bbox_inches='tight')
# """
# )

	def test_evaluateEnergyExample_output_file_exists_in_workdir(self):
		self.evaluateEnergyExample.execute()
		out_files = [self.evaluateEnergyExample.workdir + "dope_profile_loop.png"]
		flag = True
		for eachFile in out_files:
			flag = flag and os.path.exists(eachFile)
		flag |should| equal_to(True)


	def test_if_output_files_are_in_father_folder(self):
		self.evaluateEnergyExample.execute()
		output_dir = self.evaluateEnergyExample.output_dir
		filenames = ["dope_profile_loop.png"]
		flag = True
		for eachFile in filenames:
			flag = flag and os.path.exists(output_dir + os.sep + eachFile)
		flag |should| equal_to(True)

if __name__ == '__main__':
	unittest.main()

