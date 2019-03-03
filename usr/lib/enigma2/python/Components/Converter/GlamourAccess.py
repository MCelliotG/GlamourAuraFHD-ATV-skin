#  GlamourAccess converter
#  Modded and recoded by MCelliotG for use in Glamour skins or standalone
#  Based on CaidInfo2 converter coded by bigroma & 2boom
#  If you use this Converter for other skins and rename it, please keep the first and second line

from Components.Converter.Converter import Converter
from enigma import iServiceInformation, iPlayableService
from Tools.Directories import fileExists
from Components.Element import cached
from string import upper
from Components.config import config, ConfigText, ConfigSubsection
from Poll import Poll
import os
info = {}
old_ecm_mtime = None
try:
	config.softcam_actCam = ConfigText()
	config.softcam_actCam2 = ConfigText()
except:
	pass


class GlamourAccess(Poll, Converter, object):
	CAID = 0
	PID = 1
	BETACAS = 2
	IRDCAS = 3
	SECACAS = 4
	VIACAS = 5
	NAGRACAS = 6
	CRWCAS = 7
	NDSCAS = 8
	CONAXCAS = 9
	DRCCAS = 10
	BISSCAS = 11
	BULCAS = 12
	VMXCAS = 13
	PWVCAS = 14
	TBGCAS = 15
	TGFCAS = 16
	PANCAS = 17
	EXSCAS = 18
	RUSCAS = 19
	BETAECM = 20
	IRDECM = 21
	SECAECM = 22
	VIAECM = 23
	NAGRAECM = 24
	CRWECM = 25
	NDSECM = 26
	CONAXECM = 27
	DRCECM = 28
	BISSECM = 29
	BULECM = 30
	VMXECM = 31
	PWVECM = 32
	TBGECM = 33
	TGFECM = 34
	PANECM = 35
	EXSECM = 36
	RUSECM = 37
	CODICAS = 38
	CGDCAS = 39
	AGTCAS = 40
	CAIDINFO = 41
	PROV = 42
	NET = 43
	EMU = 44
	CRD = 45
	CRDTXT = 46
	FTA = 47
	CACHE = 48
	CRYPT = 49
	CRYPTINFO = 50
	CAMNAME = 51
	ADDRESS = 52
	ECMTIME = 53
	FORMAT = 54
	ECMINFO = 55
	SHORTINFO = 56
	ISCRYPTED = 57
	timespan = 1000

	def __init__(self, type):
		Poll.__init__(self)
		Converter.__init__(self, type)
		if type == "CaID":
			self.type = self.CAID
		elif type == "Pid":
			self.type = self.PID
		elif type == "BetaCaS":
			self.type = self.BETACAS
		elif type == "IrdCaS":
			self.type = self.IRDCAS
		elif type == "SecaCaS":
			self.type = self.SECACAS
		elif type == "ViaCaS":
			self.type = self.VIACAS
		elif type == "NagraCaS":
			self.type = self.NAGRACAS
		elif type == "CrwCaS":
			self.type = self.CRWCAS
		elif type == "NdsCaS":
			self.type = self.NDSCAS
		elif type == "ConaxCaS":
			self.type = self.CONAXCAS
		elif type == "DrcCaS":
			self.type = self.DRCCAS
		elif type == "BissCaS":
			self.type = self.BISSCAS
		elif type == "BulCaS":
			self.type = self.BULCAS
		elif type == "VmxCaS":
			self.type = self.VMXCAS
		elif type == "PwvCaS":
			self.type = self.PWVCAS
		elif type == "TbgCaS":
			self.type = self.TBGCAS
		elif type == "TgfCaS":
			self.type = self.TGFCAS
		elif type == "PanCaS":
			self.type = self.PANCAS
		elif type == "ExsCaS":
			self.type = self.EXSCAS
		elif type == "RusCaS":
			self.type = self.RUSCAS
		elif type == "BetaEcm":
			self.type = self.BETAECM
		elif type == "IrdEcm":
			self.type = self.IRDECM
		elif type == "SecaEcm":
			self.type = self.SECAECM
		elif type == "ViaEcm":
			self.type = self.VIAECM
		elif type == "NagraEcm":
			self.type = self.NAGRAECM
		elif type == "CrwEcm":
			self.type = self.CRWECM
		elif type == "NdsEcm":
			self.type = self.NDSECM
		elif type == "ConaxEcm":
			self.type = self.CONAXECM
		elif type == "DrcEcm":
			self.type = self.DRCECM
		elif type == "BissEcm":
			self.type = self.BISSECM
		elif type == "BulEcm":
			self.type = self.BULECM
		elif type == "VmxEcm":
			self.type = self.VMXECM
		elif type == "PwvEcm":
			self.type = self.PWVECM
		elif type == "TbgEcm":
			self.type = self.TBGECM
		elif type == "TgfEcm":
			self.type = self.TGFECM
		elif type == "PanEcm":
			self.type = self.PANECM
		elif type == "ExsEcm":
			self.type = self.EXSECM
		elif type == "RusEcm":
			self.type = self.RUSECM
		elif type == "CodiCaS":
			self.type = self.CODICAS
		elif type == "CgdCaS":
			self.type = self.CGDCAS
		elif type == "AgtCaS":
			self.type = self.AGTCAS
		elif type == "CaidInfo":
			self.type = self.CAIDINFO
		elif type == "ProvID":
			self.type = self.PROV
		elif type == "Net":
			self.type = self.NET
		elif type == "Emu":
			self.type = self.EMU
		elif type == "Crd":
			self.type = self.CRD
		elif type == "CrdTxt":
			self.type = self.CRDTXT
		elif type == "Fta":
			self.type = self.FTA
		elif type == "Cache":
			self.type = self.CACHE
		elif type == "Crypt":
			self.type = self.CRYPT
		elif type == "CryptInfo":
			self.type = self.CRYPTINFO
		elif type == "CamName":
			self.type = self.CAMNAME
		elif type == "Address":
			self.type = self.ADDRESS
		elif type == "EcmTime":
			self.type = self.ECMTIME
		elif type == "IsCrypted":
			self.type = self.ISCRYPTED
		elif type == "ShortInfo":
			self.type = self.SHORTINFO
		elif type == "EcmInfo" or type == "Default" or type == "" or type == None or type == "%":
			self.type = self.ECMINFO
		else:
			self.type = self.FORMAT
			self.sfmt = type[:]

		self.CaidsDecoded = {"00": "Unknown",
		 "10": "Tandberg",
		 "26": "Biss/EBU",
		 "01": "Seca/Mediaguard",
		 "06": "Irdeto",
		 "17": "Betacrypt",
		 "05": "Viaccess",
		 "18": "Nagravision",
		 "09": "NDS/Videoguard",
		 "0B": "Conax",
		 "0D": "CryptoWorks",
		 "4A": "DreamCrypt & variants",
		 "27": "ExSet/PolyCipher",
		 "0E": "PowerVu",
		 "22": "CodiCrypt",
		 "07": "DigiCipher",
		 "56": "Verimatrix",
		 "7B": "DreCrypt",
		 "48": "AccessGate",
		 "A1": "RusCrypt"}


	@cached
	def getBoolean(self):
		service = self.source.service
		info = service and service.info()
		ecm_info = self.ecmfile()
		self.poll_interval = self.timespan
		self.poll_enabled = True
		if not info:
			return False
		caids = list(set(info.getInfoObject(iServiceInformation.sCAIDs)))

		if self.type is self.FTA:
			if caids:
				return False
			return True

		if self.type is self.ISCRYPTED:
			if caids:
				return True
			return False

		if caids:
			if self.type == self.BETACAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "1700" and ("%0.4X" % int(caid))[:4] <= "17FF":
						return True
				return False
			if self.type == self.IRDCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "0600" and ("%0.4X" % int(caid))[:4] <= "06FF":
						return True
				return False
			if self.type == self.SECACAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "0100" and ("%0.4X" % int(caid))[:4] <= "01FF":
						return True
				return False
			if self.type == self.VIACAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "0500" and ("%0.4X" % int(caid))[:4] <= "05FF":
						return True
				return False
			if self.type == self.NAGRACAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "1800" and ("%0.4X" % int(caid))[:4] <= "18FF":
						return True
				return False
			if self.type == self.CRWCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "0D00" and ("%0.4X" % int(caid))[:4] <= "0DFF":
						return True
				return False
			if self.type == self.NDSCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "0900" and ("%0.4X" % int(caid))[:4] <= "09FF":
						return True
				return False
			if self.type == self.CONAXCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "0B00" and ("%0.4X" % int(caid))[:4] <= "0BFF":
						return True
				return False
			if self.type == self.DRCCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "4A00" and ("%0.4X" % int(caid))[:4] <= "4AE9" or ("%0.4X" % int(caid))[:4] >= "5000" and ("%0.4X" % int(caid))[:4] <= "50FF" or ("%0.4X" % int(caid))[:4] == "7BE0" or ("%0.4X" % int(caid))[:4] >= "0700" and ("%0.4X" % int(caid))[:4] <= "07FF" or ("%0.4X" % int(caid))[:4] >= "4700" and ("%0.4X" % int(caid))[:4] <= "47FF":
						return True
				return False
			if self.type == self.BISSCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "2600" and ("%0.4X" % int(caid))[:4] <= "26FF":
						return True
				return False
			if self.type == self.BULCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "5501" and ("%0.4X" % int(caid))[:4] <= "55FF" or ("%0.4X" % int(caid))[:4] == "4AEE" or ("%0.4X" % int(caid))[:4] == "4AF8":
						return True
				return False
			if self.type == self.VMXCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "5600" and ("%0.4X" % int(caid))[:4] <= "56FF":
						return True
				return False
			if self.type == self.PWVCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "0E00" and ("%0.4X" % int(caid))[:4] <= "0EFF":
						return True
				return False
			if self.type == self.TBGCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "1000" and ("%0.4X" % int(caid))[:4] <= "10FF":
						return True
				return False
			if self.type == self.TGFCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "4B00" and ("%0.4X" % int(caid))[:4] <= "4B09" or ("%0.4X" % int(caid))[:4] == "4AF6":
						return True
				return False
			if self.type == self.PANCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] == "4AFC":
						return True
				return False
			if self.type == self.EXSCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "2700" and ("%0.4X" % int(caid))[:4] <= "27FF":
						return True
				return False
			if self.type == self.RUSCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "A100" and ("%0.4X" % int(caid))[:4] <= "A1FF":
						return True
				return False
			if self.type == self.CODICAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "2200" and ("%0.4X" % int(caid))[:4] <= "22FF":
						return True
				return False
			if self.type == self.CGDCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] == "4AEA" or ("%0.4X" % int(caid))[:4] >= "1EC0" and ("%0.4X" % int(caid))[:4] <= "1ECF":
						return True
				return False
			if self.type == self.AGTCAS:
				for caid in caids:
					if ("%0.4X" % int(caid))[:4] >= "4800" and ("%0.4X" % int(caid))[:4] <= "48FF":
						return True
				return False

			if ecm_info:
				caid = ("%0.4X" % int(ecm_info.get("caid", ""), 16))[:4]
				if self.type == self.BETAECM:
					if caid >= "1700" and caid <= "17FF":
						return True
					return False
				if self.type == self.IRDECM:
					if caid >= "0600" and caid <= "06FF":
						return True
					return False
				if self.type == self.SECAECM:
					if caid >= "0100" and caid <= "01FF":
						return True
					return False
				if self.type == self.VIAECM:
					if caid >= "0500" and caid <= "05FF":
						return True
					return False
				if self.type == self.NAGRAECM:
					if caid >= "1800" and caid <= "18FF":
						return True
					return False
				if self.type == self.CRWECM:
					if caid >= "0D00" and caid <= "0DFF" or caid >= "4900" and caid <= "49FF":
						return True
					return False
				if self.type == self.NDSECM:
					if caid >= "0900" and caid <= "09FF":
						return True
					return False
				if self.type == self.CONAXECM:
					if caid >= "0B00" and caid <= "0BFF":
						return True
					return False
				if self.type == self.DRCECM:
					if caid >= "4A00" and caid <= "4AE9" or caid >= "5000" and caid <= "50FF" or caid == "7BE0" or caid >= "0700" and caid <= "07FF" or caid >= "4700" and caid <= "47FF":
						return True
					return False
				if self.type == self.BISSECM:
					if caid >= "2600" and caid <= "26FF":
						return True
					return False
				if self.type == self.BULECM:
					if caid >= "5501" and caid <= "55FF" or caid == "4AEE" or caid == "4AF8":
						return True
					return False
				if self.type == self.VMXECM:
					if caid >= "5600" and caid <= "56FF":
						return True
					return False
				if self.type == self.PWVECM:
					if caid >= "0E00" and caid <= "0EFF":
						return True
					return False
				if self.type == self.TBGECM:
					if caid >= "1000" and caid <= "10FF":
						return True
					return False
				if self.type == self.TGFECM:
					if caid >= "4B00" and caid <= "4B09" or caid == "4AF6":
						return True
					return False
				if self.type == self.PANECM:
					if caid == "4AFC":
						return True
					return False
				if self.type == self.EXSECM:
					if caid >= "2700" and caid <= "27FF":
						return True
					return False
				if self.type == self.RUSECM:
					if caid >= "A100" and caid <= "A1FF":
						return True
					return False

				reader = str(ecm_info.get("reader", ""))
				protocol = str(ecm_info.get("protocol", ""))
				frm = str(ecm_info.get("from", ""))
				using = str(ecm_info.get("using", ""))
				source = str(ecm_info.get("source", ""))

				if self.type == self.CRD:
					if source == "sci":
						return True
					if source is not "cache" and source is not "net" and source.find("emu") == -1:
						return True
					return False
				if self.type == self.CACHE:
					if source == "cache" or reader == "Cache" or "cache" in frm:
						return True
					return False
				if self.type == self.EMU:
					return using == "emu" or source == "emu" or source == "card" or reader == "emu" or source.find("card") > -1 or source.find("emu") > -1 or source.find("biss") > -1 or source.find("tb") > -1 or reader.find("constant_cw") > -1 or protocol.find("constcw") > -1 or protocol.find("static") > -1
				if self.type == self.NET:
					if source == "net" and not "unsupported" in protocol and not "cache" in frm and not "static" in protocol:
						return True
					return False
		return False

	boolean = property(getBoolean)


	@cached
	def getText(self):
		ecminfo = ""
		server = ""
		ecm_info = self.ecmfile()
		ecmpath = self.ecmpath()
		self.poll_interval = self.timespan
		self.poll_enabled = True
		service = self.source.service
		if service:
			info = service and service.info()

			if self.type == self.CRYPTINFO:
				if fileExists(ecmpath):
					try:
						caid = "%0.4X" % int(ecm_info.get("caid", ""), 16)
						return "%s" % self.CaidsDecoded.get(caid[:2])
					except:
						return "Cannot decode"
				else:
					return "Cannot decode"

			if info:
				caids = list(set(info.getInfoObject(iServiceInformation.sCAIDs)))

				if self.type == self.CAMNAME:
					return self.CamName()

				if self.type == self.CAIDINFO:
					return self.CaidInfo()

				if caids:
					if len(caids) > 0:
						caidlist = self.CaidList()
						caidtxt = self.CaidTxtList()
						for cas in caids:
							cas = self.int2hex(cas).upper().zfill(4)

					if ecm_info:
						caid = "%0.4X" % int(ecm_info.get("caid", ""), 16)
						if self.type == self.CAID:
							return caid
						if self.type == self.CRYPT:
							return "%s" % self.CaidsDecoded.get(caid[:2])
						try:
							pid = "%0.4X" % int(ecm_info.get("pid", ""), 16)
						except:
							pid = ""
						if self.type == self.PID:
							return pid
						try:
							prov = "%0.6X" % int(ecm_info.get("prov", ""), 16)
						except:
							prov = ecm_info.get("prov", "")

						if self.type == self.PROV:
							return prov
						if ecm_info.get("ecm time", "").find("msec") > -1:
							ecm_time = ecm_info.get("ecm time", "")
						else:
							ecm_time = ecm_info.get("ecm time", "").replace(".", "").lstrip("0") + " msec"

						if self.type == self.ECMTIME:
							return ecm_time

						protocol = ecm_info.get("protocol", "")
						port = ecm_info.get("port", "")
						source = ecm_info.get("source", "")
						server = ecm_info.get("server", "")
						hops = hop = ecm_info.get("hops", "")
						if hops:
							if hops > "0":
								hops = " Hops: %s" % hops
								hop = "(%s)" % hop
							else:
								hops = hop = ""
						system = ecm_info.get("system", "")
						frm = ecm_info.get("from", "")
						if len(frm) > 36:
							frm = "%s..." % frm[:35]
						provider = ecm_info.get("provider", "")
						if provider:
							provider = "Prov: " + provider
						reader = ecm_info.get("reader", "")
						if len(reader) > 36:
							reader = "%s..." % reader[:35]

						if self.type == self.CRDTXT:
							info_card = "False"
							if source == "sci":
								info_card = "True"
							if source is not "cache" and source is not "net" and source.find("emu") == -1:
								info_card = "True"
							return info_card

						if self.type == self.ADDRESS:
							return server

						if self.type == self.FORMAT:
							ecminfo = ""
							params = self.sfmt.split(" ")
							for param in params:
								if param is not "":
									if param[0] is not "%":
										ecminfo += param
									elif param == "%S":
										ecminfo += server
									elif param == "%H":
										ecminfo += hops
									elif param == "%SY":
										ecminfo += system
									elif param == "%PV":
										ecminfo += provider
									elif param == "%SP":
										ecminfo += port
									elif param == "%PR":
										ecminfo += protocol
									elif param == "%C":
										ecminfo += caid
									elif param == "%P":
										ecminfo += pid
									elif param == "%p":
										ecminfo += prov
									elif param == "%O":
										ecminfo += source
									elif param == "%R":
										ecminfo += reader
									elif param == "%FR":
										ecminfo += frm
									elif param == "%T":
										ecminfo += ecm_time
									elif param == "%t":
										ecminfo += "\t"
									elif param == "%n":
										ecminfo += "\n"
									elif param[1:].isdigit():
										ecminfo = ecminfo.ljust(len(ecminfo) + int(param[1:]))
									if len(ecminfo) > 0:
										if ecminfo[-1] is not "\t" and ecminfo[-1] is not "\n":
											ecminfo += " "
							return ecminfo[:-1]

						if self.type == self.ECMINFO:
							if source == "emu":
								ecminfo = "CA: %s:%s  PID:%s  Source: %s@%s  Ecm Time: %s" % (caid, prov, pid, source, frm, ecm_time.replace("msec", "ms"))
							elif reader is not "" and source == "net" and port is not "":
								ecminfo = "CA: %s:%s  PID:%s  Reader: %s@%s  Prtc:%s (%s)  Source: %s:%s %s  Ecm Time: %s  %s" % (caid, prov, pid, reader, frm, protocol, source, server, port, hops, ecm_time.replace("msec", "ms"), provider)
							elif reader is not "" and source == "net":
								ecminfo = "CA: %s:%s  PID:%s  Reader: %s@%s  Ptrc:%s (%s)  Source: %s %s  Ecm Time: %s  %s" % (caid, prov, pid, reader, frm, protocol, source, server, hops, ecm_time.replace("msec", "ms"), provider)
							elif reader is not "" and source is not "net":
								ecminfo = "CA: %s:%s  PID:%s  Reader: %s@%s  Prtc:%s (local) - %s %s  Ecm Time: %s  %s" % (caid, prov, pid, reader, frm, protocol, source, hops, ecm_time.replace("msec", "ms"), provider)
							elif server == "" and port == "" and protocol is not "":
								ecminfo = "CA: %s:%s  PID:%s  Prtc: %s (%s) %s Ecm Time: %s" % (caid, prov, pid, protocol, source, hops, ecm_time.replace("msec", "ms"))
							elif server == "" and port == "" and protocol == "":
								ecminfo = "CA: %s:%s  PID:%s  Source: %s  Ecm Time: %s" % (caid, prov, pid, source, ecm_time.replace("msec", "ms"))
							else:
								try:
									ecminfo = "CA: %s:%s  PID:%s  Addr:%s:%s  Prtc: %s (%s) %s  Ecm Time: %s  %s" % (caid, prov, pid, server, port, protocol, source, hops, ecm_time.replace("msec", "ms"), provider)
								except:
									pass

						if self.type == self.SHORTINFO:
							if source == "emu":
								ecminfo = "%s:%s - %s - %s" % (caid, prov, source, self.CaidsDecoded.get(caid[:2]))
							elif server == "" and port == "":
								ecminfo = "%s:%s - %s - %s" % (caid, prov, source, ecm_time.replace("msec", "ms"))
							else:
								try:
									if reader is not "":
										ecminfo = "%s:%s - %s %s - %s" % (caid, prov, frm, hop, ecm_time.replace("msec", "ms"))
									else:
										ecminfo = "%s:%s - %s %s - %s" % (caid, prov, server, hop, ecm_time.replace("msec", "ms"))
								except:
									pass

					elif self.type == self.ECMINFO or self.type == self.FORMAT and self.sfmt.count("%") > 3:
						ecminfo = "Service with %s encryption (%s)" % (caidtxt, caidlist)
					elif self.type == self.SHORTINFO:
						ecminfo = "Service with %s encryption" % (caidtxt)
				elif self.type == self.ECMINFO or self.type == self.SHORTINFO or self.type == self.FORMAT and self.sfmt.count("%") > 3:
					ecminfo = "FTA service"
		return str(ecminfo)

	text = property(getText)


	def CamName(self):
		cam1 = ""
		cam2 = ""
		serlist = None
		camdlist = None
		camdname = []
		sername = []
