# coded by shamann
# modded by Malakudi, added utf8 support
from Renderer import Renderer
from enigma import eLabel
from enigma import eTimer
from Components.VariableText import VariableText

class GlamRoll(VariableText, Renderer):

	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		self.moveTimerText = eTimer()
		self.moveTimerText.callback.append(self.moveTimerText)
									
	GUI_WIDGET = eLabel

	def connect(self, source):
		Renderer.connect(self, source)
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		self.moveTimerText.stop()

		if (what[0] == self.CHANGED_CLEAR):
			self.text = ''
		else:
			self.text = self.source.text
		if self.instance:
			if (self.instance and (len(self.text.decode("utf8")) > 38)):
				self.x = len(self.text.decode("utf8")) 
				self.idx = 0
				self.backtext = self.text
				self.status = "start" 
				self.moveTimerText = eTimer()
				self.moveTimerText.timeout.get().append(self.moveTimerTextRun)
				self.moveTimerText.start(5)
            				
	def moveTimerTextRun(self):
		self.moveTimerText.stop()
		if self.x > 0:
			txttmp = self.backtext.decode("utf8")[self.idx:]
			self.text = txttmp[:60].encode("utf8","ignore")
			self.idx = self.idx+1
			self.x = self.x-1      
		if self.x == 0: 
			self.status = "end"     
			self.text = self.backtext
			if len(self.text.decode("utf8")) > 38:
			        txttmp = self.backtext.decode("utf8")
			        txttmp = txttmp[:36] + "..."
			        self.text = txttmp.encode("utf8")
		if self.status != "end":
			self.moveTimerText.start(130)