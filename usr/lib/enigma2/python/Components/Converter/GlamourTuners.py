#GlamourTuners converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below


from Components.Converter.Converter import Converter
from Components.Element import cached
import os

class GlamourTuners(Converter, object):
	TUNERS = {f"Tuner_{chr(65+i)}": i for i in range(26)}  # A-Z
	TUNER_NAMES = {i: f"Tuner_{chr(65+i)}" for i in range(26)}  # Reverse mapping
	TUNERS["NimInfo"] = 26

	def __init__(self, type):
		super().__init__(type)
		self.type = self.TUNERS.get(type, None)

	def getTuners(self):
		try:
			with open("/proc/bus/nim_sockets", "r") as file:
				return [line.strip() for line in file.readlines() if "NIM Socket" in line]
		except IOError:
			return []

	@cached
	def getTotalTuners(self):
		return len(self.getTuners())

	@cached
	def getText(self):
		if self.type == 26:
			return str(self.getTotalTuners())
		return ""

	text = property(getText)

	@cached
	def getBoolean(self):
		tuners = self.getTuners()
		return any(f"NIM Socket {self.type}:" in tuner for tuner in tuners) if self.type is not None else False

	boolean = property(getBoolean)