#OpenPLI/SatDreamGr
		if fileExists("/etc/init.d/softcam") and not fileExists("/etc/image-version") or fileExists("/etc/init.d/cardserver") and not fileExists("/etc/image-version"):
			try:
				for line in open("/etc/init.d/softcam"):
					if line.find("echo") > -1:
						camdname.append(line)
				camdlist = "%s" % camdname[1].split('"')[1]
			except:
				pass
			try:
				for line in open("/etc/init.d/cardserver"):
					if line.find("echo") > -1:
						sername.append(line)
				serlist = "%s" % sername[1].split('"')[1]
			except:
				pass
			if serlist is None:
				serlist = ""
			elif camdlist is None:
				camdlist = ""
			elif serlist is None and camdlist is None:
				serlist = ""
				camdlist = ""
			return "%s %s" % (serlist, camdlist)
#OE-A
		if fileExists("/etc/image-version") and not fileExists("/etc/.emustart"):
			for line in open("/etc/image-version"):
				if "=openATV" in line:
					if config.softcam.actCam.value:
						cam1 = config.softcam.actCam.value
						if " CAM 1" in cam1  or "no cam" in cam1:
							cam1 = "No CAM active"
					if config.softcam.actCam2.value:
						cam2 = config.softcam.actCam2.value
						if " CAM 2" in cam2 or "no cam" in cam2 or " CAM" in cam2:
							cam2 = ""
						else:
							cam2 = "+" + cam2
				elif "=opendroid" in line:
					cam1 = config.softcam_actCam.value
					if cam1:
						if " CAM 1" in cam1  or "no cam" in cam1:
							cam1 = "No CAM active"
					cam2 = config.softcam_actCam2.value
					if cam2:
						if " CAM 2" in cam2 or "no cam" in cam2 or " CAM" in cam2:
							cam2 = ""
						else:
							cam2 = "/" + cam2
				elif "=vuplus" in line:
					if fileExists("/tmp/.emu.info"):
						for line in open("/tmp/.emu.info"):
							cam1 = line.strip("\n")
				elif "version=" in line and fileExists("/etc/CurrentBhCamName"):
					cam1 = open("/etc/CurrentBhCamName").read()
			return "%s%s" % (cam1, cam2)
