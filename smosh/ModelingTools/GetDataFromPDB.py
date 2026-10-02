#data 26 de janeiro de 2016
#adicionar correcoes ao teste
import urllib.request, os

class GetDataFromPDB(object):
	"""docstring for GetDataFromPDB"""
	def __init__(self, path, template_name):
		super(GetDataFromPDB, self).__init__()
		self.path = path
		self.template_name = template_name

	def getPDB_File(self):
		# 1. Melhoria: Usar os.path.join para construir o caminho do arquivo
		pdb_file_path = os.path.join(self.path, self.__onlyTemplateName__() + ".pdb")
        
		response = urllib.request.urlopen('http://www.rcsb.org/pdb/download/downloadFile.do?fileFormat=pdb&compression=NO&structureId=' + self.__onlyTemplateName__())
		pdb_buffer = response.read() # pdb_buffer será bytes
        
        # 2. Correção: Usar 'wb' para escrever bytes e 'with' para fechamento seguro
		with open(pdb_file_path, "wb") as pdb_file:
			pdb_file.write(pdb_buffer)
            
		return pdb_file_path

	def get_PDB_FileFromDBorPDB(self,db_path):
		if os.path.exists(db_path + os.sep + self.template_name + ".pdb"):
			return db_path + os.sep + self.template_name + ".pdb"
		else:
			return self.getPDB_File()
	# http://www.rcsb.org/pdb/download/downloadFile.do?fileFormat=pdb&compression=NO&structureId=1ijk

	def __onlyTemplateName__(self):
		if len(self.template_name) == 4:
			return self.template_name
		else:
			return self.template_name[0:4]