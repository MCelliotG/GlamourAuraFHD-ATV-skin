#GlamourAccess converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

from Components.Converter.Converter import Converter
from enigma import iServiceInformation, iPlayableService
from Components.Element import cached
from Components.config import config, ConfigText, ConfigSubsection
from Components.Converter.Poll import Poll
import os
from os import path
info = {}
old_ecm_mtime = None
try:
	config.softcam_actCam = ConfigText()
	config.softcam_actCam2 = ConfigText()
except:
	pass

cainfo = (
	("0000", "0000", "no or unknown"),
	("0001", "0001", "IPDC SPP"),
	("0002", "0002", "18Crypt"),
	("0004", "0006", "OMA"),
	("0007", "0007", "Open IPTV"),
	("0008", "0008", "Open Mobile Alliance"),
	("0100", "01FF", "Seca"),
	("0200", "02FF", "CCETT"),
	("0300", "03FF", "Kabel Deutschland"),
	("0400", "04FF", "Eurodec"),
	("0500", "05FF", "Viaccess"),
	("0600", "06FF", "Irdeto"),
	("0700", "07FF", "Digichiper"),
	("0800", "08FF", "Matra"),
	("0900", "09FF", "NDS/Videoguard"),
	("0A00", "0AFF", "Nokia"),
	("0B00", "0BFF", "Conax"),
	("0C00", "0CFF", "NTL"),
	("0D00", "0DFF", "Cryptoworks"),
	("0E00", "0EFF", "PowerVu"),
	("0F00", "0FFF", "Sony"),
	("1000", "10FF", "Tandberg"),
	("1100", "11FF", "Thomson"),
	("1200", "12FF", "TV/Com"),
	("1300", "14FF", "HRT"),
	("1500", "15FF", "IBM"),
	("1600", "16FF", "Nera"),
	("1702", "1702", "Betacrypt"),
	("1722", "1722", "Betacrypt"),
	("1762", "1762", "Betacrypt"),
	("1700", "1701", "Verimatrix"),
	("1703", "1721", "Verimatrix"),
	("1723", "1761", "Verimatrix"),
	("1763", "17FF", "Verimatrix"),
	("1800", "18FF", "Nagravision"),
	("1900", "19FF", "Titan"),
	("1E00", "1E07", "Alticast"),
	("1EA0", "1EA0", "Monacrypt"),
	("1EB0", "1EB0", "Telecast"),
	("1EC0", "1EC2", "Cryptoguard"),
	("1ED0", "1ED1", "Monacrypt"),
	("2000", "20FF", "Telefonica Servicios Audiovisuales"),
	("2100", "21FF", "Stendor"),
	("2200", "22FF", "Codicrypt"),
	("2300", "23FF", "Barco"),
	("2400", "24FF", "Starguide"),
	("2500", "25FF", "Mentor"),
	("2600", "2601", "Biss"),
	("2602", "26FF", "Biss2"),
	("2700", "2711", "Exset"),
	("2712", "2712", "Derincrypt"),
	("2713", "2714", "Wuhan"),
	("2715", "2715", "Network Broadcast"),
	("2716", "2716", "Bromteck"),
	("2717", "2718", "Logiways"),
	("2719", "2719", "S-Curious"),
	("27A0", "27A4", "Bydesign India"),
	("2800", "2809", "LCS LLC"),
	("2810", "2810", "Deltasat"),
	("4347", "4347", "Crypton"),
	("4348", "4348", "Secure TV"),
	("44A0", "44A0", "Russkiy Mir"),
	("4700", "47FF", "General Instrument/Motorola"),
	("4825", "4825", "ChinaEPG"),
	("4855", "4856", "Intertrust"),
	("4800", "48FF", "Accessgate/Telemann"),
	("4900", "49FF", "Cryptoworks China"),
	("4A10", "4A1F", "Easycas"),
	("4A20", "4A2F", "Alphacrypt"),
	("4A30", "4A3F", "DVN Holdings"),
	("4A40", "4A4F", "ADT"),
	("4A50", "4A5F", "Shenzhen Kingsky"),
	("4A60", "4A6F", "@Sky"),
	("4A70", "4A7F", "Dreamcrypt"),
	("4A80", "4A8F", "THALEScrypt"),
	("4A90", "4A9F", "Runcom"),
	("4AA0", "4AAF", "SIDSA"),
	("4AB0", "4ABF", "Sky Pilot"),
	("4AC0", "4ACF", "Latens"),
	("4AD0", "4AD1", "Xcrypt"),
	("4AD2", "4AD3", "Beijing Digital"),
	("4AD4", "4AD5", "Widevine"),
	("4AD6", "4AD7", "SK Telecom"),
	("4AD8", "4AD9", "Enigma"),
	("4ADA", "4ADA", "Wyplay"),
	("4ADB", "4ADB", "Jinan Taixin"),
	("4ADC", "4ADC", "Logiways"),
	("4ADD", "4ADD", "ATSC SRM"),
	("4ADE", "4ADE", "Cerbercrypt"),
	("4ADF", "4ADF", "Caston"),
	("4AE0", "4AE0", "DRE-Crypt"),
	("4AE1", "4AE1", "DRE-Crypt"),
	("4AE2", "4AE3", "Microsoft"),
	("4AE4", "4AE4", "Coretrust"),
	("4AE5", "4AE5", "IK SATPROF"),
	("4AE6", "4AE6", "Syphermedia"),
	("4AE7", "4AE7", "Guangzhou Ewider"),
	("4AE8", "4AE8", "FG Digital"),
	("4AE9", "4AE9", "Dreamer-i"),
	("4AEA", "4AEA", "Cryptoguard"),
	("4AEB", "4AEB", "Abel"),
	("4AEC", "4AEC", "FTS DVL SRL"),
	("4AED", "4AED", "Unitend"),
	("4AEE", "4AEE", "Bulcrypt"),
	("4AEF", "4AEF", "NetUP"),
	("4AF0", "4AF0", "ABV"),
	("4AF1", "4AF2", "China DTV"),
	("4AF3", "4AF3", "Baustem"),
	("4AF4", "4AF4", "Marlin"),
	("4AF5", "4AF5", "Securemedia"),
	("4AF6", "4AF6", "Tongfang"),
	("4AF7", "4AF7", "MSA"),
	("4AF8", "4AF8", "Griffin"),
	("4AF9", "4AFA", "Beijing Topreal"),
	("4AFB", "4AFB", "NST"),
	("4AFC", "4AFC", "Panaccess"),
	("4AFD", "4AFD", "Comteza"),
	("4B00", "4B02", "Tongfang"),
	("4B03", "4B03", "Duocrypt"),
	("4B04", "4B04", "Great Wall"),
	("4B05", "4B06", "Digicap"),
	("4B07", "4B07", "Wuhan"),
	("4B08", "4B08", "Philips"),
	("4B09", "4B09", "Ambernetas"),
	("4B0A", "4B0B", "Beijing Sumavision"),
	("4B0C", "4B0F", "Sichuan"),
	("4B10", "4B10", "Exterity"),
	("4B11", "4B12", "Merlin/Advanced Digital"),
	("4B13", "4B14", "Microsoft"),
	("4B19", "4B19", "Ridsys"),
	("4B20", "4B22", "Deltasat"),
	("4B23", "4B23", "SkyNLand"),
	("4B24", "4B24", "Prowill"),
	("4B25", "4B25", "Suresoft"),
	("4B26", "4B26", "Unitend"),
	("4B30", "4B31", "VTC"),
	("4B3A", "4B3A", "ipanel"),
	("4B3B", "4B3B", "Jinggangshan"),
	("4B40", "4B41", "Excaf"),
	("4B42", "4B43", "CI Plus"),
	("4B4A", "4B4A", "Topwell"),
	("4B4B", "4B4D", "ABV"),
	("4B50", "4B53", "Safeview India"),
	("4B54", "4B54", "Telelynx"),
	("4B60", "4B60", "Kiwisat"),
	("4B61", "4B61", "O2 Czech"),
	("4B62", "4B62", "GMA"),
	("4B63", "4B63", "redCrypter"),
	("4B64", "4B64", "Samsung/TV Key"),
	("5347", "5347", "GkWare/Streamguru"),
	("5448", "5449", "Gospell Visioncrypt"),
	("5501", "5580", "Griffin"),
	("5581", "55FF", "Bulcrypt"),
	("5601", "5604", "Verimatrix"),
	("5605", "5606", "Sichuan"),
	("5607", "5608", "Viewscenes"),
	("5609", "5609", "Power On"),
	("56A0", "56A0", "Laxmi"),
	("56A1", "56A1", "C-Dot"),
	("56B0", "56B0", "Laxmi"),
	("56D0", "56D1", "redCrypter"),
	("6448", "6449", "Gospell Visioncrypt"),
	("7700", "7704", "DRE-Guard"),
	("7AC8", "7AC8", "Gospell Visioncrypt"),
	("7BE0", "7BE1", "DRE-Crypt"),
	("AA00", "AA01", "Best CAS"),
	("A100", "A1FF", "Ruscrypt"),
	("FFFE", "FFFE", "Trophyaccess")
)

