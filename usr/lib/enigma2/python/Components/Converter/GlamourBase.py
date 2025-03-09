#GlamourBase converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll
from ServiceReference import ServiceReference, resolveAlternate 
from enigma import eAVControl, iServiceInformation, iPlayableService, iPlayableServicePtr, eServiceCenter
from Tools.Transponder import ConvertToHumanReadable
from Components.config import config
import os.path
import re

def sp(text):
	if text:
		text += " "
	return text

# codec map
codecs = {
	-1: "N/A",
	0: "MPEG2",
	1: "AVC",
	2: "H263",
	3: "VC1",
	4: "MPEG4-VC",
	5: "VC1-SM",
	6: "MPEG1",
	7: "HEVC",
	8: "VP8",
	9: "VP9",
	10: "XVID",
	11: "N/A 11",
	12: "N/A 12",
	13: "DIVX 3.11",
	14: "DIVX 4",
	15: "DIVX 5",
	16: "AVS",
	17: "VCC",
	18: "VP6",
	19: "SPARK",
	20: "VCC",
}

satnames = (
	(179.7, 180.3, "Intelsat 18"),
	(177.7, 178.3, "Intelsat 10"),
	(175.5, 176.5, "NSS 11"),
	(173.5, 174.5, "Eutelsat 174A"),
	(171.7, 172.3, "Eutelsat 172B"),
	(168.7, 169.3, "Horizons 3e"),
	(166.7, 167.5, "Luch 5A"),
	(165.7, 166.3, "Intelsat 19"),
	(163.7, 164.3, "Optus 10"),
	(162.7, 163.4, "ChinaSat 19"),
	(161.7, 162.3, "Superbird B3"),
	(159.7, 160.3, "Optus D2"),
	(158.7, 159.3, "ABS 6"),
	(156.7, 157.5, "Intelsat 1R"),
	(155.7, 156.3, "Optus D3/10"),
	(153.7, 154.4, "JCSat 2B"),
	(151.7, 152.3, "Optus D1"),
	(150.4, 150.8, "BRIsat"),
	(149.7, 150.3, "JCSat 1C"),
	(145.7, 146.3, "Nusantara Satu"),
	(144.7, 145.4, "Express AMU7"),
	(143.7, 144.3, "Superbird C2"),
	(142.7, 143.3, "Inmarsat-4F1"),
	(141.7, 142.3, "Apstar 9"),
	(139.7, 140.4, "Express AM5/AT2"),
	(137.7, 138.3, "Telstar 18 Vantage"),
	(135.7, 136.4, "JCSat 16"),
	(133.7, 134.3, "Apstar 6C"),
	(131.7, 132.3, "Vinasat 1/2 & JCSat 5A"),
	(130.4, 130.8, "ChinaSat 6C"),
	(129.7, 130.3, "ChinaSat 2D"),
	(128.4, 128.8, "LaoSat 1"),
	(127.7, 128.3, "JCSat 3A"),
	(124.7, 125.3, "ChinaSat 6D"),
	(123.7, 124.3, "JCSat 4B"),
	(120.7, 122.5, "AsiaSat 9"),
	(119.8, 120.3, "AsiaSat 6 & Thaicom 7"),
	(118.8, 119.7, "Thaicom & 4Bangabandhu 1"),
	(117.8, 118.3, "Telkom 3S"),
	(115.8, 116.3, "KoreaSat 6/7"),
	(115.3, 115.7, "ChinaSat 6E"),
	(112.7, 113.3, "KoreaSat 5/5A"),
	(110.3, 110.8, "ChinaSat 10"),
	(109.7, 110.2, "BSat 3A/3C/4A & JCSat 110A"),
	(107.5, 108.5, "SES 7/9 & Telkom 4"),
	(105.3, 105.8, "AsiaSat 7"),
	(104.8, 105.1, "Asiastar 1"),
	(103.4, 103.7, "ChinaSat 2C"),
	(102.7, 103.3, "Express AMU3"),
	(101.1, 101.7, "Chinasat 9B"),
	(100.0, 100.7, "AsiaSat 5"),
	(98.5, 98.8, "Thuraya 3"),
	(97.8, 98.4, "Chinasat 11"),
	(96.8, 97.7, "GSat 9"),
	(96.2, 96.7, "Express 103"),
	(94.7, 95.3, "SES 8/12"),
	(93.0, 93.8, "GSat 15/17"),
	(92.0, 92.5, "ChinaSat 9"),
	(91.3, 91.8, "Measat 3B/3D"),
	(88.8, 90.3, "Yamal 401"),
	(87.8, 88.3, "ST 2"),
	(87.2, 87.7, "ChinaSat 12"),
	(86.2, 86.8, "Kazsat 2"),
	(84.8, 85.5, "Intelsat 15"),
	(82.8, 83.3, "GSat 10/24/30"),
	(79.8, 80.4, "Express 80"),
	(78.3, 78.8, "Thaicom 6/8"),
	(76.3, 76.8, "Apstar 7"),
	(74.7, 75.4, "ABS 2/2A"),
	(73.7, 74.4, "GSat 18"),
	(71.7, 72.4, "Intelsat 22"),
	(70.3, 70.8, "Eutelsat 70B"),
	(69.8, 70.2, "Blagovest 3"),
	(68.3, 68.8, "Intelsat 20/36"),
	(65.8, 66.3, "Intelsat 17"),
	(64.8, 65.3, "Amos 4"),
	(63.8, 64.4, "Intelsat 906 & Inmarsat-4F2"),
	(63.2, 63.6, "Astra 1G"),
	(62.8, 63.1, "G-Sat 7A"),
	(62.4, 62.7, "Inmarsat GX1"),
	(61.7, 62.3, "Intelsat 39"),
	(60.8, 61.2, "ABS 4"),
	(60.2, 60.4, "WGS 2"),
	(59.9, 60.1, "Intelsat 33e"),
	(59.4, 59.8, "Ovzon 3"),
	(58.3, 58.7, "KazSat 3"),
	(56.8, 57.3, "NSS 12"),
	(56.4, 56.7, "Inmarsat GX4"),
	(55.7, 56.3, "Express AT1"),
	(55.0, 55.4, "Yamal 402 & GSat 8"),
	(54.6, 54.9, "Yamal 402"),
	(52.9, 53.3, "Express AM6"),
	(52.7, 52.8, "Skynet 5D"),
	(52.3, 52.6, "Al Yah 1"),
	(51.8, 52.2, "TurkmenÄlem/MonacoSat"),
	(51.2, 51.7, "Belintersat 1"),
	(50.3, 50.7, "Thaicom 9A"),
	(49.7, 50.2, "Türksat 4B"),
	(48.7, 49.3, "Yamal 601"),
	(47.8, 48.3, "GSat 19/31"),
	(47.8, 48.3, "Eutelsat Quantum & GSat 12"),
	(47.6, 47.7, "Al Yah 2"),
	(45.7, 46.3, "AzerSpace 1"),
	(44.7, 45.3, "AzerSpace 2, Intelsat 38 & Cosmos 2520"),
	(43.7, 44.3, "Thuraya 2"),
	(42.4, 42.7, "Nigcomsat 1R"),
	(41.7, 42.3, "Türksat 3A/4A/5B/6A"),
	(39.8, 40.3, "Express AM7"),
	(38.7, 39.3, "HellasSat 3/4"),
	(37.9, 38.5, "Paksat 1R"),
	(37.6, 37.8, "Athena Fidus"),
	(36.8, 37.3, "Sicral 2"),
	(35.7, 36.3, "Eutelsat 36D & Express AMU1"),
	(32.9, 33.3, "Eutelsat 33F"),
	(32.6, 32.8, "Intelsat 28"),
	(31.4, 31.8, "Astra 5B"),
	(31.1, 31.3, "Hylas 2/3"),
	(30.7, 31.0, "Türksat 5A"),
	(30.2, 30.6, "Arabsat 5A/6A"),
	(28.0, 28.8, "Astra 2E/2F/2G"),
	(25.2, 26.3, "Badr 7,8 & Es'hail 1/2"),
	(24.3, 24.8, "Skynet 5B"),
	(23.0, 23.8, "Astra 3B/3C"),
	(21.4, 21.8, "Eutelsat 21B"),
	(20.8, 21.2, "AfriStar 1"),
	(19.8, 20.5, "Arabsat 5C"),
	(18.8, 19.5, "Astra 1M/1N/1P"),
	(16.6, 17.3, "Amos 17"),
	(15.6, 16.3, "Eutelsat 16A"),
	(12.7, 13.5, "HotBird 13F/13G"),
	(11.5, 11.9, "Sicral 1B"),
	(9.7, 10.3, "Eutelsat 10B"),
	(8.7, 9.3, "Eutelsat 9B & Ka-Sat 9A"),
	(6.7, 7.3, "Eutelsat 7B/7C"),
	(5.7, 6.3, "WGS 1"),
	(4.5, 5.4, "Astra 4A & SES 5"),
	(3.0, 3.6, "Eutelsat 3B"),
	(2.5, 2.9, "Rascom QAF 1R"),
	(1.4, 2.4, "BulgariaSat 1"),
	(-0.5, -1.2, "Thor 5/6/7 & Intelsat 10-02"),
	(-2.7, -3.3, "ABS 3A"),
	(-3.7, -4.4, "Amos 7"),
	(-4.7, -5.4, "Eutelsat 5WB"),
	(-6.7, -7.2, "Nilesat 201/301 & Eutelsat 7WA"),
	(-7.3, -7.4, "Eutelsat 7 West A"),
	(-7.5, -7.7, "Eutelsat 7WA/8WB"),
	(-7.8, -8.3, "Eutelsat 8 West B"),
	(-10.7, -11.3, "Express AM44"),
	(-11.8, -12.2, "WGS 9"),
	(-12.3, -12.8, "Eutelsat 12 West G"),
	(-13.8, -14.3, "Express AM8"),
	(-14.8, -15.3, "Telstar 12 Vantage"),
	(-15.8, -16.3, "Luch 5B"),
	(-17.8, -18.3, "Intelsat 37e"),
	(-19.8, -20.3, "NSS 7"),
	(-21.8, -22.4, "SES 4"),
	(-24.2, -24.6, "Intelsat 905"),
	(-24.7, -25.2, "AlcomSat 1"),
	(-27.2, -27.8, "Intelsat 901"),
	(-29.3, -29.7, "Intelsat 904"),
	(-29.8, -30.5, "Hispasat 30W-5/30W-6"),
	(-31.2, -31.8, "Intelsat 25"),
	(-33.3, -33.7, "Hylas 4"),
	(-34.2, -34.8, "Intelsat 35e"),
	(-35.7, -36.3, "Hispasat 36W-1"),
	(-37.2, -37.7, "Telstar 11N & NSS 10"),
	(-40.2, -40.8, "SES 6"),
	(-42.7, -43.5, "Sky Brasil 1"),
	(-44.7, -45.3, "Intelsat 14"),
	(-47.2, -47.8, "SES 14"),
	(-49.7, -50.4, "Intelsat 9/902"),
	(-52.7, -53.3, "Intelsat 23"),
	(-53.7, -54.3, "Inmarsat 3F5"),
	(-54.7, -55.2, "Inmarsat GX2"),
	(-55.3, -55.8, "Intelsat 34"),
	(-57.7, -58.3, "Intelsat 21"),
	(-59.7, -61.3, "Amazonas 2/3/5"),
	(-61.4, -61.7, "EchoStar 16"),
	(-62.8, -63.2, "Telstar 14R"),
	(-64.7, -65.3, "Eutelsat 65WA & Star One C2"),
	(-66.7, -67.5, "SES 10"),
	(-67.7, -68.3, "Echostar 23"),
	(-69.7, -70.3, "Star One C4/D2"),
	(-71.5, -72.3, "Arsat 1"),
	(-72.4, -72.8, "Nimiq 5"),
	(-73.7, -74.3, "Hispasat 74W-1"),
	(-74.7, -75.3, "Star One C3"),
	(-76.0, -76.5, "Intelsat 16"),
	(-76.7, -77.3, "QuetzSat 1"),
	(-78.5, -79.2, "Sky Mexico 1"),
	(-80.7, -81.3, "Arsat 2"),
	(-81.7, -82.3, "Nimiq 4"),
	(-82.7, -83.3, "AMC 18"),
	(-83.7, -84.3, "Star One D1"),
	(-84.7, -85.5, "Galaxy 17"),
	(-86.0, -86.4, "Sirius FM-5"),
	(-86.7, -87.5, "SES 2 & TKSat 1"),
	(-88.7, -89.3, "Galaxy 28/36"),
	(-90.7, -91.3, "Nimiq 6 & Galaxy 32"),
	(-92.7, -93.4, "Galaxy 35"),
	(-94.7, -95.4, "Galaxy 3C & Intelsat 30/31"),
	(-96.7, -97.4, "Galaxy 19"),
	(-97.5, -97.9, "Inmarsat 4F3"),
	(-98.8, -99.5, "Galaxy 16 & T11/T14"),
	(-100.7, -101.4, "SES 1 & T9S/T16"),
	(-102.9, -103.4, "SES 3/18 & T10/T12"),
	(-104.7, -105.4, "AMC 15, SES 11 & Echostar 105"),
	(-107.2, -107.6, "Anik F1R/G1"),
	(-109.7, -110.4, "Echostar 10/11"),
	(-110.8, -111.5, "Anik F2"),
	(-112.7, -113.4, "Eutelsat 113 West A"),
	(-114.6, -115.4, "Eutelsat 115 West B"),
	(-115.8, -116.3, "Sirius FM-6"),
	(-116.6, -117.4, "Eutelsat 117 West A/B"),
	(-118.7, -119.4, "Anik F3, T8 & Echostar 14"),
	(-120.7, -121.4, "Galaxy 31"),
	(-122.7, -123.4, "Galaxy 18"),
	(-124.7, -125.4, "Galaxy 30"),
	(-126.7, -127.4, "Galaxy 37 & Horizons 4"),
	(-128.7, -129.4, "SES 15"),
	(-130.7, -131.4, "SES 21"),
	(-132.7, -133.4, "Galaxy 33"),
	(-134.7, -135.4, "SES 19"),
	(-138.7, -139.4, "SES 22"),
	(-168.7, -169.4, "NSS 6"),
	(-176.7, -177.4, "NSS 9")
)