#BLACKHOLE
		if fileExists("/etc/CurrentDelCamName"):
			try:
				camdlist = open("/etc/CurrentDelCamName", "r")
			except:
				return None
		if fileExists("/etc/CurrentBhCamName"):
			try:
				camdlist = open("/etc/CurrentBhCamName", "r")
			except:
				return None
# DE-OpenBlackHole
		if fileExists("/etc/BhFpConf"):
			try:
				camdlist = open("/etc/BhCamConf", "r")
			except:
				return None
#HDMU
		if fileExists("/etc/.emustart") and fileExists("/etc/image-version"):
			try:
				for line in open("/etc/.emustart"):
					return line.split()[0].split("/")[-1]
			except:
				return None
# Domica
		if fileExists("/etc/active_emu.list"):
			try:
				camdlist = open("/etc/active_emu.list", "r")
			except:
				return None
# Egami 
		if fileExists("/tmp/egami.inf", "r"):
			try:
				lines = open("/tmp/egami.inf", "r").readlines()
				for line in lines:
					item = line.split(":", 1)
					if item[0] == "Current emulator":
						return item[1].strip()
			except:
				return None
# OoZooN
		if fileExists("/tmp/cam.info"):
			try:
				camdlist = open("/tmp/cam.info", "r")
			except:
				return None
