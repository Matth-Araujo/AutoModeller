from smosh.ModelingStep.ModelingStep import ModelingStep
import os
class EvaluateEnergy(ModelingStep):
	"""docstring for EvaluateEnergy"""
	def __init__(self, alignment_file, profile_template, profile_model):

		self.alignment_file = alignment_file
		self.profile_template = os.path.basename(profile_template)
		self.profile_model = os.path.basename(profile_model)
		self.output_dir = os.path.dirname(alignment_file)
		self.__input_files__ = [alignment_file, profile_template, profile_model]
		self.__output_files__ = ['dope_profile_loop.png']
		super(EvaluateEnergy, self).__init__()
		
	def __get_script__(self):
		return """import matplotlib.pyplot as plt
import numpy as np
import modeller
import os

import sys


os.chdir('""" + self.workdir + """')
def get_profile(profile_file, seq):
    '''Read `profile_file` into a Python array, and add gaps corresponding to
       the alignment sequence `seq`.'''
    # Read all non-comment and non-blank lines from the file:
    f = open(profile_file)
    vals = []
    for line in f:
        if not line.startswith('#') and len(line) > 10:
            spl = line.split()
            vals.append(float(spl[-1]))
    # Insert gaps into the profile corresponding to those in seq:
    for n, res in enumerate(seq.residues):
        for gap in range(res.get_leading_gaps()):
            vals.insert(n, None)
    # Add a gap at position '0', so that we effectively count from 1:
    vals.insert(0, None)
    return vals

e = modeller.environ()
a = modeller.alignment(e, file='""" + self.workdir + os.path.basename(self.alignment_file) + """')

# try:
	# template = get_profile('""" + self.workdir + self.profile_template + """', a['""" + os.path.basename(self.profile_template)[0:-8] + """A'])
	# model = get_profile('""" + self.workdir + self.profile_model + """', a['""" + os.path.basename(self.profile_model)[0:-18] + """'])

# except Exception, e:
#	print e
template = get_profile('""" + self.profile_template + """', a['""" + os.path.basename(self.profile_template)[0:-8] + """'])
model = get_profile('""" + self.profile_model + """', a['""" + os.path.basename(self.profile_model)[0:-18] + """'])

# Plot the template and model profiles in the same plot for comparison:
fig = plt.figure(1)
ax = fig.add_subplot(111)
plt.xlabel('Alignment position')
plt.ylabel('DOPE per-residue score')
ax.plot(model, color='red', linewidth=2, label='Model')
ax.plot(template, color='green', linewidth=2, label='Template')
handles, labels = ax.get_legend_handles_labels()
lgd = ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5,-0.1))
ax.grid('on')
fig.savefig('dope_profile_loop', bbox_extra_artists=(lgd,), bbox_inches='tight')


"""
