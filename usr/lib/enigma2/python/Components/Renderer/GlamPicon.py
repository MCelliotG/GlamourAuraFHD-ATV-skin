﻿from Tools.LoadPixmap import LoadPixmap 
from Components.Pixmap import Pixmap 
from Renderer import Renderer 
from enigma import ePixmap, eTimer 
from Tools.Directories import fileExists, SCOPE_SKIN_IMAGE, SCOPE_CURRENT_SKIN, resolveFilename 
from Components.config import config

class GlamPicon(Renderer):
	__module__ = __name__
	searchPaths = ('/usr/share/enigma2/%s/', '/media/ba/%s/', '/media/hdd/%s/', '/media/cf/%s/', '/media/usb/%s/', '/media/usb2/%s/', '/etc/%s/', '/media/sda1/%s/', '/media/sdb1/%s/', '/media/sdc1/%s/', '/media/sde1/%s/')
	
	def __init__(self):
		Renderer.__init__(self)
		self.path = 'picon'
		self.nameCache = {}
		self.pngname = ''
		self.pixmaps = []
		self.pixdelay = 100
		self.pics = []
		self.picon_default = "picon_default.png"
		
	def applySkin(self, desktop, parent):
		attribs = []
		for (attrib, value,) in self.skinAttributes:
			if (attrib == 'path'):
				self.path = value
			elif (attrib == 'picon_default'):
				self.picon_default = value
			elif attrib == "pixmaps":
				self.pixmaps = value.split(',')
			elif attrib == "pixdelay":
				self.pixdelay = int(value)
			else:
				attribs.append((attrib, value))
				
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)
		
	GUI_WIDGET = ePixmap
	
	def changed(self, what):
		if self.instance:
			pngname = ''
			if (what[0] != self.CHANGED_CLEAR):
				sname = ""
				try:
					sname = self.source.service.toString()
				except Exception, e:
					pass
					
				if len(sname) == 0:
					try:
						sname = self.source.text
					except Exception, e:
						pass
					
				if len(sname) == 0:
					return
					
				pos = sname.rfind(':')
				if (pos != -1):
					sname = sname[:pos].rstrip(':').replace(':', '_')
				pngname = self.nameCache.get(sname, '')
				if (pngname == ''):
					pngname = self.findPicon(sname)
					if (pngname != ''):
						self.nameCache[sname] = pngname
			if (pngname == ''):
				pngname = self.nameCache.get('default', '')
				if (pngname == ''):
					tmp = resolveFilename(SCOPE_CURRENT_SKIN, self.picon_default)
					if fileExists(tmp):
						pngname = tmp
					else:
						pngname = resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/picon_default.png')
					self.nameCache['default'] = pngname
					
			if (self.pngname != pngname):
				self.pngname = pngname
				self.runAnim()

					
	def findPicon(self, serviceName):
		for path in self.searchPaths:
			pngname = (((path % self.path) + serviceName) + '.png')
			if fileExists(pngname):
				return pngname
				
		return ''
		
	def runAnim(self):
		if len(self.pics) == 0:
			for x in self.pixmaps:
				self.pics.append(LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, x)))
			
		self.slide = len(self.pics)
		self.timer = eTimer()
		self.timer.callback.append(self.timerEvent)
		self.timer.start(self.pixdelay, True)
		
	def timerEvent(self):
		if self.slide > 0:
			self.timer.stop()
			self.instance.setPixmap(self.pics[len(self.pics) - self.slide])
			self.slide = self.slide - 1
			self.timer.start(self.pixdelay, True)
		else:
			self.timer.stop()
			self.instance.setPixmapFromFile(self.pngname)

