#(c) 2boom mod 2012 
# 26.09.2012 added search mountpoints
#  GlamPiconUni renderer
#  Modded and recoded by MCelliotG for use in Glamour skins or standalone
#  If you use this Renderer for other skins and rename it, please keep all the above lines adding your credits below

from Components.Renderer.Renderer import Renderer 
from enigma import ePixmap, eTimer 
from Tools.Directories import SCOPE_SKIN_IMAGE, SCOPE_CURRENT_SKIN, resolveFilename 
from Tools.LoadPixmap import LoadPixmap 
from Components.Pixmap import Pixmap 
from Components.config import * 
import os.path

class GlamPiconUni(Renderer):
	__module__ = __name__
	def __init__(self):
		Renderer.__init__(self)
		self.path = 'piconUni'
		self.nameCache = {}
		self.pngname = ''

	def applySkin(self, desktop, parent):
		attribs = []
		for (attrib, value,) in self.skinAttributes:
			if (attrib == "path"):
				self.path = value
			else:
				attribs.append((attrib, value))
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap

	def changed(self, what):
		if self.instance:
			pngname = ""
			if (what[0] != self.CHANGED_CLEAR):
				sname = self.source.text
				sname = sname.upper()
				pngname = self.nameCache.get(sname, "")
				if (pngname == ""):
					pngname = self.findPicon(sname)
					if (pngname != ""):
						self.nameCache[sname] = pngname
			if (pngname == ""):
				pngname = self.nameCache.get("default", "")
				if (pngname == ""):
					pngname = self.findPicon("na")
					if (pngname == ""):
						tmp = resolveFilename(SCOPE_CURRENT_SKIN, "na.png")
						if os.path.exists(tmp):
							pngname = tmp
						else:
							pngname = resolveFilename(SCOPE_SKIN_IMAGE, "piconYWeather/na.png")
					self.nameCache["default"] = pngname
			if (self.pngname != pngname):
				self.pngname = pngname
				self.rTimer()
				self.instance.setPixmapFromFile(self.pngname)

	def findPicon(self, serviceName):
		searchPaths = []
		if os.path.exists("/proc/mounts"):
			for line in open("/proc/mounts"):
				if line.find("/dev/sd") > -1:
					searchPaths.append(line.split()[1].replace("\\040", " ") + "/%s/")
		searchPaths.append("/usr/share/enigma2/%s/")
		for path in searchPaths:
			pngname = (((path % self.path) + serviceName) + ".png")
			if os.path.exists(pngname):
				return pngname
		return ""

	def rTimer(self):
		self.slide = 1
		self.pics = []
		self.pics.append(LoadPixmap(self.path + "na.png"))
		self.timer = eTimer()
		self.timer.callback.append(self.timerEvent)
		self.timer.start(1, True)

	def timerEvent(self):
		if (self.slide != 0):
			self.timer.stop()
			self.instance.setPixmap(self.pics[(self.slide - 1)])
			self.slide = (self.slide - 1)
			self.timer.start(1, True)
		else:
			self.timer.stop()
			self.instance.setPixmapFromFile(self.pngname)