class GlamourBase(Poll, Converter, object):
	TYPE_MAP = {
		"FreqInfo": 0, "Orbital": 1, "ResCodec": 2,
		"PidInfoDec": 3, "PidInfoHex": 4, "PidInfoDecHex": 5,
		"HDRInfo": 6, "VideoCodec": 7, "Fps": 8, "VideoSize": 9,
		"Is2160": 10, "Is1440": 11, "Is1080": 12, "Is720": 13,
		"Is576": 14, "Is480": 15, "Is360": 16, "Is288": 17,
		"Is240": 18, "Is144": 19, "IsProgressive": 20, "IsInterlaced": 21,
		"StreamUrl": 22, "StreamType": 23, "IsStreaming": 24,
		"HasMPEG2": 25, "HasAVC": 26, "HasH263": 27, "HasVC1": 28,
		"HasMPEG4VC": 29, "HasHEVC": 30, "HasMPEG1": 31, "HasVP8": 32,
		"HasVP9": 33, "HasVP6": 34, "HasDIVX": 35, "HasXVID": 36,
		"HasSPARK": 37, "HasAVS": 38, "HasVCC": 39, "IsSDR": 40,
		"IsHDR": 41, "IsHDR10": 42, "IsHLG": 43
	}
	for key, value in TYPE_MAP.items():
		locals()[key.upper()] = value

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.poll_interval = 1000
		self.poll_enabled = True
		self.list = []
		self.tp = None
		self.tpinfo = None
		self.tpDataUpdate = None
		self.type = self.TYPE_MAP.get(type, 0)

