import tempfile, os
from ModelingStep.BuildModelStep import BuildModelStep

workdir = os.path.dirname(os.path.realpath(__file__))


modeling_manager = BuildModelStep(workdir + os.sep  + "TvLDH-1bdmA.ali", workdir + os.sep + '1bdm.pdb')
modeling_manager.execute()
