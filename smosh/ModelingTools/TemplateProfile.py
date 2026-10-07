from smosh.ModelingTools.ProfileSequence import ProfileSequence

class TemplateProfile(object):
	"""docstring for TemplateProfile"""
	def __init__(self, profile_filename):
		super(TemplateProfile, self).__init__()
		self.profile_filename = profile_filename
		self.list_of_sequences = self.__get_sequences__()

	def __get_sequences__(self):
		profile_file = open(self.profile_filename, "r")
		lines = profile_file.readlines()[6:]
		list_of_sequences = []
		for eachLine in lines:
			# print eachLine
			list_of_sequences.append(ProfileSequence(eachLine))
		return list_of_sequences

	def getBetterProfile(self):
		structural_profiles = [p for p in self.list_of_sequences if p.type() == 'X']
		if not structural_profiles:
			structural_profiles = self.list_of_sequences
		if not structural_profiles:
			return None
		better_profile = structural_profiles[0]
		for eachProfile in structural_profiles:
			try:
				if float(eachProfile.identity() or 0) > float(better_profile.identity() or 0):
					better_profile = eachProfile
			except (ValueError, TypeError):
				pass
		return better_profile