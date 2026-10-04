#GlamTP renderer (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Renderer for other skins and rename it, please keep the first and second line adding your credits below

import re

from Components.Renderer.Renderer import Renderer
from enigma import eLabel, eTimer
from Components.VariableText import VariableText
from enigma import eServiceCenter, eServiceReference, iServiceInformation, eDVBFrontendParametersSatellite
from Tools.Transponder import ConvertToHumanReadable

def sp(text: str) -> str:
	return f"{text} " if text else ""

DAB_FREQUENCIES = {
	"5A": 174928, "5B": 176640, "5C": 178352, "5D": 180064,
	"6A": 181936, "6B": 183648, "6C": 185360, "6D": 187072,
	"7A": 188928, "7B": 190640, "7C": 192352, "7D": 194064,
	"8A": 195936, "8B": 197648, "8C": 199360, "8D": 201072,
	"9A": 202928, "9B": 204640, "9C": 206352, "9D": 208064,
	"10A": 209936, "10B": 211648, "10C": 213360, "10D": 215072,
	"11A": 216928, "11B": 218640, "11C": 220352, "11D": 222064,
	"12A": 223936, "12B": 225648, "12C": 227360, "12D": 229072,
	"13A": 230784, "13B": 232496, "13C": 234208, "13D": 235776,
	"13E": 237488, "13F": 239200,
}

POLARIZATIONS = {
	eDVBFrontendParametersSatellite.Polarisation_Horizontal: "H",
	eDVBFrontendParametersSatellite.Polarisation_Vertical: "V",
	eDVBFrontendParametersSatellite.Polarisation_CircularLeft: "L",
	eDVBFrontendParametersSatellite.Polarisation_CircularRight: "R"
}

