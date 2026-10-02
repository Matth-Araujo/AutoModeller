import unittest
from smosh.ModelingStep.FindTemplatesStep import FindTemplatesStep
from smosh.ModelingStep.BuildModelStep import BuildModelStep
from smosh.Exceptions.ModellerException import ModellerException
from should_dsl import should, should_not
import os

smosh_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

class ModelingStepTests(unittest.TestCase):

	def test_if_normally_no_raise_exception(self):
		good_findTemplateExample = FindTemplatesStep(smosh_path + 'files/TvLDH.pir', "FASTA")
		try:
			os.remove(smosh_path +'files/build_profilePAP.ali')
			os.remove(smosh_path + 'files/build_profilePIR.ali')
		except Exception as e:
			pass
		ModellerException |should_not| be_thrown_by(good_findTemplateExample.execute)

	def test_if_raise_exception(self):
		bad_findTemplateExample = FindTemplatesStep(smosh_path + 'files/input_dummy_file.txt', "FASTA")
		ModellerException |should| be_thrown_by(bad_findTemplateExample.execute)

	def test_internal_error_of_modeller_raise_ModellerException(self):
		buildModelStepExample = BuildModelStep(smosh_path + 'files/problematic_ali.ali',smosh_path +  'files/1bdm.pdb')
		try:
			filenames = ["TvLDH.B99990001.pdb", "TvLDH.B99990002.pdb", "TvLDH.B99990003.pdb", "TvLDH.B99990004.pdb"]
			for eachFile in filenames:
				os.remove(smosh_path + 'files/' + eachFile)
			# os.remove('files/ali.ali')
		except Exception as e:
			pass
		ModellerException |should| be_thrown_by(buildModelStepExample.execute)

	def test_creation_of_log_of_error(self):
		buildModelStepExample = BuildModelStep(smosh_path + 'files/problematic_ali.ali',smosh_path +  'files/1bdm.pdb')
		try:
			buildModelStepExample.execute()
		except ModellerException as e:
			pass
		
		workdir = buildModelStepExample.workdir
		os.path.exists(workdir + "/error.log") |should| equal_to(True)

	# def test_good_step_must_dont_have_a_error_log(self):
	# 	good_findTemplateExample = FindTemplatesStep('files/TvLDH.pir')
	# 	good_findTemplateExample.execute()
	# 	workdir = good_findTemplateExample.workdir
	# 	os.path.exists(workdir + "/error.log") |should| equal_to(False)

	def test_creation_output_log(self):
		good_findTemplateExample = FindTemplatesStep(smosh_path + 'files/TvLDH.pir', "FASTA")
		good_findTemplateExample.execute()
		workdir = good_findTemplateExample.workdir
		os.path.exists(workdir + "/out.log") |should| equal_to(True)

	def test_if_exception_had_a_mensage(self):
		buildModelStepExample = BuildModelStep(smosh_path + 'files/problematic_ali.ali',smosh_path +  'files/1bdm.pdb')
		try:
			buildModelStepExample.execute()
		except ModellerException as e:
			e.log |should| be_kind_of(str)

	def test_log_of_ModellerException_is_Modeller_data(self):
		buildModelStepExample = BuildModelStep(smosh_path + 'files/problematic_ali.ali',smosh_path +  'files/1bdm.pdb')
		try:
			buildModelStepExample.execute()
		except ModellerException as e:
			e.log |should| contain("mismatch at alignment position    319")



if __name__ == '__main__':
	unittest.main()
