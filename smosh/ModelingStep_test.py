import unittest
from smosh.ModelingStep.ModelingStep import ModelingStep
from should_dsl import should, should_not
import os

smosh_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

class DummyStepClass(ModelingStep):
	"""docstring for DummyClass"""
	def __init__(self, input_dummy_file):
		self.input_dummy_file = input_dummy_file
		self.output_dir = os.path.dirname(input_dummy_file)
		self.__input_files__ = [input_dummy_file]
		self.__output_files__ = ['output_dummy_file.txt']
		super(DummyStepClass, self).__init__()

	def __get_script__(self):
		return """\
dummy_file = open('"""+ self.workdir + """output_dummy_file.txt', "w")
dummy_file.write("Hello world!")
dummy_file.close()"""


class ModelingStepTests(unittest.TestCase):
	def setUp(self):
		self.dummystep = DummyStepClass(smosh_path + 'files/input_dummy_file.txt')
		try:
			os.remove(smosh_path + 'files/output_dummy_file.txt')
		except Exception as e:
			pass
		# self.dummystep.execute()

	def test_dummystep_has_a_workdir(self):
		workdir = self.dummystep.workdir
		os.path.exists(workdir) |should| equal_to(True)

	def test_dummystep_has_a_input_file(self):
		dummy_input_file = self.dummystep.input_dummy_file
		os.path.exists(dummy_input_file) |should| equal_to(True)

	def test_dummystep_output_folder_is_equal_to_father_directory_of_input_file(self):
		# self.findTemplateExample.make_script()
		output_dir = self.dummystep.output_dir
		dummy_input_file = self.dummystep.input_dummy_file
		output_dir |should| equal_to(os.path.dirname(dummy_input_file))

	def test_get_script_output_is_a_text(self):
		self.dummystep.__get_script__() |should| be_kind_of(str)

	def test_if_workdir_contains_the_input_file(self):
		workdir = self.dummystep.workdir
		basename_of_input_file = os.path.basename(self.dummystep.input_dummy_file)
		input_file_in_workdir = workdir + basename_of_input_file
		os.path.exists(input_file_in_workdir) |should| equal_to(True)

	def test_if_workdir_contain_script(self):
		self.dummystep.make_script()
		workdir = self.dummystep.workdir
		script_path = workdir + "step.py"
		os.path.exists(script_path) |should| equal_to(True)

	def test_if_script_contain_the_right_content(self):
		self.dummystep.make_script()
		workdir = self.dummystep.workdir
		script_path = self.dummystep.workdir + "step.py"
		script_file = open(script_path, "r")
		content = script_file.read()
		script_file.close()
		content |should| equal_to("""\
import sys
fsock = open('""" + workdir + """out.log', 'w') 
fsockerror = open('""" + workdir + """error.log', 'w')
saverrorout = sys.stderr 
sys.stderr = fsockerror
sys.stdout = fsock  
saveout = sys.stdout
dummy_file = open('"""+ workdir + """output_dummy_file.txt', "w")
dummy_file.write("Hello world!")
dummy_file.close()
sys.stdout = saveout
sys.stderr = saverrorout
fsock.close() 
fsockerror.close()""")

	def test_dummystep_output_file_exists_in_workdir(self):
		self.dummystep.execute()
		output_file = self.dummystep.workdir + self.dummystep.__output_files__[0]
		os.path.exists(output_file) |should| equal_to(True)

	def test_if_output_file_has_the_right_content(self):
		self.dummystep.execute()
		output_file_name = self.dummystep.workdir + self.dummystep.__output_files__[0]
		output_file = open(output_file_name, "r")
		content = output_file.read()
		content |should| equal_to("""Hello world!""")

	def test_if_install_dir_is_a_valid_path(self):
		install_dir = self.dummystep.__installfolder__()
#		print install_dir
		os.path.exists(install_dir) |should| equal_to(True)


	def test_if_output_files_are_in_father_folder(self):
		self.dummystep.execute()

		# self.findTemplateExample.make_script()
		output_dir = self.dummystep.output_dir
		output_file = output_dir + os.sep + self.dummystep.__output_files__[0]
		# print output_file
		os.path.exists(output_file) |should| equal_to(True)

	def test_if_ModelingStep_had_a_log_Header(self):
		workdir = self.dummystep.workdir
		log_header = """\
import sys
fsock = open('""" + workdir + """out.log', 'w') 
fsockerror = open('""" + workdir + """error.log', 'w')
saverrorout = sys.stderr 
sys.stderr = fsockerror
sys.stdout = fsock  
saveout = sys.stdout"""
		self.dummystep.get_log_header() |should| equal_to(log_header)

	def test_if_ModelingStep_had_a_log_footer(self):
		log_footer = """\
sys.stdout = saveout
sys.stderr = saverrorout
fsock.close() 
fsockerror.close()"""
		self.dummystep.get_log_footer() |should| equal_to(log_footer)



if __name__ == '__main__':
	unittest.main()