class GlamTP(VariableText, Renderer):
	__module__ = __name__

	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		self.moveTimerText = eTimer()
		self.moveTimerText.callback.append(self.moveTimerTextRun)
		self.sizeX = 0

	def applySkin(self, desktop, parent):
		attribs = []
		for attrib, value in self.skinAttributes:
			if attrib == "size":
				self.sizeX = int(value.strip().split(",")[0])
			attribs.append((attrib, value))

		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = eLabel

	def _isDAB(self, service, refstr):
		if refstr.startswith("dab://"):
			return True
		try:
			if int(refstr.split(":", 1)[0]) == 4115:
				return True
		except (IndexError, TypeError, ValueError):
			pass
		try:
			return getattr(eServiceReference, "idServiceDAB", None) == service.type
		except (AttributeError, TypeError):
			return False

	def _isDABUSB(self, refstr):
		return refstr.startswith("dab://rtlsdr/") or bool(re.search(r"(?i)dab(?:%3a|:)//rtlsdr/", refstr))

	def _dabChannel(self, refstr):
		match = re.search(r"(?i)dab(?:%3a|:)//(?:rtlsdr/)?([^/:]+)", refstr)
		channel = match.group(1).upper() if match else ""
		return channel if channel in DAB_FREQUENCIES else ""

	def _dabFrequency(self, channel):
		frequency = DAB_FREQUENCIES.get(channel)
		return f"{channel} {frequency / 1000.0:.3f} MHz" if frequency else channel

	def _dabReferenceId(self, service, index):
		try:
			return service.getUnsignedData(index)
		except (AttributeError, TypeError, ValueError):
			return 0

	def _dabParentTransponder(self, service):
		"""Resolve the selected DAB service's parent through static DVB info."""
		try:
			# Mirrors eServiceDAB::parentReference(): DVB type, SID, TSID,
			# ONID and namespace occupy unsigned data fields 0 through 4.
			fields = [service.getUnsignedData(index) for index in range(5)]
			parent = eServiceReference("1:0:%X:%X:%X:%X:%X:0:0:0:" % tuple(fields))
			info = eServiceCenter.getInstance().info(parent)
			tp = info.getInfoObject(parent, iServiceInformation.sTransponderData) if info is not None else None
			if isinstance(tp, dict) and tp.get("frequency"):
				return tp
			# Some builds expose static transponder data through this API.
			getTp = getattr(info, "getTransponderData", None)
			if getTp is not None:
				data = getTp(parent)
				if isinstance(data, dict):
					return data
			return {}
		except (AttributeError, TypeError, ValueError, KeyError, RuntimeError):
			return {}

	def connect(self, source):
		Renderer.connect(self, source)
		self.changed((self.CHANGED_DEFAULT,))

	def _staticTransponder(self, info, service):
		try:
			tp = info.getInfoObject(service, iServiceInformation.sTransponderData)
			return tp if isinstance(tp, dict) else {}
		except (AttributeError, TypeError, ValueError, RuntimeError):
			return {}

	def _humanTransponder(self, tp):
		try:
			result = ConvertToHumanReadable(tp.copy()) if tp else {}
			return result if isinstance(result, dict) else {}
		except (AttributeError, TypeError, ValueError, KeyError, RuntimeError):
			return {}

	def _streamDetails(self, refstr):
		curref = refstr.replace("%3a", ":")
		url = ""
		if curref.startswith("1:7:"):
			curref = ""
		elif "%3a/" in refstr or ":/" in refstr:
			parts = refstr.split(":", 10)
			url = parts[10].split(":", 1)[0].replace("%3a", ":") if len(parts) > 10 else ""
		if refstr.startswith("1:0:2"):
			kind = "Radio"
		elif not curref.startswith("1:0:") and "%3a/" in refstr:
			kind = "Stream"
		elif curref.startswith("1:0:") and "%3a/" in refstr:
			kind = "TS Relay" if any(addr in curref for addr in ("0.0.0.0:", "127.0.0.1:", "localhost:")) else "TS Stream"
		elif curref.startswith("1:134:"):
			kind = "Alternative"
		else:
			kind = ""
		return kind, url

	def changed(self, what):
		self.moveTimerText.stop()
		if not self.instance:
			return
		if what[0] == self.CHANGED_CLEAR:
			self.text = ""
			return
		service = self.source.service
		if service is None:
			self.text = ""
			return
		try:
			info = eServiceCenter.getInstance().info(service)
			refstr = service.toString().lower()
		except (AttributeError, TypeError, ValueError, RuntimeError):
			self.text = ""
			return
		if info is None:
			self.text = ""
			return
		isDAB = self._isDAB(service, refstr)
		isDABUSB = isDAB and self._isDABUSB(refstr)
		dabChannel = self._dabChannel(refstr) if isDABUSB else ""
		tp = self._staticTransponder(info, service)
		if isDAB and not isDABUSB and not tp.get("frequency"):
			tp = self._dabParentTransponder(service) or tp
		tpinfo = self._humanTransponder(tp)
		dabExtra = ""
		if isDAB:
			streamtype, streamurl = "DAB", ""
			sid = self._dabReferenceId(service, 6)
			eid = self._dabReferenceId(service, 7) & 0xFFFF
			if sid:
				dabExtra += f"SID:{sid:X} "
			if eid:
				dabExtra += f"EID:{eid:X} "
		else:
			streamtype, streamurl = self._streamDetails(refstr)
		if isDABUSB:
			# USB DAB must never inherit DVB details, even with malformed input.
			tp = tpinfo = {}
		self.text = self._formatTransponder(tp, tpinfo, streamtype, streamurl, dabExtra, dabChannel)
		if self.sizeX > 0 and self.instance.calculateSize().width() > self.sizeX:
			self.x = len(self.text)
			self.idx = 0
			self.backtext = self.text
			self.status = "start"
			self.moveTimerText.start(2000)

	def _formatTransponder(self, tp, tpinfo, streamtype, streamurl, dabExtra, dabChannel=""):
		freq = sr = orbpos = isid = plsmode = plscode = plpid = t2mi_id = t2mi_pid = ""
		ch = f"{tpinfo.get('channel', '')}/" if "channel" in tpinfo else ""

		sys = tpinfo.get("system", "") or ""
		freq = ""
		if tp.get("frequency") is not None:
			try:
				value = int(tp["frequency"])
				tuner = tp.get("tuner_type", "") or ""
				if "DVB-T" in sys or "ATSC" in sys or tuner in ("DVB-T", "ATSC"):
					freq = f"{value / 1000000.0:g} MHz"
				elif "DVB-C" in sys or tuner == "DVB-C":
					freq = f"{value / 1000.0:g} MHz"
				elif "DVB-S" in sys or tuner == "DVB-S":
					freq = str(value // 1000)
			except (TypeError, ValueError, OverflowError):
				freq = ""

		if "plp_id" in tp and "DVB-T2" in sys:
			plpid = f"PLP ID:{tpinfo.get('plp_id', 0)}"

		if "t2mi_plp_id" in tp and "DVB-S2" in sys:
			t2mi_id = str(tpinfo.get("t2mi_plp_id", -1))
			t2mi_pid = str(tpinfo.get("t2mi_pid", ""))

			if t2mi_id in {"-1", "None"} or t2mi_pid == "0" or t2mi_id.isdigit() and int(t2mi_id) > 255:
				t2mi_id = t2mi_pid = ""
			else:
				t2mi_id = f"T2MI PLP {t2mi_id}"
				t2mi_pid = f"PID {t2mi_pid}" if t2mi_pid != "None" else ""

		mod = tpinfo.get("modulation", "")

		pol = POLARIZATIONS.get(tp.get("polarization"), "")

		const = tpinfo.get("constellation", "")
		fec = tpinfo.get("fec_inner", "")
		try:
			sr = str(int(tp["symbol_rate"]) // 1000) if "symbol_rate" in tp else ""
		except (TypeError, ValueError, OverflowError):
			sr = ""

		try:
			position = int(tp["orbital_position"]) if "orbital_position" in tp else None
		except (TypeError, ValueError, OverflowError):
			position = None
		if position is not None:
			orbpos = position
			if orbpos > 1800:
				orbpos = f"{(3600 - orbpos) / 10.0}°W"
			else:
				orbpos = f"{orbpos / 10.0}°E"

		if "is_id" in tp or "pls_code" in tp or "pls_mode" in tp:
			isid = str(tpinfo.get("is_id", 0))
			plscode = str(tpinfo.get("pls_code", 0))
			plsmode = str(tpinfo.get("pls_mode", None))

			if plsmode in {"None", "Unknown"} or (plsmode and plscode == "0"):
				plsmode = ""

			isid = f"IS:{isid}" if isid not in {"None", "-1", "0"} else ""
			plscode = "" if plscode in {"None", "-1", "0"} else plscode

			if (plscode == "0" and plsmode == "Gold") or (plscode == "1" and plsmode == "Root"):
				plscode = plsmode = ""

		# RTL-SDR DAB has no DVB transponder dictionary.  Re-apply the DAB
		# presentation after the generic DVB calculations above so an empty
		# tp cannot overwrite its channel/frequency with blank values.
		if dabChannel:
			ch = ""
			freq = self._dabFrequency(dabChannel)
			pol = sys = mod = const = fec = sr = orbpos = isid = plsmode = plscode = plpid = t2mi_id = t2mi_pid = ""

		prefix = "".join(sp(value) for value in (streamtype, streamurl, orbpos)) + ch
		transport = "".join(sp(value) for value in (freq, pol, sys, mod, plpid, sr, fec, const, isid, plsmode, plscode, t2mi_id, t2mi_pid))
		return prefix + transport + dabExtra

	def moveTimerTextRun(self):
		self.moveTimerText.stop()
		if not self.instance:
			return
		if self.x > 0:
			self.text = self.backtext[self.idx:].replace("\n", "").replace("\r", " ")
			self.idx += 1
			self.x -= 1
		if self.x == 0: 
			self.status = "end"
			self.text = self.backtext
			text_width = self.instance.calculateSize().width()
			if text_width > self.sizeX:
				while text_width > self.sizeX:
					self.text = self.text[:-1]
					text_width = self.instance.calculateSize().width()
				self.text = f"{self.text[:-3]}..."
		if self.status != "end":
			self.moveTimerText.start(150)
