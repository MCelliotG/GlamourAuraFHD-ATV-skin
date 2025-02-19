#GlamRoll renderer (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Renderer for other skins and rename it, please keep the first and second line adding your credits below

from Components.Renderer.Renderer import Renderer
from enigma import eLabel, eTimer
from Components.VariableText import VariableText

class GlamRoll(VariableText, Renderer):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		self.moveTimerText = eTimer()
		self.moveTimerText.timeout.get().append(self.moveTimerTextRun)
		self.sizeX = 0
		self.x = 0
		self.idx = 0
		self.backtext = ""
		self.status = "end"

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

		if what[0] == self.CHANGED_CLEAR:
			self.text = ""
			return

		self.text = self.source.text
		if self.instance:
			text_width = self.instance.calculateSize().width()
			if text_width > self.sizeX:
				self.x = len(self.text)
				self.idx = 0
				self.backtext = self.text
				self.status = "start"
				self.moveTimerText.start(1500)
			else:
				self.applyEllipsis()

	def moveTimerTextRun(self):
		self.moveTimerText.stop()
		if self.x > 0:
			self.text = self.backtext[self.idx:].replace("\n", "").replace("\r", " ")
			self.idx += 1
			self.x -= 1

		if self.x == 0:
			self.status = "end"
			self.text = self.backtext
			self.applyEllipsis()

		if self.status != "end":
			self.moveTimerText.start(100)

	def applyEllipsis(self):
		if self.instance:
			text_width = self.instance.calculateSize().width()
			if text_width > self.sizeX:
				cutoff = len(self.text)
				while text_width > self.sizeX and cutoff > 4:
					cutoff -= 1
					self.text = self.text[:cutoff]
					text_width = self.instance.calculateSize().width()
				space_idx = self.text.rfind(" ")
				if space_idx > 3:
					cutoff = space_idx
				self.text = self.text[:cutoff].rstrip() + "..."