# Dream Elite
		if fileExists("/usr/bin/emuactive"):
			try:
				camdlist = open("/usr/bin/emuactive", "r")
			except:
				return None
# Merlin2
		if fileExists("/etc/clist.list"):
			try:
				camdlist = open("/etc/clist.list", "r")
			except:
				return None
# TS-Panel
		if fileExists("/etc/startcam.sh"):
			try:
				for line in open("/etc/startcam.sh"):
					if line.find("script") > -1:
						return "%s" % line.split("/")[-1].split()[0][:-3]
			except:
				camdlist = None
#  GlassSysUtil
		if fileExists("/tmp/ucm_cam.info"):
			try:
				return open("/tmp/ucm_cam.info").read()
			except:
				return None
# Others
		if serlist is not None:
			try:
				cardserver = ""
				for current in serlist.readlines():
					cardserver = current
				serlist.close()
			except:
				pass
		else:
			cardserver = "N/A"
		if camdlist is not None:
			try:
				emu = ""
				for current in camdlist.readlines():
					emu = current
				camdlist.close()
			except:
				pass
		else:
			emu = "N/A"
		return "%s %s" % (cardserver.split("\n")[0], emu.split("\n")[0])



	def int2hex(self, int):
		return "%x" % int


	def Caids(self):
		caids = ""
		service = self.source.service
		if service:
			info = service and service.info()
			if info:
				caids = list(set(info.getInfoObject(iServiceInformation.sCAIDs)))
		return caids


	def CaidList(self):
		caids = self.Caids()
		caidlist = ""
		if caids:
			for caid in caids:
				caid = self.int2hex(caid).upper().zfill(4)
				if len(caids) > 1:
					caidlist = ", ".join(("{:04x}".format(x) for x in caids)).upper()
				else:
					caidlist += caid
		return caidlist


	def CaidTxtList(self):
		catxt = ""
		caids = self.Caids()
		if caids:
			for caid in caids:
				caid = self.int2hex(caid).upper().zfill(4)
				if caid.startswith("01"):
					caid = "Seca"
				if caid.startswith("05"):
					caid = "Viaccess"
				if caid.startswith("06"):
					caid = "Irdeto"
				if caid.startswith("07"):
					caid = "DigiChiper"
				if caid.startswith("09"):
					caid = "NDS/Videoguard"
				if caid.startswith("17"):
					caid = "Betacrypt"
				if caid.startswith("18"):
					caid = "Nagravision"
				if caid.startswith("0D"):
					caid = "CryptoWorks"
				if caid.startswith("0B"):
					caid = "Conax"
				if caid.startswith("0E"):
					caid = "PowerVu"
				if caid.startswith("26"):
					caid = "Biss/EBU"
				if caid.startswith("55"):
					caid = "Bulcrypt/Griffin"
				if caid.startswith("4AEE"):
					caid = "Bulcrypt"
				if caid.startswith("56"):
					caid = "VeriMatrix"
				if caid.startswith("4AE1") or caid.startswith("4AE5") or caid.startswith("4AE7") or caid.startswith("4AE0"):
					caid = "DreCrypt"
				if caid.startswith("7B") or caid.startswith("50"):
					caid = "DreCrypt"
				if caid.startswith("27"):
					caid = "ExSet/PolyChipher"
				if caid.startswith("4AA"):
					caid = "KeyFly"
				if caid.startswith("4AB"):
					caid = "DigiCrypt"
				if caid.startswith("4AD"):
					caid = "FireCrypt"
				if caid.startswith("4AF6") or caid.startswith("4B0"):
					caid = "Tongfang"
				if caid.startswith("4AFC"):
					caid = "PanAccess"
				if caid.startswith("4B2"):
					caid = "MultiKom DS"
				if caid.startswith("4AF8"):
					caid = "Griffin"
				if caid.startswith("53"):
					caid = "GkWare e.K."
				if caid.startswith("10"):
					caid = "Tandberg"
				if caid.startswith("22"):
					caid = "Codicrypt"
				if caid.startswith("A1"):
					caid = "RusCrypt"
				if caid.startswith("FFFE"):
					caid = "TrophyAccess"
				if caid.startswith("0F"):
					caid = "Sony"
				if caid.startswith("11"):
					caid = "Thomson"
				if caid.startswith("49"):
					caid = "CryptoWorks China"
				if caid.startswith("AA"):
					caid = "Best CAS"
				if caid.startswith("13") or caid.startswith("14"):
					caid = "HRT"
				if caid.startswith("12"):
					caid = "TV/Com"
				if caid.startswith("15"):
					caid = "IBM"
				if caid.startswith("16"):
					caid = "Nera"
				if caid.startswith("19"):
					caid = "Titan"
				if caid.startswith("20"):
					caid = "Telefonica Servicios Audiovisuales"
				if caid.startswith("21"):
					caid = "Stendor"
				if caid.startswith("47"):
					caid = "General Instruments/Motorola"
				if caid.startswith("48"):
					caid = "AccessGate/Telemann"
				if caid.startswith("43"):
					caid = "Crypton"
				if caid.startswith("23"):
					caid = "Barco AS"
				if caid.startswith("24"):
					caid = "Starguide Digital Systems"
				if caid.startswith("25"):
					caid = "Mentor Data Systems"
				if caid.startswith("0A"):
					caid = "Nokia"
				if caid.startswith("02"):
					caid = "CCETT"
				if caid.startswith("04"):
					caid = "Eurodec"
				if caid.startswith("08"):
					caid = "Matra"
				if caid.startswith("4A1"):
					caid = "Easycas"
				if caid.startswith("4A2"):
					caid = "AlphaCrypt"
				if caid.startswith("4A3"):
					caid = "DVN Holdings"
				if caid.startswith("4A4"):
					caid = "ADT"
				if caid.startswith("4A5"):
					caid = "Shenzhen Kingsky Company"
				if caid.startswith("4A6"):
					caid = "@Sky"
				if caid.startswith("4A7"):
					caid = "Dreamcrypt"
				if caid.startswith("4A8"):
					caid = "THALESCrypt"
				if caid.startswith("4A9"):
					caid = "Runcom"
				if caid.startswith("4AC"):
					caid = "Latens"
				if caid.startswith("4AF4"):
					caid = "Marlin"
				if caid.startswith("4B64"):
					caid = "Samsung/TVKey"
				if caid.startswith("4AEA") or caid.startswith("1EC"):
					caid = "CryptoGuard"
				if caid.startswith("00"):
					caid = "Unknown"
				catxt += caid + ","
				calist = catxt.rstrip(",").split(",")
				calist = list(set(calist))
				if len(calist) > 1:
					caidtxt = ", ".join(calist[:-1]) + " & " + calist[-1]
				else:
					caidtxt = calist[0]
		return caidtxt


	def CaidInfo(self):
		caids = self.Caids()
		caidlist = ""
		if caids:
			for caid in caids:
				caid = self.int2hex(caid).upper().zfill(4)
				if caid.startswith("01"):
					caid = caid + " (Seca) "
				if caid.startswith("05"):
					caid = caid + " (Viaccess) "
				if caid.startswith("06"):
					caid = caid + " (Irdeto) "
				if caid.startswith("07"):
					caid = caid + " (DigiChiper) "
				if caid.startswith("09"):
					caid = caid + " (Videoguard) "
				if caid.startswith("17"):
					caid = caid + " (Betacrypt) "
				if caid.startswith("18"):
					caid = caid + " (Nagravision) "
				if caid.startswith("0D"):
					caid = caid + " (Cryptoworks) "
				if caid.startswith("0B"):
					caid = caid + " (Conax) "
				if caid.startswith("0E"):
					caid = caid + " (PowerVu) "
				if caid.startswith("26"):
					caid = caid + " (Biss/EBU) "
				if caid.startswith("55"):
					caid = caid + " (Bulcrypt/Griffin) "
				if caid.startswith("4AEE"):
					caid = caid + " (Bulcrypt) "
				if caid.startswith("56"):
					caid = caid + " (Verimatrix) "
				if caid.startswith("4AE1") or caid.startswith("4AE5") or caid.startswith("4AE7") or caid.startswith("4AE0"):
					caid = caid + " (DreCrypt) "
				if caid.startswith("7BE0") or caid.startswith("50"):
					caid = caid + " (DreCrypt) "
				if caid.startswith("27"):
					caid = caid + " (ExSet/PolyChipher) "
				if caid.startswith("4AA"):
					caid = caid + " (KeyFly) "
				if caid.startswith("4AB"):
					caid = caid + " (DigiCrypt) "
				if caid.startswith("4AD"):
					caid = caid + " (FireCrypt) "
				if caid.startswith("4AF6") or caid.startswith("4B0"):
					caid = caid + " (Tongfang) "
				if caid.startswith("4AFC"):
					caid = caid + " (PanAccess) "
				if caid.startswith("4B2"):
					caid = caid + " (MultiKom DS) "
				if caid.startswith("4AF8"):
					caid = caid + " (Griffin) "
				if caid.startswith("53"):
					caid = caid + " (GkWare e.K.) "
				if caid >= "1000" and caid <= "10FF":
					caid = caid + " (Tandberg) "
				if caid.startswith("22"):
					caid = caid + " (Codicrypt) "
				if caid.startswith("A1"):
					caid = caid + " (RusCrypt) "
				if caid.startswith("FFFE"):
					caid = caid + " (TrophyAccess) "
				if caid.startswith("0F"):
					caid = caid + " (Sony) "
				if caid.startswith("11"):
					caid = caid + " (Thomson) "
				if caid.startswith("49"):
					caid = caid + " (CryptoWorks China) "
				if caid.startswith("AA"):
					caid = caid + " (Best CAS) "
				if caid.startswith("13") or caid.startswith("14"):
					caid = caid + " (HRT) "
				if caid.startswith("12"):
					caid = caid + " (TV/Com) "
				if caid.startswith("15"):
					caid = caid + " (IBM) "
				if caid.startswith("16"):
					caid = caid + " (Nera) "
				if caid.startswith("19"):
					caid = caid + " (Titan) "
				if caid.startswith("20"):
					caid = caid + " (Telefonica Servicios Audiovisuales) "
				if caid.startswith("21"):
					caid = caid + " (Stendor) "
				if caid.startswith("47"):
					caid = caid + " (General Instruments/Motorola) "
				if caid.startswith("48"):
					caid = caid + " (AccessGate/Telemann) "
				if caid.startswith("43"):
					caid = caid + " (Crypton) "
				if caid.startswith("23"):
					caid = caid + " (Barco AS) "
				if caid.startswith("24"):
					caid = caid + " (Starguide Digital Systems) "
				if caid.startswith("25"):
					caid = caid + " (Mentor Data Systems) "
				if caid.startswith("0A"):
					caid = caid + " (Nokia) "
				if caid.startswith("02"):
					caid = caid + " (CCETT) "
				if caid.startswith("04"):
					caid = caid + " (Eurodec) "
				if caid.startswith("08"):
					caid = caid + " (Matra) "
				if caid.startswith("4A1"):
					caid = caid + " (Easycas) "
				if caid.startswith("4A2"):
					caid = caid + " (AlphaCrypt) "
				if caid.startswith("4A3"):
					caid = caid + " (DVN Holdings) "
				if caid.startswith("4A4"):
					caid = caid + " (ADT) "
				if caid.startswith("4A5"):
					caid = caid + " (Shenzhen Kingsky Company) "
				if caid.startswith("4A6"):
					caid = caid + " (@Sky) "
				if caid.startswith("4A7"):
					caid = caid + " (Dreamcrypt) "
				if caid.startswith("4A8"):
					caid = caid + " (THALESCrypt) "
				if caid.startswith("4A9"):
					caid = caid + " (Runcom) "
				if caid.startswith("4AC"):
					caid = caid + " (Latens) "
				if caid.startswith("4AF4"):
					caid = caid + " (Marlin) "
				if caid.startswith("4B64"):
					caid = caid + " (Samsung/TVKey) "
				if caid.startswith("4AEA") or caid.startswith("1EC"):
					caid = caid + " (CryptoGuard) "
				if caid.startswith("00"):
					caid = " Unknown "
				caidlist += " " + caid
			if config.osd.language.value == "el_GR":
				caidlist = "Συστήματα κωδικοποίησης: " + caidlist
			else:
				caidlist = "Coding systems: " + caidlist
			return caidlist
		if not caids:
			if config.osd.language.value == "el_GR":
				return "Χωρίς κωδικοποίηση ή αναγνωριστικό"
			else:
				return "Free to air or no descriptor"


	def ecmpath(self):
		ecmpath = None
		if fileExists("/tmp/ecm7.info"):
			ecmpath = "/tmp/ecm7.info"
		elif fileExists("/tmp/ecm6.info") and not fileExists("tmp/ecm7.info"):
			ecmpath = "/tmp/ecm6.info"
		elif fileExists("/tmp/ecm5.info") and not fileExists("tmp/ecm6.info"):
			ecmpath = "/tmp/ecm5.info"
		elif fileExists("/tmp/ecm4.info") and not fileExists("tmp/ecm5.info"):
			ecmpath = "/tmp/ecm4.info"
		elif fileExists("/tmp/ecm3.info") and not fileExists("tmp/ecm4.info"):
			ecmpath = "/tmp/ecm3.info"
		elif fileExists("/tmp/ecm2.info") and not fileExists("tmp/ecm3.info"):
			ecmpath = "/tmp/ecm2.info"
		elif fileExists("/tmp/ecm1.info") and not fileExists("tmp/ecm2.info"):
			ecmpath = "/tmp/ecm1.info"
		elif fileExists("/tmp/ecm0.info") and not fileExists("/tmp/ecm1.info"):
			ecmpath = "/tmp/ecm0.info"
		else:
			try:
				ecmpath = "/tmp/ecm.info"
			except:
				pass
		return ecmpath


	def ecmfile(self):
		global info
		global old_ecm_mtime
		ecm = None
		ecmpath = self.ecmpath()
		service = self.source.service
		if service:
			try:
				ecm_mtime = os.stat(ecmpath).st_mtime
				if not os.stat(ecmpath).st_size > 0:
					info = {}
				if ecm_mtime == old_ecm_mtime:
					return info
				old_ecm_mtime = ecm_mtime
				ecmf = open(ecmpath, "rb")
				ecm = ecmf.readlines()
			except:
				old_ecm_mtime = None
				info = {}
				return info
			if ecm:
				for line in ecm:
					x = line.lower().find("msec")
					if x is not -1:
						info["ecm time"] = line[0:x + 4]
					else:
						item = line.split(":", 1)
						if len(item) > 1:
							if item[0] == "Provider":
								item[0] = "prov"
								item[1] = item[1].strip()[2:]
							elif item[0] == "ECM PID":
								item[0] = "pid"
							elif item[0] == "response time":
								info["source"] = "net"
								it_tmp = item[1].strip().split(" ")
								info["ecm time"] = "%s msec" % it_tmp[0]
								y = it_tmp[-1].find("[")
								if y is not -1:
									info["server"] = it_tmp[-1][:y]
									info["protocol"] = it_tmp[-1][y + 1:-1]
								y = it_tmp[-1].find("(")
								if y is not -1:
									info["server"] = it_tmp[-1].split("(")[-1].split(":")[0]
									info["port"] = it_tmp[-1].split("(")[-1].split(":")[-1].rstrip(")")
								elif y == -1:
									item[0] = "source"
									item[1] = "sci"
								if it_tmp[-1].find("emu") > -1 or it_tmp[-1].find("card") > -1 or it_tmp[-1].find("biss") > -1 or it_tmp[-1].find("tb") > -1:
									item[0] = "source"
									item[1] = "emu"
							elif item[0] == "hops":
								item[1] = item[1].strip("\n")
							elif item[0] == "from":
								item[1] = item[1].strip("\n")
							elif item[0] == "system":
								item[1] = item[1].strip("\n")
							elif item[0] == "provider":
								item[1] = item[1].strip("\n")
							elif item[0][:2] == "cw" or item[0] == "ChID" or item[0] == "Service":
								pass
							elif item[0] == "source":
								if item[1].strip()[:3] == "net":
									it_tmp = item[1].strip().split(" ")
									info["protocol"] = it_tmp[1][1:]
									info["server"] = it_tmp[-1].split(":", 1)[0]
									info["port"] = it_tmp[-1].split(":", 1)[1][:-1]
									item[1] = "net"
							elif item[0] == "prov":
								y = item[1].find(",")
								if y is not -1:
									item[1] = item[1][:y]
							elif item[0] == "reader":
								if item[1].strip() == "emu":
									item[0] = "source"
							elif item[0] == "protocol":
								if item[1].strip() == "emu" or item[1].strip() == "constcw":
									item[1] = "emu"
									item[0] = "source"
								elif item[1].strip() == "internal":
									item[1] = "sci"
									item[0] = "source"
								else:
									info["source"] = "net"
									item[0] = "server"
							elif item[0] == "provid":
								item[0] = "prov"
							elif item[0] == "using":
								if item[1].strip() == "emu" or item[1].strip() == "sci":
									item[0] = "source"
								else:
									info["source"] = "net"
									item[0] = "protocol"
							elif item[0] == "address":
								tt = item[1].find(":")
								if tt is not -1:
									info["server"] = item[1][:tt].strip()
									item[0] = "port"
									item[1] = item[1][tt + 1:]
							info[item[0].strip().lower()] = item[1].strip()
						else:
							if "caid" not in info:
								x = line.lower().find("caid")
								if x is not -1:
									y = line.find(",")
									if y is not -1:
										info["caid"] = line[x + 5:y]
							if "pid" not in info:
								x = line.lower().find("pid")
								if x is not -1:
									y = line.find(" =")
									z = line.find(" *")
									if y is not -1:
										info["pid"] = line[x + 4:y]
									elif z is not -1:
										info["pid"] = line[x + 4:z]
				ecmf.close()
		return info


	def changed(self, what):
		Converter.changed(self, (self.CHANGED_POLL,))