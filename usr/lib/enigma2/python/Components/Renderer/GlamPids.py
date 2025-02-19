#  GlamPids renderer
#  Modded and recoded by MCelliotG for use in Glamour skins or standalone
#  If you use this Renderer for other skins and rename it, please keep the first and second line adding your credits below

from Components.Renderer.Renderer import Renderer
from enigma import eLabel
from Components.VariableText import VariableText
from enigma import eServiceCenter, iServiceInformation

class GlamPids(VariableText, Renderer):
	__module__ = __name__

	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)

	GUI_WIDGET = eLabel

	def connect(self, source):
		Renderer.connect(self, source)
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		if self.instance:
			if what[0] == self.CHANGED_CLEAR:
				self.text = " "
				return
			
			service = self.source.service
			info = eServiceCenter.getInstance().info(service)

			if not (info and service):
				return

			refstr = self.source.service.toString()
			curref = refstr.replace("%3a", ":")
			
			if curref.startswith("1:7:") or "%3a/" in refstr:
				self.text = " "
				return

			try:
				ids = refstr.split(":")
				hex_vals = [ids[i].zfill(4) for i in range(3, 6)]
				dec_vals = [str(int(h, 16)).zfill(4) for h in hex_vals]

				sid = f"SID:{dec_vals[0]} ({hex_vals[0]}) " if int(dec_vals[0]) >= 0 else ""
				tsid = f"TSID:{dec_vals[1]} ({hex_vals[1]}) " if int(dec_vals[1]) >= 0 else ""
				onid = f"ONID:{dec_vals[2]} ({hex_vals[2]}) " if int(dec_vals[2]) >= 0 else ""

				self.text = sid + tsid + onid
			except:
				self.text = " "
