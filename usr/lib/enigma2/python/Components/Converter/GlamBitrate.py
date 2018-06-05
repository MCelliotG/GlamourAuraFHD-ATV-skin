from Components.Converter.Converter import Converter
from enigma import iServiceInformation, iPlayableService, eTimer, eServiceReference
from Components.Element import cached
import os
if os.path.isfile('/usr/lib/enigma2/python/Plugins/Extensions/BitrateViewer/bitratecalc.so'):
    from Plugins.Extensions.BitrateViewer.bitratecalc import eBitrateCalculator
    binaryfound = True
else:
    binaryfound = False

class GlamBitrate(Converter, object):
    VBIT = 0
    ABIT = 1
    FORMAT = 2

    def __init__(self, type):
        Converter.__init__(self, type)
        if type == 'VideoBitrate':
            self.type = self.VBIT
        elif type == 'AudioBitrate':
            self.type = self.ABIT
        else:
            self.type = self.FORMAT
            self.sfmt = type[:]
            if self.sfmt is '':
                self.sfmt = 'Video:%V Kb/s Audio:%A Kb/s'
        self.clearData()
        self.initTimer = eTimer()
        self.initTimer.callback.append(self.initBitrateCalc)

    def clearData(self):
        self.videoBitrate = None
        self.audioBitrate = None
        self.video = self.audio = 0


    def initBitrateCalc(self):
        service = self.source.service
        vpid = apid = dvbnamespace = tsid = onid = -1
        if binaryfound:
            if service:
                serviceInfo = service.info()
                vpid = serviceInfo.getInfo(iServiceInformation.sVideoPID)
                apid = serviceInfo.getInfo(iServiceInformation.sAudioPID)
                tsid = serviceInfo.getInfo(iServiceInformation.sTSID)
                onid = serviceInfo.getInfo(iServiceInformation.sONID)
                dvbnamespace = serviceInfo.getInfo(iServiceInformation.sNamespace)
            if vpid:
                self.videoBitrate = eBitrateCalculator(vpid, dvbnamespace, tsid, onid, 1000, 1048576)
                self.videoBitrate.callback.append(self.getVideoBitrateData)
            if apid:
                self.audioBitrate = eBitrateCalculator(apid, dvbnamespace, tsid, onid, 1000, 65536)
                self.audioBitrate.callback.append(self.getAudioBitrateData)

    @cached
    def getText(self):
        if not binaryfound:
            return 'N/A'
        elif self.type is self.VBIT:
            return '%d' % self.video
        elif self.type is self.ABIT:
            return '%d' % self.audio
        else:
            return self.sfmt[:].replace('%A', '%d' % self.audio).replace('%V', '%d' % self.video)

    text = property(getText)

    def getVideoBitrateData(self, value, status):
        if status:
            self.video = value
        else:
            self.videoBitrate = None
        Converter.changed(self, (self.CHANGED_POLL,))

    def getAudioBitrateData(self, value, status):
        if status:
            self.audio = value
        else:
            self.audioBitrate = None
        Converter.changed(self, (self.CHANGED_POLL,))

    def changed(self, what):
        if what[0] is self.CHANGED_SPECIFIC:
            if what[1] is iPlayableService.evStart or what[1] is iPlayableService.evUpdatedInfo:
                self.initTimer.start(20, True)
            elif what[1] is iPlayableService.evEnd:
                self.clearData()
                Converter.changed(self, what)