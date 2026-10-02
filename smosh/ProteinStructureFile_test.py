import unittest
from smosh.ModelingTools.PDBFile import PDBFile
from should_dsl import should, should_not
import os

smosh_path = os.path.dirname(os.path.abspath(__file__)) + os.sep

class ModelingStepTests(unittest.TestCase):
	def setUp(self):
		self.pDBFileExample = PDBFile(smosh_path + 'files/1bdm.pdb','r')

	def test_pdbFile_has_a_pdb_code_with_4_char(self):
		self.pDBFileExample.pdbCode() |should| equal_to('1bdm')

	def test_strutucture_name(self):
		self.pDBFileExample.structureName() |should| equal_to('1BDM')

	def test_file_name(self):
		self.pDBFileExample.name |should| equal_to(smosh_path + 'files/1bdm.pdb')

	def test_chains(self):
		self.pDBFileExample.chains() |should| equal_to(["A", "B"])

	# def test_heteroatoms_name(self):
	# 	self.pDBFileExample.heteroatoms() |should| equal_to({"A":["NAX"], "B":["NAX"]})

	# def test_change_hetoms(self):
	# 	self.pDBFileExample.changeHetoms("A", "NAX", "HOH")
	# 	self.pDBFileExample.heteroatoms() |should| equal_to({"A":["NAX"], "B":["NAX"]})

	def test_what_heteroatoms_in_chain(self):
		self.pDBFileExample.hetatomsInChain("A") |should| equal_to(["NAX"])

	def test_execute_if_using_readlines_cause_problems(self):
		self.pDBFileExample.chains()
		self.pDBFileExample.hetatomsInChain("A") |should| equal_to(["NAX"])



if __name__ == '__main__':
	unittest.main()
