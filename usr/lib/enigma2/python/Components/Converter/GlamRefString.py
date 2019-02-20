#	GlamRefString for Enigma-2
#	Coded by Vali (c)2011
#	modified by MCelliotG for Glamour skins

from Components.Converter.Converter import Converter
from Components.Element import cached
from Screens.InfoBar import InfoBar

class GlamRefString(Converter, object):
	CURRENT = 0
	EVENT = 1
	
	def __init__(self, type):
		Converter.__init__(self, type)
		self.CHANSEL = None
		self.type = {
				"CurrentRef": self.CURRENT,
				"ServicelistRef": self.EVENT
			}[type]

	@cached
	def getText(self):
		if (self.type == self.EVENT):
			servname= str(self.source.service.toString())
			return servname
		elif (self.type == self.CURRENT):
			if self.CHANSEL == None:
				self.CHANSEL = InfoBar.instance.servicelist
			if len(InfoBar.instance.session.dialog_stack)>1:
				for zz in InfoBar.instance.session.dialog_stack:
					if (str(zz[0]) == "<class 'Screens.MovieSelection.MovieSelection'>") or (str(InfoBar.instance.session.dialog_stack[1][0]) == "<class 'Screens.InfoBar.MoviePlayer'>"):
						return self.source.text
			vSrv = self.CHANSEL.servicelist.getCurrent()
			return str(vSrv.toString())
		else:
			return "na"

	text = property(getText)
 