import tempfile, os
from ModelingStep.AlignStep import AlignStep

workdir = os.path.dirname(os.path.realpath(__file__))


modeling_manager = AlignStep(workdir + os.sep  + "seqs.fasta")
modeling_manager.execute()
