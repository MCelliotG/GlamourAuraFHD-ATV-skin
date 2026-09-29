#GlamourBitrate converter (Python 3) - FINAL DAB/media/OpenATV 7.6 compatible
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

import os
import re
import shutil
from Components.Converter.Converter import Converter
from enigma import eTimer, iServiceInformation, eConsoleAppContainer, iPlayableService, eServiceReference
from Components.Element import cached
from Components.ServiceEventTracker import ServiceEventTracker

BITRATE_BINARY_PATH = 'bitrate'
binaryfound = shutil.which(BITRATE_BINARY_PATH) is not None

class GlamourBitrate(Converter, object):
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
		self.mediaTotal = 0
		self.serviceMode = "unknown"
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
				iPlayableService.evEnd: self.stopBitrateProcess
			})

	def initBitrate(self):
		if not binaryfound:
			print("[GlamourBitrate] Bitrate binary not found; DAB bitrate remains available.")
		else:
			print("[GlamourBitrate] Using bitrate binary.")
		self.timer.start(1000, True)  # Refresh rate

	def clearValues(self):
		print("[GlamourBitrate] Clearing values.")
		self.vmin = self.vmax = self.vavg = self.vcur = 0
		self.amin = self.amax = self.aavg = self.acur = 0
		self.mediaTotal = 0
		Converter.changed(self, (self.CHANGED_POLL,))

	def serviceChanged(self):
		mode = self.getServiceMode()
		if mode == "dab":
			if self.serviceMode != "dab":
				self.container.kill()
				self.clearValues()
			self.serviceMode = "dab"
			self.updateDABBitrate()
			return
		if mode == "media":
			if self.serviceMode != "media":
				self.container.kill()
				self.clearValues()
			self.serviceMode = "media"
			self.updateMediaBitrate()
			return
		wasNonDVB = self.serviceMode != "dvb"
		self.serviceMode = mode
		if wasNonDVB:
			self.clearValues()
		print("[GlamourBitrate] Service changed, checking PIDs.")
		vpid, apid = self.getServicePIDs()
		if vpid <= 0 and apid <= 0:
			print("[GlamourBitrate] No valid PIDs found, clearing values.")
			self.clearValues()
		else:
			print("[GlamourBitrate] Valid PIDs found, restarting bitrate process.")
			self.startBitrateProcess()

	def getServiceMode(self):
		service = getattr(self.source, 'service', None)
		if service is None:
			return "unknown"
		try:
			serviceRef = service.info().getInfoString(iServiceInformation.sServiceref)
			if not serviceRef:
				return "unknown"
			serviceType = eServiceReference(serviceRef).type
			dabType = getattr(eServiceReference, "idServiceDAB", None)
			if dabType is not None and serviceType == dabType:
				return "dab"
			dvbTypes = (eServiceReference.idDVB, getattr(eServiceReference, "idDVBScrambled", eServiceReference.idDVB + 0x100))
			if serviceType in dvbTypes:
				return "dvb"
			return "media"
		except Exception as e:
			print(f"[GlamourBitrate] Error detecting service type: {e}")
			return "unknown"

	def isDABService(self):
		return self.getServiceMode() == "dab"

	def getDABBitrate(self):
		"""Return the selected DAB audio component bitrate in kbit/s."""
		service = getattr(self.source, 'service', None)
		if service is None:
			return 0
		try:
			serviceInfo = service.info()
			# sTransferBPS is the total DAB input/ensemble throughput, not the
			# bitrate of the selected audio service.  Use the component bitrate
			# published by the DAB decoder instead.
			tagBitrate = serviceInfo.getInfoString(iServiceInformation.sTagBitrate)
			match = re.search(r"(\d+(?:\.\d+)?)", tagBitrate or "")
			if match:
				return self.sanitize(int(round(float(match.group(1)))))
		except Exception as e:
			print(f"[GlamourBitrate] Error getting DAB bitrate: {e}")
		return 0

	def updateDABBitrate(self):
		value = self.getDABBitrate()
		self.vmin = self.vmax = self.vavg = self.vcur = 0
		if value <= 0:
			self.acur = self.amin = self.amax = self.aavg = 0
		else:
			self.acur = value
			# DAB exposes the service/component bitrate, not the DVB-style
			# rolling audio statistics.  Keep the existing placeholders useful
			# for BitrateAdv without presenting false min/max/avg values.
			self.amin = self.amax = self.aavg = value
		Converter.changed(self, (self.CHANGED_POLL,))

	def getMediaBitrate(self):
		"""Return (bitrate, has_video, is_total_media_bitrate)."""
		service = getattr(self.source, 'service', None)
		if service is None:
			return 0, False, False
		try:
			serviceInfo = service.info()
			serviceRef = serviceInfo.getInfoString(iServiceInformation.sServiceref)
			path = eServiceReference(serviceRef or "").getPath()
			hasVideo = False
			try:
				hasVideo = serviceInfo.getInfo(iServiceInformation.sVideoWidth) > 0 and serviceInfo.getInfo(iServiceInformation.sVideoHeight) > 0
			except Exception:
				pass
			if not hasVideo and path:
				hasVideo = os.path.splitext(path.split("?")[0].lower())[1] in (".mp4", ".mkv", ".ts", ".mts", ".m2ts", ".avi", ".mov", ".m4v", ".webm", ".wmv")

			# GStreamer reports GST_TAG_BITRATE in bit/s for eServiceMP3.
			bitrate = serviceInfo.getInfo(iServiceInformation.sTagBitrate)
			if bitrate > 0:
				value = self.sanitize(int(round(bitrate / 1000.0)))
				# For a video container this is one aggregate/container value,
				# not a separate audio or video elementary-stream bitrate.
				return value, hasVideo, hasVideo

			# Fixed local files do not always carry a bitrate tag.  In that
			# case expose their average container bitrate as a last resort.
			if not path or "://" in path or not os.path.isfile(path):
				return 0, hasVideo, False
			seek = service.seek()
			length = seek and seek.getLength()
			if length and length[0] == 0 and length[1] > 0:
				seconds = length[1] / 90000.0
				value = self.sanitize(int(round(os.path.getsize(path) * 8 / seconds / 1000.0)))
				return value, hasVideo, hasVideo
		except Exception as e:
			print(f"[GlamourBitrate] Error getting media bitrate: {e}")
		return 0, False, False

	def updateMediaBitrate(self):
		value, hasVideo, isTotal = self.getMediaBitrate()
		self.vmin = self.vmax = self.vavg = self.vcur = 0
		self.amin = self.amax = self.aavg = self.acur = 0
		self.mediaTotal = value if isTotal and value > 0 else 0
		if isTotal:
			# Keep the total separate. It must not be reported as Audio or Video.
			pass
		elif hasVideo:
			self.vmin = self.vmax = self.vavg = self.vcur = value
		else:
			self.acur = self.amin = self.amax = self.aavg = value
		Converter.changed(self, (self.CHANGED_POLL,))

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
				print(f"[GlamourBitrate] Adapter: {adapter}, Demux: {demux}")
			except Exception as e:
				print(f"[GlamourBitrate] Error getting adapter/demux: {e}")
		return adapter, demux

	def stopBitrateProcess(self):
		self.container.kill()
		self.serviceMode = "unknown"
		self.clearValues()

	def startBitrateProcess(self):
		mode = self.getServiceMode()
		if mode == "dab":
			self.updateDABBitrate()
			return
		if mode == "media":
			self.updateMediaBitrate()
			return
		if mode != "dvb":
			self.clearValues()
			return
		if not binaryfound:
			self.clearValues()
			return
		vpid, apid = self.getServicePIDs()
		adapter, demux = self.getAdapterAndDemux()
		if vpid == 0 and apid == 0:
			self.clearValues()
			print("[GlamourBitrate] Invalid PIDs, clearing values.")
			return
		cmd = f"{BITRATE_BINARY_PATH} {adapter} {demux} {vpid} {apid}"
		print(f"[GlamourBitrate] Executing: {cmd}")
		self.container.execute(cmd)

	@staticmethod
	def sanitize(value):
		return value if value <= 999999 else 0

	def processOutput(self, data):
		# A killed bitrate process can still deliver buffered output.  Never
		# allow DVB output to overwrite DAB/media values after a zap.
		if self.serviceMode != "dvb" or self.getServiceMode() != "dvb":
			return
		try:
			output = data.decode('utf-8').strip()
			print(f"[GlamourBitrate] Raw Output: {output}")
			lines = output.split("\n")
			if len(lines) >= 2:
				vdata = [int(x) if x.isdigit() else 0 for x in lines[0].split()]
				adata = [int(x) if x.isdigit() else 0 for x in lines[1].split()]
				self.vmin, self.vmax, self.vavg, self.vcur = (vdata + [0, 0, 0, 0])[:4]
				self.amin, self.amax, self.aavg, self.acur = (adata + [0, 0, 0, 0])[:4]

				# --- Sanitize fake large values ---
				for attr in ["vmin", "vmax", "vavg", "vcur", "amin", "amax", "aavg", "acur"]:
					setattr(self, attr, self.sanitize(getattr(self, attr)))
				# ------------------------------------------------------

				print(f"[GlamourBitrate] Video - Min: {self.vmin}, Max: {self.vmax}, Avg: {self.vavg}, Cur: {self.vcur}")
				print(f"[GlamourBitrate] Audio - Min: {self.amin}, Max: {self.amax}, Avg: {self.aavg}, Cur: {self.acur}")
				Converter.changed(self, (self.CHANGED_POLL,))
		except Exception as e:
			self.clearValues()
			print(f"[GlamourBitrate] Error processing bitrate output: {e}")

	def updateBitrate(self):
		mode = self.getServiceMode()
		if mode == "dab":
			if self.serviceMode != "dab":
				self.container.kill()
				self.clearValues()
			self.serviceMode = "dab"
			self.updateDABBitrate()
		elif mode == "media":
			if self.serviceMode != "media":
				self.container.kill()
				self.clearValues()
			self.serviceMode = "media"
			self.updateMediaBitrate()
		elif mode == "dvb" and binaryfound:
			self.serviceMode = "dvb"
			self.startBitrateProcess()
		self.timer.start(1000, True)

	@cached
	def getText(self):
		mode = self.getServiceMode()
		showNA = mode == "media"
		display = lambda value: "N/A" if showNA and value <= 0 else str(value)
		rate = lambda label, value: f"{label}:{value}" if value == "N/A" else f"{label}:{value} Kbit/s"
		vcur, vmin, vmax, vavg = display(self.vcur), display(self.vmin), display(self.vmax), display(self.vavg)
		acur, amin, amax, aavg = display(self.acur), display(self.amin), display(self.amax), display(self.aavg)
		values = {
			"%VCUR": vcur, "%VMIN": vmin, "%VMAX": vmax, "%VAVG": vavg,
			"%ACUR": acur, "%AMIN": amin, "%AMAX": amax, "%AAVG": aavg
		}
		if mode == "media" and self.mediaTotal > 0:
			return f"Bitrate: {self.mediaTotal} Kbit/s"
		if not binaryfound and mode != "dab" and mode != "media":
			return "N/A"
		if self.type == "VIDEOBITRATE":
			if showNA and self.vcur <= 0:
				return "Video: N/A"
			return f"Video: Cur:{vcur} Min:{vmin} Max:{vmax} Avg:{vavg}"
		elif self.type == "AUDIOBITRATE": 
			if showNA and self.acur <= 0:
				return "Audio: N/A"
			return f"Audio: Cur:{acur} Min:{amin} Max:{amax} Avg:{aavg}"
		elif self.type == "VCUR": 
			return rate("Cur", vcur)
		elif self.type == "VMIN": 
			return rate("Min", vmin)
		elif self.type == "VMAX": 
			return rate("Max", vmax)
		elif self.type == "VAVG": 
			return rate("Avg", vavg)
		elif self.type == "ACUR": 
			return rate("Cur", acur)
		elif self.type == "AMIN": 
			return rate("Min", amin)
		elif self.type == "AMAX": 
			return rate("Max", amax)
		elif self.type == "AAVG": 
			return rate("Avg", aavg)
		elif self.type == "ALL": 
			if showNA and self.vcur <= 0 and self.acur <= 0:
				return "Video: N/A\nAudio: N/A"
			return f"Video: Cur:{vcur} Min:{vmin} Max:{vmax} Avg:{vavg}\nAudio: Cur:{acur} Min:{amin} Max:{amax} Avg:{aavg}"
		text = self.type
		for key, value in values.items():
			text = text.replace(key, value)
		if showNA:
			text = re.sub(r"N/A\s*(?:kbit/s|kb/s)", "N/A", text, flags=re.IGNORECASE)
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
