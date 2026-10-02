import tempfile, os
from ModelingStep.MakeProfile import MakeProfile

workdir = os.path.dirname(os.path.realpath(__file__)) + os.sep


modeling_manager = MakeProfile(workdir + "TvLDH.B99990002.pdb" )
modeling_manager.execute()