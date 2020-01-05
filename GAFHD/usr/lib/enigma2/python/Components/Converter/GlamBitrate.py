from Components.Converter.Converter import Converter
from enigma import iServiceInformation, iPlayableService, eTimer
from Components.Element import cached
from Tools.Directories import fileExists
if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/BitrateViewer/bitratecalc.so'):
	from Plugins.Extensions.BitrateViewer.bitratecalc import eBitrateCalculator
	binaryfound = True
else:
	binaryfound = False

class GlamBitrate(Converter, object):
	VPID = 0
	APID = 1
	FORMAT = 2

	def __init__(self, type):
		Converter.__init__(self, type)
		if type == 'VideoBitrate':
			self.type = self.VPID
		elif type == 'AudioBitrate':
			self.type = self.APID
		else:
			self.type = self.FORMAT
			self.sfmt = type[:]
			if self.sfmt == '':
				self.sfmt = 'V:%V Kbit/s A:%A Kbit/s'
		self.clearData()
		self.initTimer = eTimer()
		self.initTimer.callback.append(self.initBitrateCalc)

	def clearData(self):
		self.videoBitrate = None
		self.audioBitrate = None
		self.video = self.audio = 0
		return

	def initBitrateCalc(self):
		service = self.source.service
		vpid = apid = dvbnamespace = tsid = onid = -1
		if service and binaryfound:
			serviceInfo = service.info()
			vpid = serviceInfo.getInfo(iServiceInformation.sVideoPID)
			apid = serviceInfo.getInfo(iServiceInformation.sAudioPID)
			tsid = serviceInfo.getInfo(iServiceInformation.sTSID)
			onid = serviceInfo.getInfo(iServiceInformation.sONID)
			dvbnamespace = serviceInfo.getInfo(iServiceInformation.sNamespace)
		if vpid > 0 and (self.type == self.VPID or self.type == self.FORMAT and '%V' in self.sfmt):
			self.videoBitrate = eBitrateCalculator(vpid, dvbnamespace, tsid, onid, 1000, 1048576)
			self.videoBitrate.callback.append(self.getVideoBitrateData)
		if apid > 0 and (self.type == self.APID or self.type == self.FORMAT and '%A' in self.sfmt):
			self.audioBitrate = eBitrateCalculator(apid, dvbnamespace, tsid, onid, 1000, 65536)
			self.audioBitrate.callback.append(self.getAudioBitrateData)

			
	@cached
	def getText(self):
		if not binaryfound:
			return 'N/A'
		elif self.type == self.VPID:
			ret = '%d' % self.video
		elif self.type == self.APID:
			ret = '%d' % self.audio
		else:
			ret = ''
			tmp = self.sfmt[:]
			while True:
				pos = tmp.find('%')
				if pos == -1:
					ret += tmp
					break
				ret += tmp[:pos]
				pos += 1
				l = len(tmp)
				f = pos < l and tmp[pos] or '%'
				if f == 'V':
					ret += '%d' % self.video
				elif f == 'A':
					ret += '%d' % self.audio
				else:
					ret += f
				if pos + 1 >= l:
					break
				tmp = tmp[pos + 1:]

		return ret

	text = property(getText)

	def getVideoBitrateData(self, value, status):
		if status:
			self.video = value
		else:
			self.videoBitrate = None
			self.video = 0
		Converter.changed(self, (self.CHANGED_POLL,))
		return

	def getAudioBitrateData(self, value, status):
		if status:
			self.audio = value
		else:
			self.audioBitrate = None
			self.audio = 0
		Converter.changed(self, (self.CHANGED_POLL,))
		return

	def changed(self, what):
		if what[0] is self.CHANGED_SPECIFIC:
			if what[1] is iPlayableService.evStart:
				self.initTimer.start(200, True)
			elif what[1] is iPlayableService.evEnd:
				self.clearData()
				Converter.changed(self, what)