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
except Exception:
	pass

try:
	config.glamour = ConfigSubsection()
	config.glamour.freely = ConfigText(default="FTA service")
except Exception:
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

	def resetCaches(self):
		global info, old_ecm_mtime
		info = {}
		old_ecm_mtime = None

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
			self.TGFCAS: [("4B00", "4B09"), ("4AF6", "4AF6")],
			self.PANCAS: [("4AFC", "4AFC")],
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
				try:
					caid = ("%0.4X" % int(ecm_info.get("caid", ""), 16))[:4]
				except Exception:
					caid = ""

				if self.type == self.BETAECM and caid in ("1702", "1722", "1762"):
					return True

				ecm_caid_ranges = {
					self.IRDECM: [("0600", "06FF")],
					self.SECAECM: [("0100", "01FF")],
					self.VIAECM: [("0500", "05FF")],
					self.NAGRAECM: [("1800", "18FF")],
					self.CRWECM: [("0D00", "0DFF"), ("4900", "49FF")],
					self.NDSECM: [("0900", "09FF")],
					self.CONAXECM: [("0B00", "0BFF")],
					self.DRCECM: [("4A00", "4AE9"), ("5000", "50FF"), ("7BE0", "7BE1"), ("0700", "07FF"), ("4700", "47FF")],
					self.BISSECM: [("2600", "26FF")],
					self.BULECM: [("4AEE", "4AEE"), ("5501", "55FF")],
					self.VMXECM: [("5600", "5604"), ("1700", "1701"), ("1703", "1721"), ("1723", "1761"), ("1763", "17FF")],
					self.PWVECM: [("0E00", "0EFF")],
					self.TBGECM: [("1000", "10FF")],
					self.TGFECM: [("4B00", "4B09"), ("4AF6", "4AF6")],
					self.PANECM: [("4AFC", "4AFC")],
					self.EXSECM: [("2700", "27FF")],
					self.CGDECM: [("4AEA", "4AEA"), ("1EC0", "1ECF")],
					self.VCRECM: [("5448", "5449"), ("7AC8", "7AC8")],
				}
				if self.type in ecm_caid_ranges:
					for valid_caid_range in ecm_caid_ranges[self.type]:
						if isinstance(valid_caid_range, tuple):
							start, end = valid_caid_range
							if start <= caid <= end:
								return True
						elif valid_caid_range == caid:
							return True

				try:
					show_crypto = int(config.usage.show_cryptoinfo.value)
				except Exception:
					show_crypto = 0

				if show_crypto == 0:
					return False

				if self.type == self.CRD:
					return source == "sci" or (source not in {"cache", "net"} and "emu" not in source)

				if self.type == self.CACHE:
					return source == "cache" or reader == "Cache" or "cache" in frm

				if self.type == self.EMU:
					return using == "emu" or source in {"emu", "card"} or reader == "emu" or any(x in source for x in {"card", "emu", "biss", "tb"}) or "constant_cw" in reader or any(x in protocol for x in {"constcw", "static"})

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
				if ecmpath and os.path.exists(ecmpath):
					try:
						_ = f"{int(ecm_info.get('caid', ''), 16):04X}"
						return caidname
					except Exception:
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
						caids = [f"{int(cas):04X}" for cas in caids]  # форматирование CAID в 4-значный HEX

					if ecm_info:
						try:
							caid = f"{int(ecm_info.get('caid', ''), 16):04X}"  # CAID
						except Exception:
							caid = ""

						if self.type == self.CAID:
							return caid

						# PID
						pid = ""
						if ecm_info.get("pid"):
							try:
								pid = f"{int(ecm_info.get("pid", ''), 16):04X}"
							except Exception:
								pid = ""
						if self.type == self.PID:
							return pid

						# Provider ID (Prov)
						prov = ecm_info.get("prov", "")
						if prov:
							try:
								prov = f"{int(prov, 16):06X}"
							except Exception:
								prov = str(prov)
						if self.type == self.PROV:
							return prov

						ecm_time = ""
						if "ecm time" in ecm_info:
							t = ecm_info["ecm time"]
							if "msec" in t:
								ecm_time = t.replace("msec", "ms")
							else:
								ecm_time = f"{t.replace('.', '').lstrip('0')} ms"
						if self.type == self.ECMTIME:
							return ecm_time

						csi = f"Service with {caidtxt} encryption"
						casi = f"Service with {caidtxt} encryption ({caidlist})"

						protocol = ecm_info.get("protocol", "")
						port = ecm_info.get("port", "")
						source = ecm_info.get("source", "")
						server = ecm_info.get("server", "")

						# Проверка на hops, только если значение > 0
						hop_value = str(ecm_info.get("hops", "")).strip()
						if hop_value.isdigit() and int(hop_value) > 0:
							hops = f" Hops: {hop_value}"
						else:
							hop_value = ""
							hops = ""

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

						try:
							hide_server_attr = getattr(getattr(config, "softcam", None), "hideServerName", None)
							hide_server = bool(hide_server_attr and hide_server_attr.value)
						except Exception:
							hide_server = False

						if hide_server:
							server = ""
							frm = ""
							reader = ""

						if self.type == self.CRDTXT:
							return "True" if source == "sci" or (source not in {"cache", "net"} and "emu" not in source) else "False"

						if self.type == self.ADDRESS:
							return server

						if self.type == self.FORMAT:
							ecminfo = ""
							params = self.sfmt.split(" ")
							for param in params:
								if not param:
									continue
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
								if ecminfo and ecminfo[-1] not in ("\t", "\n"):
									ecminfo += " "
							return ecminfo.rstrip()

						if self.type in (self.ECMINFO, self.SHORTINFO, self.CASINFO):
							try:
								show_crypto = int(config.usage.show_cryptoinfo.value)
							except Exception:
								show_crypto = 0

							if "fta" in protocol:
								ecminfo = "FTA service"
							elif show_crypto > 0:
								if self.type == self.SHORTINFO:
									if source == "emu":
										ecminfo = f"{caid}:{prov} - {source} - {caidname}"
									elif not server and not port:
										ecminfo = f"{caid}:{prov} - {source} - {ecm_time}"
									else:
										try:
											if reader:
												if hop_value:
													ecminfo = f"{caid}:{prov} - {frm} ({hop_value}) - {ecm_time}"
												else:
													ecminfo = f"{caid}:{prov} - {frm} - {ecm_time}"
											else:
												if hop_value:
													ecminfo = f"{caid}:{prov} - {server} ({hop_value}) - {ecm_time}"
												else:
													ecminfo = f"{caid}:{prov} - {server} - {ecm_time}"
										except Exception:
											pass
								elif self.type == self.CASINFO:
									if source == "emu" or not server and not port:
										ecminfo = f"{csi} [{caid}:{prov} - {source} - {ecm_time}]"
									else:
										try:
											if reader:
												if hop_value:
													ecminfo = f"{csi} [{caid}:{prov} - {reader}@{hop_value} - {ecm_time}]"
												else:
													ecminfo = f"{csi} [{caid}:{prov} - {reader} - {ecm_time}]"
											else:
												if hop_value:
													ecminfo = f"{csi} [{caid}:{prov} - {server}@{hop_value} - {ecm_time}]"
												else:
													ecminfo = f"{csi} [{caid}:{prov} - {server} - {ecm_time}]"
										except Exception:
											pass
								elif self.type == self.ECMINFO:
									if source == "emu":
										ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Source: {source}@{frm}  Ecm Time: {ecm_time}"
									elif reader and source == "net" and port:
										ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Reader: {reader}@{frm}  Prtc:{protocol} ({source})  Source: {server}:{port}{hops}  Ecm Time: {ecm_time}  {provider}"
									elif reader and source == "net" and "fta" not in protocol:
										ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Reader: {reader}@{frm}  Ptrc:{protocol} ({source})  Source: {server}{hops}  Ecm Time: {ecm_time}  {provider}"
									elif reader and source != "net":
										ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Reader: {reader}@{frm}  Prtc:{protocol} (local) - {source}{hops}  Ecm Time: {ecm_time}  {provider}"
									elif not server and not port and protocol:
										ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Prtc: {protocol} ({source}){hops} Ecm Time: {ecm_time}"
									elif not server and not port and not protocol:
										ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Source: {source}  Ecm Time: {ecm_time}"
									else:
										try:
											ecminfo = f"CA: {caid}:{prov}  PID:{pid}  Addr:{server}:{port}  Prtc: {protocol} ({source}){hops}  Ecm Time: {ecm_time}  {provider}"
										except Exception:
											pass
							else:
								ecminfo = casi
					elif self.type == self.ECMINFO or (self.type == self.FORMAT and self.sfmt.count("%") > 3):
						ecminfo = f"Service with {caidtxt} encryption ({caidlist})"
					elif self.type in (self.SHORTINFO, self.CASINFO):
						ecminfo = f"Service with {caidtxt} encryption"
				elif self.type in (self.ECMINFO, self.SHORTINFO, self.CASINFO) or (self.type == self.FORMAT and self.sfmt.count("%") > 3):
					try:
						text = config.glamour.freely.value
						ecminfo = text if text.strip() else "FTA service"
					except Exception:
						ecminfo = "FTA service"

		if self.type in (self.ECMINFO, self.SHORTINFO, self.CASINFO):
			ecminfo = self.splitInfoLines(ecminfo, self.type)
		return ecminfo

	text = property(getText)

	def read_file(self, file_path):
		try:
			with open(file_path, "r") as f:
				return f.readlines()
		except Exception:
			return []

	def CamName(self):
		cam1 = ""
		cam2 = ""
		serlist = None
		camdlist = None
		camdname = []
		sername = []

		# OpenPLI/SatDreamGr
		if os.path.exists("/etc/init.d/softcam") and not os.path.exists("/etc/image-version"):
			lines = self.read_file("/etc/init.d/softcam")
			for line in lines:
				if line.startswith("CAMNAME="):
					cam1 = line.split('"')[1]
				elif "echo" in line:
					camdname.append(line)
			if camdname and not cam1:
				cam2 = camdname[1].split('"')[1]
			camdlist = cam1 if cam1 else cam2
			if not camdlist:
				camdlist = ""
			if os.path.exists("/etc/init.d/cardserver"):
				lines = self.read_file("/etc/init.d/cardserver")
				for line in lines:
					if line.startswith("CAMNAME="):
						serlist = line.split('"')[1]
					elif "echo" in line:
						sername.append(line)
				if sername and not serlist:
					serlist = sername[1].split('"')[1]
			try:
				if serlist:
					return f"{serlist} {camdlist}"
			except Exception:
				pass
			return camdlist

		# OpenVix, OpenATV, OpenESI, PurE2
		if os.path.exists("/etc/image-version") and not os.path.exists("/etc/.emustart"):
			try:
				with open("/etc/enigma2/settings", "r") as f:
					for line in f:
						if "config.misc.softcams=" in line:
							active_softcam = line.split("=", 1)[1].strip()
							if not active_softcam or active_softcam.lower() == "none":
								if os.path.exists("/etc/init.d/softcam"):
									with open("/etc/init.d/softcam", "r") as f2:
										for line in f2:
											if "Short-Description:" in line:
												active_softcam = line.split(":", 1)[1].strip()
												break
							if not active_softcam or active_softcam.lower() in ("nocam", "none"):
								return "No active softcam"
							active_softcam_cap = active_softcam.capitalize()
							lower_softcam = active_softcam.lower()
							if "oscam" in lower_softcam or "ncam" in lower_softcam:
								if "oscam" in lower_softcam:
									version_file = "/tmp/.oscam/oscam.version"
								else:
									version_file = "/tmp/.ncam/ncam.version"
								if os.path.exists(version_file):
									with open(version_file, "r") as vf:
										version = ""
										for line in vf:
											if "Version:" in line:
												version = line.split(":", 1)[1].strip()
												break
									if version:
										if "oscam" in active_softcam.lower():
											if "@" in version:
												version = f"v.{version.split('-')[1].split('@')[0]}"
											elif "svn" in version:
												version = version.split("_")[1]
										active_softcam_cap = f"{active_softcam_cap} {version}"
							return active_softcam_cap
			except Exception:
				pass
			return "No active softcam"

		# BlackHole/Pli-based images
		if os.path.exists("/etc/CurrentDelCamName"):
			camdlist = self.read_file("/etc/CurrentDelCamName")
		elif os.path.exists("/etc/CurrentBhCamName"):
			camdlist = self.read_file("/etc/CurrentBhCamName")
		elif os.path.exists("/etc/BhFpConf"):
			camdlist = self.read_file("/etc/BhCamConf")
		else:
			camdlist = None

		# Egami
		if os.path.exists("/etc/.emustart") and os.path.exists("/etc/image-version"):
			try:
				with open("/etc/.emustart", "r") as f:
					camdlist = f.readline().split()[0].split("/")[-1]
				return camdlist
			except Exception:
				pass

		if os.path.exists("/tmp/egami.inf"):
			try:
				with open("/tmp/egami.inf", "r") as f:
					return f.readline().strip()
			except Exception:
				pass

		if serlist:
			try:
				with open(serlist, "r") as f:
					cardserver = f.read()
			except Exception:
				cardserver = "N/A"
		else:
			cardserver = "N/A"
		if camdlist:
			try:
				emu = "".join(camdlist)
			except Exception:
				emu = "No active softcam"
		else:
			emu = "No active softcam"
		try:
			card_line = cardserver.split("\n")[0]
		except Exception:
			card_line = ""
		try:
			emu_line = emu.split("\n")[0]
		except Exception:
			emu_line = ""
		return f"{card_line} {emu_line}"

	def get_caid_name(self, caidr):
		for ce in cainfo:
			try:
				if ce[0] <= caidr <= ce[1] or caidr.startswith(ce[0]):
					return ce[2]
			except Exception:
				pass
		return ""

	def formatProviderForCAID(self, caid_hex, provid):
		if not caid_hex:
			return ""
		if not provid:
			return caid_hex
		provid = str(provid).upper().replace("0X", "").strip()
		if provid in ("0000", "FFFF", "000000", "FFFFFF"):
			return caid_hex
		if caid_hex.startswith("01"):
			return f"{caid_hex}:{provid[-4:]}"
		if caid_hex.startswith("18"):
			return f"{caid_hex}:{provid[-4:]}"
		if caid_hex.startswith("05"):
			return f"{caid_hex}:{provid[-6:]}"
		return caid_hex

	def CaidList(self):
		service = self.source.service
		value = ""
		if service:
			info = service.info()
			if info:
				caidpids = info.getInfoObject(iServiceInformation.sCAIDPIDs)
				if caidpids:
					results = []
					for entry in caidpids:
						try:
							caid, pid, provid = entry
						except Exception:
							continue
						try:
							caid_hex = f"{int(caid):04X}"
						except Exception:
							try:
								caid_hex = f"{int(str(caid), 16):04X}"
							except Exception:
								continue
						provid_str = ""
						if isinstance(provid, str):
							provid_str = provid.strip()
						elif provid not in (None, ""):
							try:
								provid_str = f"{int(provid):X}"
							except Exception:
								provid_str = ""
						formatted = self.formatProviderForCAID(caid_hex, provid_str)
						if formatted:
							results.append(formatted)
					if results:
						unique = sorted(set(results))
						value = ", ".join(unique)
						return value

		caids = self.Caids()
		if caids:
			caidlist = ", ".join(("{:04x}".format(x) for x in caids)).upper()
			return caidlist

		return ""

	def CaidName(self):
		ecm_info = self.ecmfile()
		if ecm_info:
			try:
				caidr = ("%0.4X" % int(ecm_info.get("caid", ""), 16))[:4]
				return self.get_caid_name(caidr)
			except Exception:
				return ""
		return ""

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
			caidnames = caidnames.split(", ")
			caidnames = list(dict.fromkeys(caidnames))
			if len(caidnames) > 1:
				caidtxt = ", ".join(caidnames[:-1]) + " & " + caidnames[-1]
			else:
				caidtxt = caidnames[0]
		return caidtxt

	def Caids(self):
		caids = []
		service = self.source.service
		if service:
			info = service.info()
			if info:
				try:
					caids = list(set(info.getInfoObject(iServiceInformation.sCAIDs)))
				except Exception:
					caids = []
		caids.sort()
		return caids

	def CaidInfo(self):
		caids = self.CaidList()
		caidnames = self.CaidNames()
		if caids and caidnames:
			caidlist = f"{caids} ({caidnames})"
			try:
				if config.osd.language.value == "el_GR":
					return f"Συστήματα κωδικοποίησης: {caidlist}"
			except Exception:
				pass
			return f"Coding systems: {caidlist}"
		elif not caids:
			return "Free to air or no descriptor"

	def splitInfoLines(self, text, info_type):
		try:
			if not text:
				return text
			try:
				mode = int(config.usage.show_cryptoinfo.value)
			except Exception:
				return text
			if mode != 2:
				return text
			if info_type == self.ECMINFO:
				for key in ["  Reader:", "  Addr:", "  Prtc:", "  Ptrc:", "  Source:", "  Ecm Time:"]:
					idx = text.find(key)
					if idx != -1:
						return text[:idx].rstrip() + "\n" + text[idx + 2:].lstrip()
				return text
			if info_type in (self.SHORTINFO, self.CASINFO):
				sep = " - "
				idx = text.rfind(sep)
				if idx != -1:
					return text[:idx].rstrip() + "\n" + text[idx + 1:].lstrip()
			return text
		except Exception:
			return text

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
		if not service or not ecmpath:
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
				info = {}
				return info

			info = {}

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
							info["port"] = it_tmp[-1].split("(")[-1].split(":")[-1][:-1]
						else:
							key = "source"
							value = "sci"
						if "emu" in it_tmp[-1] or "card" in it_tmp[-1] or "biss" in it_tmp[-1] or "tb" in it_tmp[-1]:
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
		try:
			reason = what[0]
		except Exception:
			reason = None

		service = getattr(self.source, "service", None)
		if not service:
			Converter.changed(self, what)
			return

		if reason != self.CHANGED_POLL:
			self.resetCaches()

		Converter.changed(self, (self.CHANGED_POLL,))