######### COMMON VARIABLES #################
	def _read_value(self, path, base=16):
		try:
			with open(path, "r") as f:
				return int(f.read().strip(), base)
		except (OSError, ValueError):
			return None

	def videowidth(self, info):
		width = self._read_value("/proc/stb/vmpeg/0/xres")
		if width is None or width in {-1, 4294967295}:
			width = eAVControl.getInstance().getResolutionX(0)
		return width if width not in {-1, 4294967295} else ""

	def videoheight(self, info):
		height = self._read_value("/proc/stb/vmpeg/0/yres")
		if height is None or height in {-1, 4294967295}:
			height = eAVControl.getInstance().getResolutionY(0)
		return height if height not in {-1, 4294967295} else ""

	def proginfo(self, info):
		progrs = self._read_value("/proc/stb/vmpeg/0/progressive")
		if progrs is None or progrs == -1:
			progrs = eAVControl.getInstance().getProgressive()
		return "p" if progrs == 1 else "i" if progrs == 0 else ""

	def videosize(self, info):
		xres, yres, prog = self.videowidth(info), self.videoheight(info), self.proginfo(info)
		return f"{xres}x{yres}{prog}" if xres and yres and prog else ""

	def framerate(self, info):
		fps = self._read_value("/proc/stb/vmpeg/0/framerate", base=10)
		if fps is None or fps <= 0 or fps == -1:
			fps = eAVControl.getInstance().getFrameRate(0)
		return f"{fps / 1000:.3f}".rstrip("0").rstrip(".") + " fps" if fps and fps != -1 else ""


	def videocodec(self, info):
		vcodec = codecs.get(info.getInfo(iServiceInformation.sVideoType), "N/A")
		return vcodec

	def hdr(self, info):
		gamma_map = {0: "SDR", 1: "HDR", 2: "HDR10", 3: "HLG"}
		gamma = gamma_map.get(info.getInfo(iServiceInformation.sGamma), "")
		return gamma

	def frequency(self, tp):
		freq = tp.get("frequency", 0) + 500
		return str(freq // 1000) if freq else ""

	def terrafreq(self, tp):
		return str((tp.get("frequency", 0) + 1) // 1000000) if tp else ""

	def channel(self, tpinfo):
		return str(tpinfo.get("channel", ""))

	def symbolrate(self, tp):
		return str(tp.get("symbol_rate", 0) // 1000) if tp else ""

	def polarization(self, tpinfo):
		return str(tpinfo.get("polarization_abbreviation", ""))

	def fecinfo(self, tpinfo):
		return str(tpinfo.get("fec_inner", ""))

	def tunernumber(self, tpinfo):
		return str(tpinfo.get("tuner_number", ""))

	def system(self, tpinfo):
		return str(tpinfo.get("system", ""))

	def modulation(self, tpinfo):
		return str(tpinfo.get("modulation", ""))

	def constellation(self, tpinfo):
		return str(tpinfo.get("constellation", ""))

	def tunertype(self, tp):
		return str(tp.get("tuner_type", "")) if tp else ""

	def terrafec(self, tpinfo):
		return f"LP:{tpinfo.get('code_rate_lp', '')} HP:{tpinfo.get('code_rate_hp', '')} GI:{tpinfo.get('guard_interval', '')}"

	def plpid(self, tpinfo):
		plpid = tpinfo.get("plp_id", 0)
		return f"PLP ID:{plpid}" if plpid not in (None, -1) else ""

	def t2mi_info(self, tpinfo):
		t2mi_id = tpinfo.get("t2mi_plp_id")
		t2mi_pid = tpinfo.get("t2mi_pid")
		if t2mi_id in (None, -1) or t2mi_pid == 0:
			return ""
		t2mi_id = f"T2MI PLP {t2mi_id}" if t2mi_id is not None else ""
		t2mi_pid = f"PID {t2mi_pid}" if t2mi_pid not in (None, "None") else ""
		return sp(t2mi_id) + sp(t2mi_pid)

	def multistream(self, tpinfo):
		isid = str(tpinfo.get("is_id", 0))
		plscode = str(tpinfo.get("pls_code", 0))
		plsmode = str(tpinfo.get("pls_mode", "None"))
		if plsmode in ("None", "Unknown"):
			plsmode = ""
		if plsmode in ("Gold", "Root", "Combo") and plscode == "0":
			plsmode = ""
		isid = "" if isid in ("None", "-1", "0") else f"IS:{isid}"
		plscode = "" if plscode in ("None", "-1", "0") else plscode
		if not any([isid, plscode, plsmode]):
			return ""
		return sp(isid) + sp(plsmode) + sp(plscode)
 
	def satname(self, tp):
		sat = "Satellite:"
		orb = int(tp.get("orbital_position"))
		orbe = orb / 10.0
		orbw = (orb - 3600) / 10.0
		for min_pos, max_pos, name in satnames:
			if min_pos <= orbe <= max_pos or max_pos <= orbw <= min_pos:
				return name
		try:
			with open("/etc/tuxbox/satellites.xml", "r", encoding="utf-8") as f:
				for line in f:
					match = re.search(r'<sat name="(.*?)" position="(-?\d+)"', line)
					if match and int(match.group(2)) == orb:
						return match.group(1)
		except Exception:
			pass
		return sat

	def orbital(self, tp):
		orbp = tp.get("orbital_position", 0)
		if orbp > 1800:
			return f"{(3600 - orbp) / 10:.1f}°W"
		return f"{orbp / 10:.1f}°E"

	def reference(self, info):
		ref = info.getInfoString(iServiceInformation.sServiceref).lower()
		if "%3a/" in ref or ":/" in ref:
			return ref.replace("%3a", ":")

	def streamtype(self, info):
		ref = self.reference(info)
		if not ref:
			return ""
		if ref.startswith("1:0:"):
			if "0.0.0.0:" in ref or "127.0.0.1:" in ref or "localhost:" in ref:
				return "Internal TS Relay"
			if "%3a/" in ref:
				return "IPTV/TS Stream"
			if ref.startswith("1:134:"):
				return "Alternative"
		else:
			return "IPTV/Non-TS Stream"
		return ""

	def streamurl(self, info):
		streamref = info.getInfoString(iServiceInformation.sServiceref).lower()
		if "%3a/" in streamref or ":/" in streamref:
			streamurl = streamref.split(":")[10].replace("%3a", ":")
			return f"{streamurl[:79]}..." if len(streamurl) > 80 else streamurl
		return ""

	def format_pid(self, pid, prefix, mode):
		if pid < 0 or mode is None:
			return ""
		decval = f"{pid:04d}"
		hexval = f"{pid:04X}"
		formats = {
			"Dec": f"{prefix}:{decval}",
			"Hex": f"{prefix}:{hexval}",
			"DecHex": f"{prefix}:{decval}({hexval})"
		}
		return formats.get(mode, "")

	@cached
	def getText(self):
		service = self.source.service
		if service is None:
			return ""
		info = service and service.info()
		if not info:
			return ""
		if self.tpDataUpdate:
			feinfo = service.frontendInfo()
			if feinfo:
				self.tp = feinfo.getAll(config.usage.infobar_frontend_source.value == "settings")
				if self.tp:
					self.tpinfo = ConvertToHumanReadable(self.tp)
		tp = self.tp
		if not tp:
			tp = info.getInfoObject(iServiceInformation.sTransponderData)
			if tp is None:
				return ""
			tpinfo = ConvertToHumanReadable(tp)
		else:
			tpinfo = self.tpinfo

		vpid = info.getInfo(iServiceInformation.sVideoPID)
		apid = info.getInfo(iServiceInformation.sAudioPID)
		sid = info.getInfo(iServiceInformation.sSID)
		pcr = info.getInfo(iServiceInformation.sPCRPID)
		pmt = info.getInfo(iServiceInformation.sPMTPID)
		tsid = info.getInfo(iServiceInformation.sTSID)
		onid = info.getInfo(iServiceInformation.sONID)

		if self.type == self.FREQINFO:
			ref = self.reference(info)
			if ref:
				return self.streamurl(info)
			tunertype = self.tunertype(tp)
			if "DVB-S" in tunertype:
				satf = f"{self.frequency(tp)} {self.polarization(tpinfo)} {self.system(tpinfo)} {self.modulation(tpinfo)} {self.symbolrate(tp)} {self.fecinfo(tpinfo)}"
				if any(k in tpinfo for k in ("is_id", "pls_code", "pls_mode", "t2mi_plp_id")):
					return sp(satf) + self.multistream(tpinfo) + self.t2mi_info(tpinfo)
				return satf
			if "DVB-C" in tunertype:
				return f"{self.frequency(tp)} MHz {self.modulation(tpinfo)} SR: {self.symbolrate(tp)} FEC: {self.fecinfo(tpinfo)}"
			if "DVB-T" in tunertype:
				terf = f"{self.channel(tpinfo)} ({self.terrafreq(tp)} MHz)  {self.constellation(tpinfo)}  {self.terrafec(tpinfo)}"
				if "DVB-T2" in tunertype:
					return sp(terf) + self.plpid(tpinfo)
				return terf
			if "ATSC" in tunertype:
				return f"{self.terrafreq(tp)} MHz {self.modulation(tpinfo)}"
			return ""

		if self.type == self.ORBITAL:
			ref = self.reference(info)
			if ref:
				return self.streamtype(info)
			tunertype = self.tunertype(tp)
			if "DVB-S" in tunertype:
				return f"{self.satname(tp)} ({self.orbital(tp)})"
			if any(t in tunertype for t in ("DVB-C", "DVB-T", "ATSC")):
				return self.system(tpinfo)
			return ""

		if self.type == self.VIDEOCODEC:
			return self.videocodec(info)

		if self.type == self.HDRINFO:
			return self.hdr(info)

		if self.type == self.FPS:
			return self.framerate(info)

		if self.type == self.VIDEOSIZE:
			return self.videosize(info)

		if self.type == self.RESCODEC:
			vidsize = self.videosize(info)
			fps = self.framerate(info)
			vidcodec = self.videocodec(info)
			return f"{vidsize}   {fps}   {vidcodec}"

		if self.type == self.STREAMURL:
			return self.streamurl(info)

		if self.type == self.STREAMTYPE:
			return self.streamtype(info)

		pidtypes_mapping = {
			self.PIDINFODEC: "Dec",
			self.PIDINFOHEX: "Hex",
			self.PIDINFODECHEX: "DecHex"
		}

		if self.type in pidtypes_mapping:
			pid_type = pidtypes_mapping[self.type]
			return " ".join([
				self.format_pid(vpid, "VPID", pid_type),
				self.format_pid(apid, "APID", pid_type),
				self.format_pid(sid, "SID", pid_type),
				self.format_pid(pcr, "PCR", pid_type),
				self.format_pid(pmt, "PMT", pid_type),
				self.format_pid(tsid, "TSID", pid_type),
				self.format_pid(onid, "ONID", pid_type)
			])

		return ""

	text = property(getText)

	@cached
	def getBoolean(self):
		service = self.source.service
		info = service and service.info()
		if not info:
			return False
		xresol = info.getInfo(iServiceInformation.sVideoWidth) if info.getInfo(iServiceInformation.sVideoWidth) != -1 else eAVControl.getInstance().getResolutionX(0)
		yresol = info.getInfo(iServiceInformation.sVideoHeight) if info.getInfo(iServiceInformation.sVideoHeight) != -1 else eAVControl.getInstance().getResolutionY(0)
		progrs = self.proginfo(info)
		vcodec = self.videocodec(info)
		streamurl = self.streamurl(info)
		gamma = self.hdr(info)
		resolutions = {
			self.IS2160: (2160 <= xresol <= 5150) and (1570 <= yresol <= 2170),
			self.IS1440: (1430 <= yresol <= 1450),
			self.IS1080: (1320 <= xresol <= 3840) and (780 <= yresol <= 1090),
			self.IS720: (601 <= yresol <= 740),
			self.IS576: (501 <= yresol <= 600),
			self.IS480: (380 <= yresol <= 500),
			self.IS360: (300 <= yresol <= 379),
			self.IS288: (261 <= yresol <= 299),
			self.IS240: (181 <= yresol <= 260),
			self.IS144: (120 <= yresol <= 180),
		}
		videoinfos = {
			self.ISPROGRESSIVE: progrs == "p",
			self.ISINTERLACED: progrs == "i",
			self.ISSTREAMING: bool(streamurl),
			self.HASMPEG2: vcodec == "MPEG2",
			self.HASAVC: vcodec in ("AVC", "MPEG4"),
			self.HASH263: vcodec == "H263",
			self.HASVC1: "VC1" in vcodec,
			self.HASMPEG4VC: vcodec == "MPEG4-VC",
			self.HASHEVC: vcodec in ("HEVC", "H265"),
			self.HASMPEG1: vcodec == "MPEG1",
			self.HASVP8: vcodec in ("VB8", "VP8"),
			self.HASVP9: vcodec in ("VB9", "VP9"),
			self.HASVP6: vcodec in ("VB6", "VP6"),
			self.HASDIVX: "DIVX" in vcodec,
			self.HASXVID: "XVID" in vcodec,
			self.HASSPARK: vcodec == "SPARK",
			self.HASAVS: "AVS" in vcodec,
			self.HASVCC: "VCC" in vcodec,
			self.ISSDR: gamma == "SDR",
			self.ISHDR: gamma == "HDR",
			self.ISHDR10: gamma == "HDR10",
			self.ISHLG: gamma == "HLG",
		}
		return resolutions.get(self.type, videoinfos.get(self.type, False))

	boolean = property(getBoolean)

	def changed(self, what):
		if what[0] == self.CHANGED_SPECIFIC:
			self.tpDataUpdate = False
			if what[1] == iPlayableService.evNewProgramInfo:
				self.tpDataUpdate = True
			if what[1] == iPlayableService.evEnd:
				self.tp = None
				self.tpinfo = None
			Converter.changed(self, what)
		elif what[0] == self.CHANGED_POLL and self.tpDataUpdate is not None:
			self.tpDataUpdate = False
			Converter.changed(self, what)
