#abaixar uma linha 
class PirSequence(object):
	"""docstring for Sequence"""
	def __init__(self, user_sequence):
		self.user_sequence = user_sequence
		self.__next_sequence_symbol__ = "/"

	def number_of_chains(self):
		return self.sequence().count(self.__next_sequence_symbol__) + 1

	def sequence(self):
		list_of_lines_of_sequence = self.user_sequence.split("\n")[2:]
		str_containing_only_sequence = "\n".join(list_of_lines_of_sequence)
		return str_containing_only_sequence

	def chain(self, number_of_chain):
		chain_choosed = self.sequence().split(self.__next_sequence_symbol__)[number_of_chain - 1]
		if "*" not in chain_choosed:		
			return chain_choosed
		else:
			return chain_choosed[:-1]


	def list_heteroatoms(self, chain):
		heteroatoms = []
		for selectedResidue in self.chain(chain):
			if (selectedResidue.islower() or selectedResidue.isdigit() or not selectedResidue.isalnum()) and not (selectedResidue in ["-","*",'\n'] or selectedResidue in heteroatoms):
				heteroatoms.append(selectedResidue)
		return heteroatoms

	def change_heteroatom(self, chain, old_heteroatom, new_heteroatom):
		new_modified_sequence = self.header() + "\n"
		for selectedChain in range(1,self.number_of_chains() + 1):
			if selectedChain == chain:
				new_modified_sequence = new_modified_sequence + self.__show_chain_with_new_heteroatoms__(chain, old_heteroatom, new_heteroatom)
			else:
				new_modified_sequence = new_modified_sequence + self.chain(selectedChain)
			new_modified_sequence = new_modified_sequence + self.__next_sequence_symbol__
		new_modified_sequence = new_modified_sequence[:-1] # remove last "/"
		new_modified_sequence = new_modified_sequence + "*" # add terminator symbol
		self.user_sequence = new_modified_sequence

	def add_heteroatoms(self, het_sequence):
		cleaned = self.user_sequence.rstrip('\r\n')
		if cleaned.endswith('*'):
			cleaned = cleaned[:-1]
		self.user_sequence = cleaned + het_sequence + "*"

	def header(self):
		list_of_lines_of_header = self.user_sequence.split("\n")[0:2]
		str_containing_only_header = "\n".join(list_of_lines_of_header)
		return str_containing_only_header

	def __show_chain_with_new_heteroatoms__(self, chain, old_heteroatom, new_heteroatom):
		return self.chain(chain).replace(old_heteroatom, new_heteroatom)

	def change_het_in_position(self,heteroatom, position):
		new_modified_sequence = self.header() + "\n"
		number_of_returns = self.sequence()[:position].count("\n")
		real_position = position # - number_of_returns
		new_modified_sequence = new_modified_sequence + self.sequence()[:real_position -1] + heteroatom + self.sequence()[real_position:]
		self.user_sequence = new_modified_sequence

	def name(self):
		return self.header().split("\n")[0].split(";")[1]
	def type(self):
		return self.header().split("\n")[1].split(":")[0]

	def number_of_gap_in_n_terminals(self):
		count = 0
		for eachLetter in self.sequence():
			if eachLetter == "-":
				count = count + 1
			else:
				break
		return count

	def removestartNatoms(self, n):
		if n > 0:
			# print self.user_sequence
			only_sequece = self.user_sequence.split("\n")[2:]
			size_of_line = len(only_sequece[1])
			full_sequence = "".join(only_sequece)
			removed_NatomsSequence = full_sequence[n:-1]
			parted_sequence = [removed_NatomsSequence[i:i+size_of_line] for i in range(0, len(removed_NatomsSequence), size_of_line)]###
			# self.user_sequence = parted_sequence
			self.user_sequence = self.header() + "\n" + "\n".join(parted_sequence) + "*"
			# self.user_sequence = [n:-1]
