from smosh.ModelingStep.FindTemplatesStep import FindTemplatesStep
from smosh.ModelingStep.GetSequenceFromPDBStep import GetSequenceFromPDBStep
from smosh.ModelingStep.AlignStep import AlignStep
from smosh.ModelingStep.BuildModelStep import BuildModelStep
from smosh.ModelingStep.MakeProfile import MakeProfile
from smosh.ModelingStep.EvaluateEnergy import EvaluateEnergy
from smosh.ModelingStep.LoopRefinementStep import LoopRefinementStep

from smosh.ModelingStep.EvaluateEnergyofLoopRefinementStep import EvaluateEnergyofLoopRefinementStep

from smosh.ModelingTools.pdb import pdb
from smosh.ModelingTools.TemplateProfile import TemplateProfile
from smosh.ModelingTools.GetDataFromPDB import GetDataFromPDB
from smosh.ModelingTools.PDBFile import PDBFile
from smosh.ModelingTools.AlignFile import AlignFile

import os

def get_results(workdir,sequence_name):
        folder = workdir
        mof = 0
        filemof = ""
        for files in os.listdir(folder):
            if (files.startswith(sequence_name + '.B') and files.endswith(".pdb")):
                    arqr = open(folder + '/' + files, 'r')
                    arqr.readline()
                    linha = arqr.readline()
                    if (mof == 0) or (linha.partition(':      ')[2] < mof):
                            mof = linha.partition(':      ')[2]
                            filemof = folder + '/' + files
                            arqr.close()
        return filemof

def get_results2(workdir, sequence_name):
        folder = workdir
        mof = 0
        filemof = ""
        for files in os.listdir(folder):
            if (files.startswith(sequence_name + '.BL')):
                    arqr = open(folder + '/' + files, 'r')
                    arqr.readline()
                    linha = arqr.readline()
                    if (mof == 0) or (linha.partition(':      ')[2] < mof):
                            mof = linha.partition(':      ')[2]
                            filemof = folder + '/' + files
                            arqr.close()
        return filemof

if __name__ == '__main__':
	workdir = '/home/joao/UENF/Pesquisa/230/smosh_py3/smosh/acceptance/'
	sequence_file_name = workdir + 'AAM81249.pir'
	findTemplatesExample = FindTemplatesStep(sequence_file_name, "PIR")
	print("Searching Template Candidates...")
	findTemplatesExample.execute()

	profile_of_templates = TemplateProfile(workdir + 'build_profile.prf')
	better_profile = profile_of_templates.getBetterProfile()
	print("Selected Template: " + better_profile.name())

	print("Downloading " + better_profile.name() + " structure from PDB.org")
	template_manager = GetDataFromPDB(workdir, better_profile.name())
	downloaded_pdb_path = template_manager.getPDB_File()
	downloaded_pdb = PDBFile(downloaded_pdb_path,'r') 

	print("Removing others chains from selected template")
	new_pdb = downloaded_pdb_path + "m"
	modified_pdb = open(new_pdb, "w")
	chain = better_profile.name()[-1]
	modified_pdb.write(downloaded_pdb.const({chain: downloaded_pdb.hetatomsInChain(chain)}, chain))
	modified_pdb.close()
	os.rename(new_pdb, downloaded_pdb_path)

	print("Get Sequence from PDB File...")
	template_sequence_manager = GetSequenceFromPDBStep(downloaded_pdb_path, chain, chain)
	template_sequence_manager.execute()
	template_sequence = template_sequence_manager.__output_files__[0]

	print("Align Sequences from PDB and User")
	unaligned_sequence = workdir + 'unaligned_sequence.pir'
	filenames = [sequence_file_name, workdir + template_sequence]
	with open(unaligned_sequence, 'w') as outfile:
	    for fname in filenames:
	        with open(fname) as infile:
	            for line in infile:
	                outfile.write(line)
	sequence_Manager = AlignFile(unaligned_sequence) #verify
	sequence_Manager.copy_heteroatoms(1,0)
	sequence_Manager.write_changes()
	sequence_Manager.close()
	alignment_manager = AlignStep(unaligned_sequence)
	alignment_manager.execute()

	print("Build Model of Sequence") #melhorar
	modeling_manager = BuildModelStep(workdir + 'ali.ali', downloaded_pdb_path)
	modeling_manager.execute()
	starting_name_of_files = modeling_manager.__output_files__[0].split(".")[0]
	better_result = get_results(workdir,starting_name_of_files)
	print("better model filename: "+ better_result) 

	print("Get profile for graph DOPE Score")
	profile_manager = MakeProfile(better_result)
	profile_manager.execute()
	profile_manager2 = MakeProfile(downloaded_pdb_path)
	profile_manager2.execute()

	print("Generating DOPE Graph") 
	evaluate_energy_manager = EvaluateEnergy(workdir + 'ali.ali', workdir + profile_manager2.__output_files__[0], workdir + profile_manager.__output_files__[0])
	evaluate_energy_manager.execute()

	print("Loop Refinement in residues 1 at 5")
	loop_refinement_step = LoopRefinementStep(better_result, 1, 5)
	loop_refinement_step.execute()
	starting_name_of_files2 = loop_refinement_step.__output_files__[0].split(".")[0]

	print("Get profile for graph DOPE Score") #melhorar
	better_result2 = get_results2(workdir,starting_name_of_files2)
	profile_manager3 = MakeProfile(better_result2) 
	profile_manager3.execute()

	print("Generating DOPE Graph") 
	evaluate_energy_manager = EvaluateEnergyofLoopRefinementStep(workdir + 'ali.ali', workdir + profile_manager2.__output_files__[0], workdir + profile_manager.__output_files__[0], workdir + profile_manager3.__output_files__[0])
	evaluate_energy_manager.execute()
