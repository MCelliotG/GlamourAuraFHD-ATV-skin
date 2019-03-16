# coded by shamann
# modded by Malakudi, added utf8 support
from Renderer import Renderer
from enigma import eLabel, eTimer
from Components.VariableText import VariableText

class GlamRoll(VariableText, Renderer):

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
			else:
				attribs.append((attrib, value))

		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = eLabel

	def connect(self, source):
		Renderer.connect(self, source)
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		self.moveTimerText.stop()

		if (what[0] == self.CHANGED_CLEAR):
			self.text = ""
		else:
			self.text = self.source.text
		if self.instance:
			text_width = self.instance.calculateSize().width()
			if (self.instance and (text_width > self.sizeX)):
				self.x = len(self.text.decode("utf8","ignore"))
				self.idx = 0
				self.backtext = self.text
				self.status = "start" 
				self.moveTimerText = eTimer()
				self.moveTimerText.timeout.get().append(self.moveTimerTextRun)
				self.moveTimerText.start(2000)


	def moveTimerTextRun(self):
		self.moveTimerText.stop()
		if self.x > 0:
			txttmp = self.backtext.decode("utf8","ignore")[self.idx:]
			self.text = txttmp.encode("utf8","ignore").replace("\n","").replace("\r"," ")
			self.idx = self.idx+1
			self.x = self.x-1
		if self.x == 0: 
			self.status = "end"
			self.text = self.backtext
			text_width = self.instance.calculateSize().width()
			if text_width > self.sizeX:
				while text_width > self.sizeX:
					self.text = self.text[:-1]
					text_width = self.instance.calculateSize().width()
				self.text = self.text[:-4] + " ..."
		if self.status is not "end":
			self.moveTimerText.start(150)
