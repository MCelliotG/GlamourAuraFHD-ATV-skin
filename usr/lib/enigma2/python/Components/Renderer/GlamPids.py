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
		self.changed((self.CHANGED_DEFAULT))


	def changed(self, what):
		if self.instance:
			if (what[0] == self.CHANGED_CLEAR):
				self.text = " "
			else:
				service = self.source.service
				info = eServiceCenter.getInstance().info(service)
				if (info and service):
					refstr = self.source.service.toString()
					curref = refstr.replace("%3a", ":")
					sid = tsid = onid = ""
					try:
						if curref.startswith("1:7:"):
							sid = tsid = onid = ""
						if "%3a/" not in refstr and not curref.startswith("1:7:"):
							ids = refstr.split(":")
							hsid = str(int(ids[3], 16)).zfill(4)
							dsid = str((ids[3])).zfill(4)
							if dsid < "0":
								sid = ""
							else:
								sid = "SID:%s (%s) " % (dsid, hsid)
							htsid = str(int(ids[4], 16)).zfill(4)
							dtsid = str((ids[4])).zfill(4)
							if dtsid < "0":
								tsid = ""
							else:
								tsid = "TSID:%s (%s) " % (dtsid, htsid)
							honid = str(int(ids[5], 16)).zfill(4)
							donid = str((ids[5]).zfill(4))
							if donid < "0":
								onid = ""
							else:
								onid = "ONID:%s (%s) " % (donid, honid)
					except:
						pass
					self.text = (sid + tsid + onid)