class GlamourAccess(Poll, Converter):
	CAID, PID, BETACAS, IRDCAS, SECACAS, VIACAS, NAGRACAS, CRWCAS, NDSCAS, CONAXCAS, DRCCAS, BISSCAS, BULCAS, VMXCAS, PWVCAS, TBGCAS, TGFCAS, PANCAS, EXSCAS, CGDCAS, VCRCAS = range(21)
	BETAECM, IRDECM, SECAECM, VIAECM, NAGRAECM, CRWECM, NDSECM, CONAXECM, DRCECM, BISSECM, BULECM, VMXECM, PWVECM, TBGECM, TGFECM, PANECM, EXSECM, CGDECM, VCRECM = range(21, 40)
	RUSCAS, CODICAS, AGTCAS, SAMCAS, CAIDINFO, PROV, NET, EMU, CRD, CRDTXT, FTA, CACHE, CRYPTINFO, CAMNAME, ADDRESS, ECMTIME, FORMAT, ECMINFO, SHORTINFO, CASINFO, ISCRYPTED = range(40, 61)
	timespan = 1000

	TYPE_MAP = {
		"CaID": CAID, "Pid": PID, "BetaCaS": BETACAS, "IrdCaS": IRDCAS, "SecaCaS": SECACAS, "ViaCaS": VIACAS,
		"NagraCaS": NAGRACAS, "CrwCaS": CRWCAS, "NdsCaS": NDSCAS, "ConaxCaS": CONAXCAS, "DrcCaS": DRCCAS,
		"BissCaS": BISSCAS, "BulCaS": BULCAS, "VmxCaS": VMXCAS, "PwvCaS": PWVCAS, "TbgCaS": TBGCAS, "TgfCaS": TGFCAS,
		"PanCaS": PANCAS, "ExsCaS": EXSCAS, "RusCaS": RUSCAS, "BetaEcm": BETAECM, "IrdEcm": IRDECM,
		"SecaEcm": SECAECM, "ViaEcm": VIAECM, "NagraEcm": NAGRAECM, "CrwEcm": CRWECM, "NdsEcm": NDSECM,
		"ConaxEcm": CONAXECM, "DrcEcm": DRCECM, "BissEcm": BISSECM, "BulEcm": BULECM, "VmxEcm": VMXECM,
		"PwvEcm": PWVECM, "TbgEcm": TBGECM, "TgfEcm": TGFECM, "PanEcm": PANECM, "ExsEcm": EXSECM,
		"CgdEcm": CGDECM, "VcrEcm": VCRECM, "CodiCaS": CODICAS, "CgdCaS": CGDCAS, "VcrCaS": VCRCAS,
		"AgtCaS": AGTCAS, "SamCaS": SAMCAS, "CaidInfo": CAIDINFO, "ProvID": PROV, "Net": NET, "Emu": EMU,
		"Crd": CRD, "CrdTxt": CRDTXT, "Fta": FTA, "Cache": CACHE, "CryptInfo": CRYPTINFO, "CamName": CAMNAME,
		"Address": ADDRESS, "EcmTime": ECMTIME, "IsCrypted": ISCRYPTED, "ShortInfo": SHORTINFO, "CasInfo": CASINFO,
		"EcmInfo": ECMINFO, "Default": ECMINFO, "": ECMINFO, None: ECMINFO, "%": ECMINFO
	}

	def __init__(self, type):
		Poll.__init__(self)
		Converter.__init__(self, type)
		self.type = self.TYPE_MAP.get(type, self.FORMAT)
		if self.type == self.FORMAT:
			self.sfmt = type[:]

	@cached
	def getBoolean(self):
		service = self.source.service
		info = service and service.info()
		ecm_info = self.ecmfile()
		protocol = str(ecm_info.get("protocol", ""))
		self.poll_interval = self.timespan
		self.poll_enabled = True
		if not info:
			return False
		caids = self.CaidList().strip(", ").split()

		if self.type == self.FTA:
			if not caids and not ecm_info:
				return True
			return "fta" in protocol if ecm_info else False

		if self.type == self.ISCRYPTED:
			return bool(caids)

		caid_ranges = {
			self.BETACAS: [("1702", "1762")],
			self.IRDCAS: [("0600", "06FF")],
			self.SECACAS: [("0100", "01FF")],
			self.VIACAS: [("0500", "05FF")],
			self.NAGRACAS: [("1800", "18FF")],
			self.CRWCAS: [("0D00", "0DFF"), ("4900", "49FF")],
			self.NDSCAS: [("0900", "09FF")],
			self.CONAXCAS: [("0B00", "0BFF")],
			self.DRCCAS: [("4A00", "4AE9"), ("5000", "50FF"), ("7BE0", "7BE1"), ("0700", "07FF"), ("4700", "47FF")],
			self.BISSCAS: [("2600", "26FF")],
			self.BULCAS: [("4AEE", "4AEE"), ("5501", "55FF")],
			self.VMXCAS: [("5600", "5604"), ("1700", "1701"), ("1703", "1721"), ("1723", "1761"), ("1763", "17FF")],
			self.PWVCAS: [("0E00", "0EFF")],
			self.TBGCAS: [("1000", "10FF")],
			self.TGFCAS: [("4B00", "4B09"), ("4AF6")],
			self.PANCAS: [("4AFC")],
			self.EXSCAS: [("2700", "27FF")],
			self.RUSCAS: [("A100", "A1FF"), ("44A0", "44A0")],
			self.CODICAS: [("2200", "22FF")],
			self.CGDCAS: [("4AEA", "4AEA"), ("1EC0", "1ECF")],
			self.VCRCAS: [("5448", "5449"), ("7AC8")],
			self.AGTCAS: [("4800", "48FF")],
			self.SAMCAS: [("4B64", "4B64")],
		}
		if caids or ecm_info:
			for caid in caids:
				for valid_caid_range in caid_ranges.get(self.type, []):
					if isinstance(valid_caid_range, tuple):
						start, end = valid_caid_range
						if start <= caid <= end:
							return True
					elif valid_caid_range == caid:
						return True

			if ecm_info:
				reader = str(ecm_info.get("reader", ""))
				protocol = str(ecm_info.get("protocol", ""))
				frm = str(ecm_info.get("from", ""))
				using = str(ecm_info.get("using", ""))
				source = str(ecm_info.get("source", ""))
				caid = ("%0.4X" % int(ecm_info.get("caid", ""), 16))[:4]
				ecm_caid_ranges = {
					self.BETAECM: ["1702", "1722", "1762"],
					self.IRDECM: [("0600", "06FF")],
					self.SECAECM: [("0100", "01FF")],
					self.VIAECM: [("0500", "05FF")],
					self.NAGRAECM: [("1800", "18FF")],
					self.CRWECM: [("0D00", "0DFF"), ("4900", "49FF")],
					self.NDSECM: [("0900", "09FF")],
					self.CONAXECM: [("0B00", "0BFF")],
					self.DRCECM: [("4A00", "4AE9"), ("5000", "50FF"), ("7BE0", "7BE1"), ("0700", "07FF"), ("4700", "47FF")],
					self.BISSECM: [("2600", "26FF")],
					self.BULECM: [("4AEE"), ("5501", "55FF")],
					self.VMXECM: [("5600", "5604"), ("1700", "1701"), ("1703", "1721"), ("1723", "1761"), ("1763", "17FF")],
					self.PWVECM: [("0E00", "0EFF")],
					self.TBGECM: [("1000", "10FF")],
					self.TGFECM: [("4B00", "4B09"), ("4AF6")],
					self.PANECM: [("4AFC")],
					self.EXSECM: [("2700", "27FF")],
					self.CGDECM: [("4AEA", "4AEA"), ("1EC0", "1ECF")],
					self.VCRECM: [("5448", "5449"), ("7AC8")],
				}
				if self.type in ecm_caid_ranges:
					for valid_caid in ecm_caid_ranges[self.type]:
						if isinstance(valid_caid, tuple):
							if valid_caid[0] <= caid <= valid_caid[1]:
								return True
						elif valid_caid == caid:
							return True

				if int(config.usage.show_cryptoinfo.value) == 0:
					return False

				if self.type == self.CRD:
					return source == "sci" or (source not in {"cache", "net"} and "emu" not in source)

				if self.type == self.CACHE:
					return source == "cache" or reader == "Cache" or "cache" in frm

				if self.type == self.EMU:
					return using == "emu" or source in {"emu", "card"} or reader == "emu" or \
						any(x in source for x in {"card", "emu", "biss", "tb"}) or \
						"constant_cw" in reader or any(x in protocol for x in {"constcw", "static"})

				if self.type == self.NET:
					return source == "net" and all(x not in protocol for x in {"unsupported", "static", "fta"}) and "cache" not in frm

		return False

	boolean = property(getBoolean)

	@cached
	def getText(self):
		ecminfo = ""
		server = ""
		caidlist = self.CaidList()
		caidtxt = "hidden or custom"
		caidname = self.CaidName()
		ecm_info = self.ecmfile()
		ecmpath = self.ecmpath()
		self.poll_interval = self.timespan
		self.poll_enabled = True
		service = self.source.service

		if service:
			info = service.info() if service else None

			if self.type == self.CRYPTINFO:
				if os.path.exists(ecmpath):
					try:
						caid = f"{int(ecm_info.get('caid', ''), 16):04X}"
						return caidname
					except:
						return "Unknown CA Info"
				return "CA Info not available"

			if info:
				caids = list(set(info.getInfoObject(iServiceInformation.sCAIDs)))

				if self.type == self.CAMNAME:
					return self.CamName()

				if self.type == self.CAIDINFO:
					return self.CaidInfo()

				if caids or ecm_info:
					if caids:
						caidtxt = self.CaidTxtList()
						caids = [f"{int(cas):04X}" for cas in caids]

					if ecm_info:
						caid = f"{int(ecm_info.get('caid', ''), 16):04X}"

						if self.type == self.CAID:
							return caid

						pid = f"{int(ecm_info.get('pid', ''), 16):04X}" if ecm_info.get('pid') else ""
						if self.type == self.PID:
							return pid

						prov = f"{int(ecm_info.get('prov', ''), 16):06X}" if ecm_info.get('prov') else ecm_info.get('prov', "")
						if self.type == self.PROV:
							return prov

						ecm_time = ""
						if "ecm time" in ecm_info:
							if "msec" in ecm_info["ecm time"]:
								ecm_time = ecm_info["ecm time"].replace("msec", "ms")
							else:
								ecm_time = f"{ecm_info['ecm time'].replace('.', '').lstrip('0')} ms"
						if self.type == self.ECMTIME:
							return ecm_time

						csi = f"Service with {caidtxt} encryption"
						casi = f"Service with {caidtxt} encryption ({caidlist})"
						protocol = ecm_info.get("protocol", "")
						port = ecm_info.get("port", "")
						source = ecm_info.get("source", "")
						server = ecm_info.get("server", "")

						hop = ecm_info.get("hops", "")
						if hop and hop.isdigit() and int(hop) > 0:
							hop = str(hop)
							hops = f" Hops: {hop}"
						else:
							hops = hop = ""

						system = ecm_info.get("system", "")
						frm = ecm_info.get("from", "")

						if len(frm) > 36:
							frm = f"{frm[:35]}..."

						provider = ecm_info.get("provider", "")
						if provider:
							provider = f"Prov: {provider}"

						reader = ecm_info.get("reader", "")
						if len(reader) > 36:
							reader = f"{reader[:35]}..."

						if self.type == self.CRDTXT:
							return "True" if source == "sci" or (source not in {"cache", "net"} and "emu" not in source) else "False"

						if self.type == self.ADDRESS:
							return server

						if self.type == self.FORMAT:
							ecminfo = ""
							params = self.sfmt.split(" ")
							for param in params:
								if param != "":
									if param[0] != "%":
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
									if len(ecminfo) > 0 and ecminfo[-1] not in ["\t", "\n"]:
										ecminfo += " "
							return ecminfo.rstrip()

						if self.type in [self.ECMINFO, self.SHORTINFO, self.CASINFO]:
								if "fta" in protocol:
									ecminfo = "FTA service"
								elif int(config.usage.show_cryptoinfo.value) > 0:
									if self.type == self.SHORTINFO:
										if source == "emu":
											ecminfo = f"{caid}:{prov} - {source} - {caidname}"
										elif not server and not port:
											ecminfo = f"{caid}:{prov} - {source} - {ecm_time}"
										else:
											try:
												if reader:
													ecminfo = f"{caid}:{prov} - {frm} ({hop}) - {ecm_time}" if hop else f"{caid}:{prov} - {frm} - {ecm_time}"
												else:
													ecminfo = f"{caid}:{prov} - {server} ({hop}) - {ecm_time}" if hop else f"{caid}:{prov} - {server} - {ecm_time}"
											except:
												pass

									elif self.type == self.CASINFO:
										if source == "emu" or not server and not port:
											ecminfo = f"{csi} [{caid}:{prov} - {source} - {ecm_time}]"
										else:
											try:
												if reader:
													ecminfo = f"{csi} [{caid}:{prov} - {reader}@{hop} - {ecm_time}]" if hop else f"{csi} [{caid}:{prov} - {reader} - {ecm_time}]"
												else:
													ecminfo = f"{csi} [{caid}:{prov} - {server}@{hop} - {ecm_time}]" if hop else f"{csi} [{caid}:{prov} - {server} - {ecm_time}]"
											except:
												pass

									elif self.type == self.ECMINFO:
										if source == "emu":
											ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Source: {source}@{frm}  Ecm Time: {ecm_time}"
										elif reader and source == "net" and port:
											ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Reader: {reader}@{frm}  Prtc:{protocol} ({source})  Source: {server}:{port} {hops}  Ecm Time: {ecm_time}  {provider}"
										elif reader and source == "net" and "fta" not in protocol:
											ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Reader: {reader}@{frm}  Ptrc:{protocol} ({source})  Source: {server} {hops}  Ecm Time: {ecm_time}  {provider}"
										elif reader and source != "net":
											ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Reader: {reader}@{frm}  Prtc:{protocol} (local) - {source} {hops}  Ecm Time: {ecm_time}  {provider}"
										elif not server and not port and protocol:
											ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Prtc: {protocol} ({source}) {hops} Ecm Time: {ecm_time}"
										elif not server and not port and not protocol:
											ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Source: {source}  Ecm Time: {ecm_time}"
										else:
											try:
												ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Addr:{server}:{port}  Prtc: {protocol} ({source}) {hops}  Ecm Time: {ecm_time}  {provider}"
											except:
												pass
								else:
									ecminfo = casi

					elif self.type == self.ECMINFO or self.type == self.FORMAT and self.sfmt.count("%") > 3:
						ecminfo = f"Service with {caidtxt} encryption ({caidlist})"
					elif self.type == self.SHORTINFO or self.type == self.CASINFO:
						ecminfo = f"Service with {caidtxt} encryption"
				elif self.type == self.ECMINFO or self.type == self.SHORTINFO or self.type == self.CASINFO or self.type == self.FORMAT and self.sfmt.count("%") > 3:
					ecminfo = "FTA service"
		return ecminfo

	text = property(getText)

	# Helper function for reading lines from a file
	def read_file(self, file_path):
		try:
			with open(file_path) as f:
				return f.readlines()
		except:
			return []

	def CamName(self):
		cam1 = ""
		cam2 = ""
		serlist = None
		camdlist = None
		camdname = []
		sername = []

		# OpenPLI/SatDreamGr
		if os.path.exists("/etc/init.d/softcam") and not os.path.exists("/etc/image-version") or os.path.exists("/etc/init.d/cardserver") and not os.path.exists("/etc/image-version"):
			lines = self.read_file("/etc/init.d/softcam")
			for line in lines:
				if line.startswith("CAMNAME="):
					cam1 = line.split('"')[1]
				elif "echo" in line:
					camdname.append(line)
			if camdname:
				cam2 = camdname[1].split('"')[1]
			camdlist = cam1 if cam1 else cam2
			if not camdlist:
				camdlist = ""
			serlist = self.read_cardserver()
			return f"{serlist} {camdlist}" if camdlist else "No active softcam"

		# OE-A (OpenATV)
		if os.path.exists("/etc/image-version") and not os.path.exists("/etc/.emustart"):
			lines = self.read_file("/etc/enigma2/settings")
			active_softcam = ""
			for line in lines:
				if line.startswith("config.misc.softcams="):
					active_softcam = line.split('=')[1].strip()
					break
			# Alternative search method for softcam name
			if not active_softcam or active_softcam.lower() == "none":
				softcam_init_file = "/etc/init.d/softcam"
				if os.path.exists(softcam_init_file):
					with open(softcam_init_file, "r") as f:
						for line in f:
							if "Short-Description:" in line:
								active_softcam = line.split(":")[1].strip()
								break
			if not active_softcam or active_softcam.lower() in {"nocam", "none"}:
				return "No active softcam"
			active_softcam = active_softcam.capitalize()
			if "oscam" in active_softcam.lower() or "ncam" in active_softcam.lower():
				version_file = "/tmp/.oscam/oscam.version" if "oscam" in active_softcam.lower() else "/tmp/.ncam/ncam.version"
				if os.path.exists(version_file):
					version = self.read_version_from_file(version_file)
					if "oscam" in active_softcam.lower() and "@" in version:
						version = f"v.{version.split('-')[1].split('@')[0]}"
					elif "oscam" in active_softcam.lower() and "svn" in version:
						version = version.split('_')[1]
					return f"{active_softcam} {version}"
			return active_softcam

		# Handle other cases (BLACKHOLE, HDMU, Domica, etc.)
		if os.path.exists("/etc/CurrentDelCamName"):
			camdlist = self.read_file("/etc/CurrentDelCamName")
		elif os.path.exists("/etc/CurrentBhCamName"):
			camdlist = self.read_file("/etc/CurrentBhCamName")
		elif os.path.exists("/etc/BhFpConf"):
			camdlist = self.read_file("/etc/BhCamConf")

		if os.path.exists("/etc/.emustart") and os.path.exists("/etc/image-version"):
			lines = self.read_file("/etc/.emustart")
			if lines:
				return lines[0].split()[0].split("/")[-1]

		# Additional checks for specific systems
		if os.path.exists("/tmp/egami.inf"):
			return self.read_egami_info("/tmp/egami.inf")

		# Others
		if serlist:
			cardserver = self.read_lines(serlist)
		else:
			cardserver = "N/A"
		if camdlist:
			emu = self.read_lines(camdlist)
		else:
			emu = "No active softcam"
		
		return f"{cardserver.split('\n')[0]} {emu.split('\n')[0]}"

	# Helper method to read lines
	def read_lines(self, file_path):
		with open(file_path, "r") as f:
			return f.readlines()

	# Read version from a file
	def read_version_from_file(self, file_path):
		lines = self.read_file(file_path)
		for line in lines:
			if line.startswith("Version:"):
				return line.split(':')[1].strip()
		return ""

	# Helper function for extracting CAID name from a list of ranges
	def get_caid_name(self, caidr):
		for ce in cainfo:
			try:
				if ce[0] <= caidr <= ce[1] or caidr.startswith(ce[0]):
					return ce[2]
			except:
				pass
		return ""

	def Caids(self):
		caids = ""
		service = self.source.service
		if service:
			info = service.info()
			if info:
				caids = list(set(info.getInfoObject(iServiceInformation.sCAIDs)))
		return sorted(caids)

	def CaidList(self):
		caids = self.Caids()
		if caids:
			caidlist = ", ".join(("{:04x}".format(x) for x in caids)).upper()
			return caidlist
		return ""

	def CaidName(self):
		ecm_info = self.ecmfile()
		caidname = ""
		if ecm_info:
			caidr = ("%0.4X" % int(ecm_info.get("caid", ""), 16))[:4]
			caidname = self.get_caid_name(caidr)
		return caidname

	def CaidNames(self):
		caidnames = []
		caids = self.CaidList().strip(",").split()
		if caids:
			for caid in caids:
				for ce in cainfo:
					if ce[0] <= caid <= ce[1] or caid.startswith(ce[0]):
						caid = ce[2]
				caidnames.append(caid)
		return ", ".join(caidnames)

	def CaidTxtList(self):
		caidtxt = ""
		caidnames = self.CaidNames()
		if caidnames:
			unique_names = list(dict.fromkeys(caidnames.split(", ")))
			if len(unique_names) > 1:
				caidtxt = ", ".join(unique_names[:-1]) + " & " + unique_names[-1]
			else:
				caidtxt = unique_names[0]
		return caidtxt

	def CaidInfo(self):
		caids = self.CaidList()
		caidnames = self.CaidNames()
		if caids and caidnames:
			caidlist = f"{caids} ({caidnames})"
			if config.osd.language.value == "el_GR":
				return f"Συστήματα κωδικοποίησης: {caidlist}"
			else:
				return f"Coding systems: {caidlist}"
		elif not caids:
				return "Free to air or no descriptor"

	def ecmpath(self):
		for i in range(7, 0, -1):
			ecm_file = f"/tmp/ecm{i}.info"
			if os.path.exists(ecm_file):
				return ecm_file
		return "/tmp/ecm.info" if os.path.exists("/tmp/ecm.info") else None

	def ecmfile(self):
		global info
		global old_ecm_mtime
		ecmpath = self.ecmpath()
		service = self.source.service
		if not service:
			return info

		try:
			stat = os.stat(ecmpath)
			ecm_mtime = stat.st_mtime
			if not stat.st_size > 0:
				info = {}
				return info
			if ecm_mtime == old_ecm_mtime:
				return info
			old_ecm_mtime = ecm_mtime

			with open(ecmpath, "r") as ecmf:
				ecm = ecmf.readlines()

			if not ecm:
				return info

			for line in ecm:
				line_lower = line.lower()
				x = line_lower.find("msec")
				if x != -1:
					info["ecm time"] = line[:x + 4]
					continue

				item = line.split(":", 1)
				if len(item) <= 1:
					if "caid" not in info:
						x = line_lower.find("caid")
						if x != -1:
							y = line.find(",")
							if y != -1:
								info["caid"] = line[x + 5:y]
					if "pid" not in info:
						x = line_lower.find("pid")
						if x != -1:
							y = line.find(" =")
							z = line.find(" *")
							if y != -1:
								info["pid"] = line[x + 4:y]
							elif z != -1:
								info["pid"] = line[x + 4:z]
					continue

				key, value = item[0].strip().lower(), item[1].strip()

				match key:
					case "provider":
						key = "prov"
						value = value[2:]
					case "ecm pid":
						key = "pid"
					case "response time":
						info["source"] = "net"
						it_tmp = value.split(" ")
						info["ecm time"] = f"{it_tmp[0]} msec"
						if "[" in it_tmp[-1]:
							info["server"] = it_tmp[-1].split("[")[0]
							info["protocol"] = it_tmp[-1].split("[")[1][:-1]
						elif "(" in it_tmp[-1]:
							info["server"] = it_tmp[-1].split("(")[-1].split(":")[0]
							info["port"] = it_tmp[-1].split("(")[-1].split(":")[-1].rstrip(")")
						else:
							key = "source"
							value = "sci"
						if any(x in it_tmp[-1] for x in ["emu", "card", "biss", "tb"]):
							key = "source"
							value = "emu"
					case "hops" | "from" | "system" | "provider":
						value = value.rstrip("\n")
					case "source":
						if value.startswith("net"):
							it_tmp = value.split(" ")
							info["protocol"] = it_tmp[1][1:]
							if ":" in it_tmp[-1]:
								info["server"], info["port"] = it_tmp[-1].split(":", 1)
								info["port"] = info["port"][:-1]
							else:
								try:
									info["server"], info["port"] = it_tmp[3].split(":", 1)
									info["port"] = info["port"][:-1]
								except (IndexError, ValueError):
									info["server"] = info["port"] = ""
							value = "net"
					case "prov":
						if "," in value:
							value = value.split(",")[0]
					case "reader":
						if value == "emu":
							key = "source"
					case "protocol":
						match value:
							case "emu" | "constcw":
								key, value = "source", "emu"
							case "internal":
								key, value = "source", "sci"
							case _:
								info["source"] = "net"
								key = "server"
					case "provid":
						key = "prov"
					case "using":
						match value:
							case "emu" | "sci":
								key = "source"
							case _:
								info["source"] = "net"
								key = "protocol"
					case "address":
						if ":" in value:
							info["server"], value = value.split(":", 1)
							key = "port"
					case _:
						pass

				info[key] = value

		except Exception:
			old_ecm_mtime = None
			info = {}

		return info

	def changed(self, what):
		Converter.changed(self, (self.CHANGED_POLL,))