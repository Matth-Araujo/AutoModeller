import tempfile, os
from ModelingStep.EvaluateEnergy import EvaluateEnergy

workdir = os.path.dirname(os.path.realpath(__file__)) + os.sep


modeling_manager = EvaluateEnergy(workdir   + "ali.ali", workdir + "1bdm.profile", workdir + "TvLDH.B99990002.profile" )
modeling_manager.execute()