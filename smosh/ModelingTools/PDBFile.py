import os
class PDBFile():
	"""docstring for PDBFile"""

	def __init__(self, pdbfilename, status):
		self.name = pdbfilename
		pdb_file = open(pdbfilename, status)
		self.lines = pdb_file.readlines()
		pdb_file.close()
	
	
	def pdbCode(self):
		return os.path.basename(self.name).split(".")[0]

	def structureName(self):
		return self.pdbCode().upper()

	def chains(self):
		list_of_chains = []
		lines = self.lines
		for eachLine in lines:
			if eachLine.startswith("ATOM"):
				chain_of_selected_line = eachLine[21]
				if chain_of_selected_line not in list_of_chains:
					list_of_chains.append(chain_of_selected_line)
		return list_of_chains

	def hetatomsInChain(self,chain):
		list_of_hetatoms = []
		lines = self.lines
		for eachLine in lines:
			if eachLine.startswith("HETATM"):
				chain_of_selected_line = eachLine[21]
				if chain_of_selected_line == chain:
					hetatom_of_line = eachLine[17:20]
					if hetatom_of_line not in list_of_hetatoms:					
						list_of_hetatoms.append(hetatom_of_line)
		return list_of_hetatoms

	# def selectChainandHets(self):
	# 	pass

	def removeWaters(self):
		lines = self.lines
		new_lines = []
		for eachLine in lines:
			if not eachLine[17:20] == "HOH" or eachLine[17:20] == "SOL":
				new_lines.append(eachLine)

		self.lines = new_lines

	def const(self,  hetatms,  chains):
            pdbsaida = ''
            for i in self.lines:
                Line = filter(None, re.split(" ", i))

                if(Line[0] != "CONECT"):
                    if ((Line[0] == "COMPND") and (Line[2] == "CHAIN:")):
                        texto = "COMPND   3 CHAIN: "
                        for letra in range(0, len(chains)):
                            texto = texto + chains[letra]
                            if (letra != len(chains)-1):
                                texto = texto + ","                        
                        pdbsaida = pdbsaida + texto + ";" + (62-2*len(chains))*(" ") + "\n"

                    else:
                        if ((i.startswith("ATOM")) or (i.startswith("HETATM"))):
                                 if((i[21] in chains) and (i[17:20].replace(" ", "") in hetatms[i[21]])):
                                    pdbsaida = pdbsaida  + i
                                 else:
                                     pass
                                 if((i.startswith("ATOM")) and (i[21] in chains)):
                                    pdbsaida = pdbsaida + i
                                 else:
                                    pass
                        else:
                                pdbsaida = pdbsaida + i
            return(pdbsaida)

	def const(self, hetatms, chains):
	    pdbsaida = ''
	    for i in self.lines:
	        # Melhoria: Usar list comprehension para dividir e filtrar
	        # Isso substitui o filter() do Python 2 de forma mais clara
	        line_parts = [item for item in i.split(" ") if item]
	        
	        # Ignora linhas vazias ou muito curtas
	        if not line_parts:
	            continue
	        
	        # Processa a linha COMPND
	        if i.startswith("COMPND") and len(line_parts) > 2 and line_parts[2] == "CHAIN:":
	            texto = "COMPND   3 CHAIN: "
	            texto += ",".join(chains)
	            pdbsaida += texto.ljust(80) + "\n" # ljust alinha e preenche com espaços até 80 caracteres
	        
	        # Processa as linhas ATOM e HETATM
	        elif i.startswith("ATOM") or i.startswith("HETATM"):
	            # Acessar a cadeia de caracteres na posição 21
	            chain_id = i[21]
	            
	            # Acessar o resíduo (resíduo de aminoácido) na posição 17-20
	            res_name = i[17:20].strip()

	            # Verificação para a cadeia e hetatms
	            if chain_id in chains:
	                if i.startswith("ATOM"):
	                    pdbsaida += i
	                elif i.startswith("HETATM") and res_name in hetatms.get(chain_id, []):
	                    pdbsaida += i

	        # Adiciona outras linhas que não ATOM, HETATM ou COMPND
	        else:
	            pdbsaida += i
	            
	    return pdbsaida
# class ClassName(object):
# 	"""docstring for ClassName"""
# 	def __init__(self, arg):
# 		super(ClassName, self).__init__()
# 		self.arg = arg
		
