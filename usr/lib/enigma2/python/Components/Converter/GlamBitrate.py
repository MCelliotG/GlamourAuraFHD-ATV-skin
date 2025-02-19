#GlamBitrate converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

import os
import shutil
from Components.Converter.Converter import Converter
from enigma import eTimer, iServiceInformation, eConsoleAppContainer, iPlayableService
from Components.Element import cached
from Components.ServiceEventTracker import ServiceEventTracker

BITRATE_BINARY_PATH = 'bitrate'
binaryfound = shutil.which(BITRATE_BINARY_PATH) is not None

class GlamBitrate(Converter, object):
	VIDEOBITRATE = -1
	AUDIOBITRATE = 0
	VCUR = 1
	VMIN = 2
	VMAX = 3
	VAVG = 4
	ACUR = 5
	AMIN = 6
	AMAX = 7
	AAVG = 8
	ALL = 9

	def __init__(self, type):
		Converter.__init__(self, type)
		self.type = type
		self.video = self.audio = 0
		self.tpDataUpdate = False
		self.vcur = self.vmin = self.vmax = self.vavg = 0
		self.acur = self.amin = self.amax = self.aavg = 0
		self.clearValues()
		self.timer = eTimer()
		self.timer.callback.append(self.updateBitrate)
		self.container = eConsoleAppContainer()
		self.container.dataAvail.append(self.processOutput)
		self.initBitrate()

		self.session = getattr(self.source, 'session', None)
		if self.session:
			self.__event_tracker = ServiceEventTracker(screen=self.session, eventmap={
				iPlayableService.evStart: self.serviceChanged,
				iPlayableService.evUpdatedInfo: self.serviceChanged,
				iPlayableService.evEnd: self.clearValues
			})

	def initBitrate(self):
		if not binaryfound:
			print("[GlamBitrate] Bitrate binary not found!")
			return
		print("[GlamBitrate] Using bitrate binary.")
		self.timer.start(1000, True)  # Refresh rate

	def clearValues(self):
		print("[GlamBitrate] Clearing values.")
		self.vmin = self.vmax = self.vavg = self.vcur = 0
		self.amin = self.amax = self.aavg = self.acur = 0
		Converter.changed(self, (self.CHANGED_POLL,))

	def serviceChanged(self):
		print("[GlamBitrate] Service changed, checking PIDs.")
		vpid, apid = self.getServicePIDs()
		if vpid <= 0 and apid <= 0:
			print("[GlamBitrate] No valid PIDs found, clearing values.")
			self.clearValues()
		else:
			print("[GlamBitrate] Valid PIDs found, restarting bitrate process.")
			self.startBitrateProcess()

	def getCurrentlyPlayingServiceReference(self):
		if self.source and self.source.service:
			return self.source.service.toString()
		return None

	def getServicePIDs(self):
		service = getattr(self.source, 'service', None)
		if service is None:
			self.clearValues()
			return -1, -1
		serviceInfo = service.info()
		vpid = serviceInfo.getInfo(iServiceInformation.sVideoPID)
		apid = serviceInfo.getInfo(iServiceInformation.sAudioPID)
		if vpid <= 0 and apid <= 0:
			self.clearValues()
		return vpid, apid

	def getAdapterAndDemux(self):
		adapter, demux = 0, 0
		service = getattr(self.source, 'service', None)
		if service:
			try:
				streamdata = service.stream().getStreamingData()
				adapter = streamdata.get('adapter', 0)
				demux = streamdata.get('demux', 0)
				print(f"[GlamBitrate] Adapter: {adapter}, Demux: {demux}")
			except Exception as e:
				print(f"[GlamBitrate] Error getting adapter/demux: {e}")
		return adapter, demux

	def stopBitrateProcess(self):
		self.container.kill()
		self.clearValues()

	def startBitrateProcess(self):
		if not binaryfound:
			self.clearValues()
			return
		vpid, apid = self.getServicePIDs()
		adapter, demux = self.getAdapterAndDemux()
		if vpid == 0 and apid == 0:
			self.clearValues()
			print("[GlamBitrate] Invalid PIDs, clearing values.")
			return
		cmd = f"{BITRATE_BINARY_PATH} {adapter} {demux} {vpid} {apid}"
		print(f"[GlamBitrate] Executing: {cmd}")
		self.container.execute(cmd)

	def processOutput(self, data):
		try:
			output = data.decode('utf-8').strip()
			print(f"[GlamBitrate] Raw Output: {output}")
			lines = output.split("\n")
			if len(lines) >= 2:
				vdata = [int(x) if x.isdigit() else 0 for x in lines[0].split()]
				adata = [int(x) if x.isdigit() else 0 for x in lines[1].split()]
				self.vmin, self.vmax, self.vavg, self.vcur = (vdata + [0, 0, 0, 0])[:4]
				self.amin, self.amax, self.aavg, self.acur = (adata + [0, 0, 0, 0])[:4]
				print(f"[GlamBitrate] Video - Min: {self.vmin}, Max: {self.vmax}, Avg: {self.vavg}, Cur: {self.vcur}")
				print(f"[GlamBitrate] Audio - Min: {self.amin}, Max: {self.amax}, Avg: {self.aavg}, Cur: {self.acur}")
				Converter.changed(self, (self.CHANGED_POLL,))
		except Exception as e:
			self.clearValues()
			print(f"[GlamBitrate] Error processing bitrate output: {e}")
		except Exception as e:
			print(f"[GlamBitrate] Error processing bitrate output: {e}")

	def updateBitrate(self):
		if binaryfound:
			self.startBitrateProcess()
		self.timer.start(1000, True)

	@cached
	def getText(self):
		if not binaryfound:
			return "N/A"
		values = {
			"%VCUR": str(self.vcur), "%VMIN": str(self.vmin), "%VMAX": str(self.vmax), "%VAVG": str(self.vavg),
			"%ACUR": str(self.acur), "%AMIN": str(self.amin), "%AMAX": str(self.amax), "%AAVG": str(self.aavg)
		}
		if self.type == "VIDEOBITRATE":
			return f"Video: Cur:{self.vcur} Min:{self.vmin} Max:{self.vmax} Avg:{self.vavg}"
		elif self.type == "AUDIOBITRATE": 
			return f"Audio: Cur:{self.acur} Min:{self.amin} Max:{self.amax} Avg:{self.aavg}"
		elif self.type == "VCUR": 
			return f"Cur:{self.vcur} Kbit/s"
		elif self.type == "VMIN": 
			return f"Min:{self.vmin} Kbit/s"
		elif self.type == "VMAX": 
			return f"Max:{self.vmax} Kbit/s"
		elif self.type == "VAVG": 
			return f"Avg:{self.vavg} Kbit/s"
		elif self.type == "ACUR": 
			return f"Cur:{self.acur} Kbit/s"
		elif self.type == "AMIN": 
			return f"Min:{self.amin} Kbit/s"
		elif self.type == "AMAX": 
			return f"Max:{self.amax} Kbit/s"
		elif self.type == "AAVG": 
			return f"Avg:{self.aavg} Kbit/s"
		elif self.type == "ALL": 
			return f"Video: Cur:{self.vcur} Min:{self.vmin} Max:{self.vmax} Avg:{self.vavg}\nAudio: Cur:{self.acur} Min:{self.amin} Max:{self.amax} Avg:{self.aavg}"
		text = self.type
		for key, value in values.items():
			text = text.replace(key, value)
		return text

	text = property(getText)

	def changed(self, what):
		if what[0] == self.CHANGED_SPECIFIC:
			self.tpDataUpdate = False
			if what[1] in (iPlayableService.evStart, iPlayableService.evUpdatedInfo):
				self.tpDataUpdate = True
				self.serviceChanged()
			elif what[1] == iPlayableService.evEnd:
				self.stopBitrateProcess()
			Converter.changed(self, what)
		elif what[0] == self.CHANGED_POLL and self.tpDataUpdate is not None:
			self.tpDataUpdate = False
			Converter.changed(self, what)