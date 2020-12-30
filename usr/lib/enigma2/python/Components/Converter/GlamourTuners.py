#	GlamourTuners converter
#	Modded and recoded by MCelliotG for use in Glamour skins or standalone
#	If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

from Components.Converter.Converter import Converter
from Components.Element import cached
import os.path


class GlamourTuners(Converter, object):
	TUNER_A = 0
	TUNER_B = 1
	TUNER_C = 2
	TUNER_D = 3
	TUNER_E = 4
	TUNER_F = 5
	TUNER_G = 6
	TUNER_H = 7
	TUNER_I = 8
	TUNER_J = 9
	TUNER_K = 10
	TUNER_L = 11
	TUNER_M = 12
	TUNER_N = 13
	TUNER_O = 14
	TUNER_P = 15
	TUNER_Q = 16
	TUNER_R = 17
	TUNER_S = 18
	TUNER_T = 19
	TUNER_U = 20
	TUNER_V = 21
	TUNER_W = 22
	TUNER_X = 23
	TUNER_Y = 24
	TUNER_Z = 25
	NIMINFO = 26


	def __init__(self, type):
		Converter.__init__(self, type)
		self.type = type
		self.short_list = True
		self.list = []
		if "Tuner_A" in type:
			self.type = self.TUNER_A
		elif "Tuner_B" in type:
			self.type = self.TUNER_B
		elif "Tuner_C" in type:
			self.type = self.TUNER_C
		elif "Tuner_D" in type:
			self.type = self.TUNER_D
		elif "Tuner_E" in type:
			self.type = self.TUNER_E
		elif "Tuner_F" in type:
			self.type = self.TUNER_F
		elif "Tuner_G" in type:
			self.type = self.TUNER_G
		elif "Tuner_H" in type:
			self.type = self.TUNER_H
		elif "Tuner_I" in type:
			self.type = self.TUNER_I
		elif "Tuner_J" in type:
			self.type = self.TUNER_J
		elif "Tuner_K" in type:
			self.type = self.TUNER_K
		elif "Tuner_L" in type:
			self.type = self.TUNER_L
		elif "Tuner_M" in type:
			self.type = self.TUNER_M
		elif "Tuner_N" in type:
			self.type = self.TUNER_N
		elif "Tuner_O" in type:
			self.type = self.TUNER_O
		elif "Tuner_P" in type:
			self.type = self.TUNER_P
		elif "Tuner_Q" in type:
			self.type = self.TUNER_Q
		elif "Tuner_R" in type:
			self.type = self.TUNER_R
		elif "Tuner_S" in type:
			self.type = self.TUNER_S
		elif "Tuner_T" in type:
			self.type = self.TUNER_T
		elif "Tuner_U" in type:
			self.type = self.TUNER_U
		elif "Tuner_V" in type:
			self.type = self.TUNER_V
		elif "Tuner_W" in type:
			self.type = self.TUNER_W
		elif "Tuner_X" in type:
			self.type = self.TUNER_X
		elif "Tuner_Y" in type:
			self.type = self.TUNER_Y
		elif "Tuner_Z" in type:
			self.type = self.TUNER_Z
		elif "NimInfo" in type:
			self.type = self.NIMINFO

######### COMMON VARIABLES #################
	def getTuners(self):
		niminfo = [ ]
		if os.path.exists("/proc/bus/nim_sockets"):
			try:
				with open("/proc/bus/nim_sockets", "r") as niminfo:
					niminfo = niminfo.readlines()
					niminfo = " ".join(map(str, niminfo))
			except IOError:
				return
			return str(niminfo)


	@cached
	def getText(self):
		service = self.source.service
		info = service and service.info()
		if not info:
			return ""

		if (self.type == self.NIMINFO):
			return str(self.getTuners())
	text = property(getText)


	@cached
	def getBoolean(self):
		service = self.source.service
		info = service and service.info()
		if not info:
			return False
		else: 
			tuners = self.getTuners()
			if (self.type == self.TUNER_A):
				if "NIM Socket 0:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_B):
				if "NIM Socket 1:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_C):
				if "NIM Socket 2:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_D):
				if "NIM Socket 3:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_E):
				if "NIM Socket 4:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_F):
				if "NIM Socket 5:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_G):
				if "NIM Socket 6:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_H):
				if "NIM Socket 7:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_I):
				if "NIM Socket 8:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_J):
				if "NIM Socket 9:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_K):
				if "NIM Socket 10:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_L):
				if "NIM Socket 11:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_M):
				if "NIM Socket 12:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_N):
				if "NIM Socket 13:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_O):
				if "NIM Socket 14:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_P):
				if "NIM Socket 15:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_Q):
				if "NIM Socket 16:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_R):
				if "NIM Socket 17:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_S):
				if "NIM Socket 18:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_T):
				if "NIM Socket 19:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_U):
				if "NIM Socket 20:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_V):
				if "NIM Socket 21:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_W):
				if "NIM Socket 22:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_X):
				if "NIM Socket 23:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_Y):
				if "NIM Socket 24:" in tuners:
					return True
				return False
			elif (self.type == self.TUNER_Z):
				if "NIM Socket 25:" in tuners:
					return True
				return False

	boolean = property(getBoolean)