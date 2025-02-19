#GlamTP renderer (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Renderer for other skins and rename it, please keep the first and second line adding your credits below

from Components.Renderer.Renderer import Renderer
from enigma import eLabel, eTimer
from Components.VariableText import VariableText
from enigma import eServiceCenter, iServiceInformation, eDVBFrontendParametersSatellite
from Tools.Transponder import ConvertToHumanReadable

def sp(text: str) -> str:
	return f"{text} " if text else ""

class GlamTP(VariableText, Renderer):
	__module__ = __name__

	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		self.moveTimerText = eTimer()
		self.moveTimerText.callback.append(self.moveTimerText)

	def applySkin(self, desktop, parent):
		attribs = []
		for attrib, value in self.skinAttributes:
			if attrib == "size":
				self.sizeX = int(value.strip().split(",")[0])
			attribs.append((attrib, value))

		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = eLabel

	def connect(self, source):
		Renderer.connect(self, source)
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		self.moveTimerText.stop()
		if not self.instance:
			return

		if what[0] == self.CHANGED_CLEAR:
			self.text = ""
			return

		service = self.source.service
		info = eServiceCenter.getInstance().info(service)
		if not (info and service):
			return

		tp = info.getInfoObject(service, iServiceInformation.sTransponderData)
		tpinfo = ConvertToHumanReadable(tp)
		refstr = self.source.service.toString().lower()
		curref = refstr.replace("%3a", ":")

		streamtype = streamurl = freq = ch = pol = sys = mod = const = fec = sr = orbpos = isid = plsmode = plscode = plpid = t2mi_id = t2mi_pid = ""
		if curref.startswith("1:7:"):
			curref = ""
		elif "%3a/" in refstr or ":/" in refstr:
			streamurl = refstr.split(":")[10].replace("%3a", ":")
		
		if refstr.startswith("1:0:2"):
			streamtype = "Radio"
		elif not curref.startswith("1:0:") and "%3a/" in refstr:
			streamtype = "Stream"
		elif curref.startswith("1:0:") and "%3a/" in refstr:
			streamtype = "TS Relay" if any(addr in curref for addr in ("0.0.0.0:", "127.0.0.1:", "localhost:")) else "TS Stream"
		elif curref.startswith("1:134:"):
			streamtype = "Alternative"

		ch = f"{tpinfo.get('channel', '')}/" if "channel" in tpinfo else ""

		sys = tpinfo.get("system", "")
		freq = ""
		if "system" in tp:
			freq = f"{int(tp['frequency']) // 1000} Mhz" if "DVB-C" in sys or "DVB-T" in sys or "ATSC" in sys else f"{int(tp['frequency']) // 1000}" if "DVB-S" in sys else ""

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

		pol = {
			eDVBFrontendParametersSatellite.Polarisation_Horizontal: "H",
			eDVBFrontendParametersSatellite.Polarisation_Vertical: "V",
			eDVBFrontendParametersSatellite.Polarisation_CircularLeft: "L",
			eDVBFrontendParametersSatellite.Polarisation_CircularRight: "R"
		}.get(tp.get("polarization"), "")

		const = tpinfo.get("constellation", "")
		fec = tpinfo.get("fec_inner", "")
		sr = str(int(tp["symbol_rate"]) // 1000) if "symbol_rate" in tp else ""

		if "orbital_position" in tp:
			orbpos = int(tp["orbital_position"])
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

		self.text = sp(streamtype) + sp(streamurl) + sp(orbpos) + ch + sp(freq) + sp(pol) + sp(sys) + sp(mod) + sp(plpid) + sp(sr) + sp(fec) + sp(const) + sp(isid) + sp(plsmode) + sp(plscode) + sp(t2mi_id) + t2mi_pid

		text_width = self.instance.calculateSize().width()
		if self.instance and text_width > self.sizeX:
			self.x = len(self.text) 
			self.idx = 0
			self.backtext = self.text
			self.status = "start" 
			self.moveTimerText = eTimer()
			self.moveTimerText.timeout.get().append(self.moveTimerTextRun)
			self.moveTimerText.start(2000)

	def moveTimerTextRun(self):
		self.moveTimerText.stop()
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
