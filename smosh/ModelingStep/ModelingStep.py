from abc import ABC, abstractmethod
import tempfile, os, shutil, sys
from smosh.ModelingStep.Modeller_Caller import Modeller_Caller
from ..Exceptions.ModellerException import ModellerException


class ModelingStep(ABC):

	def __init__(self):
		self.pre_execution()

	def pre_execution(self): 
		self.__prepare_workdir_and_copy_input_files__()

	def execute(self):
		try:
			self.make_script()
			processo = Modeller_Caller()
			if processo.run(self.workdir + '/step.py'):
				out_log_path = os.path.join(self.workdir, "out.log")
				err_log_path = os.path.join(self.workdir, "error.log")
				text_of_generated_log = ""
				text_of_generated_error_log = ""
				if os.path.exists(out_log_path):
					with open(out_log_path, 'r', encoding='utf-8', errors='ignore') as generated_log:
						text_of_generated_log = generated_log.read()
				if os.path.exists(err_log_path):
					with open(err_log_path, 'r', encoding='utf-8', errors='ignore') as generated_error_log:
						text_of_generated_error_log = generated_error_log.read()
				if not text_of_generated_error_log and getattr(processo, 'last_stderr', ''):
					text_of_generated_error_log = processo.last_stderr
				raise ModellerException(
					"--- out.log ---\n" + text_of_generated_log +
					"\n--- error.log ---\n" + text_of_generated_error_log
				)
			self.pos_execution()
		finally:
			# Limpa diretório temporário em /tmp para evitar lotação de disco no servidor
			if getattr(self, 'workdir', None) and os.path.isdir(self.workdir):
				shutil.rmtree(self.workdir, ignore_errors=True)

	def pos_execution(self): 
		self.__copy_files_to_output_dir__()

	def make_script(self):
		script = self.get_log_header() + "\n" + self.__get_script__() + "\n" + self.get_log_footer()
		arq = open(self.workdir + 'step.py', 'w')
		arq.write(script)
		arq.close()

	def __prepare_workdir_and_copy_input_files__(self):
		self.workdir = tempfile.mkdtemp() + os.sep
		for eachFile in self.__input_files__:
			shutil.copyfile(eachFile, self.workdir + os.path.basename(eachFile))
	
	def __copy_files_to_output_dir__(self):
		for eachFile in self.__output_files__:
			shutil.copyfile(self.workdir + eachFile, self.output_dir + os.sep + os.path.basename(eachFile))

	def __installfolder__(self):
		'''Returns where the Smosh was instaled'''
		import smosh
		return os.path.dirname(os.path.realpath(smosh.__file__)) + os.sep

	@abstractmethod
	def __get_script__(self): pass
		#get script data

	def get_log_header(self):
		return """\
import sys
fsock = open('""" + self.workdir + """out.log', 'w') 
fsockerror = open('""" + self.workdir + """error.log', 'w')
saverrorout = sys.stderr 
sys.stderr = fsockerror
sys.stdout = fsock  
saveout = sys.stdout"""

	def get_log_footer(self):
		return """\
sys.stdout = saveout
sys.stderr = saverrorout
fsock.close() 
fsockerror.close()"""
