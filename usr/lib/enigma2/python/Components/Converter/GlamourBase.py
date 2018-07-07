#  GlamourBase converter
#  Modded and recoded by MCelliotG for use in Glamour skins or standalone
#  If you use this Converter for other skins and rename it, please keep the first and second line

from Components.Converter.Converter import Converter
from Components.Element import cached
from Poll import Poll 
import NavigationInstance
from ServiceReference import ServiceReference, resolveAlternate 
from enigma import iServiceInformation, iPlayableService, iPlayableServicePtr, eServiceCenter
from string import upper 
from Tools.Transponder import ConvertToHumanReadable, getChannelNumber
from os import rename, system
from Components.config import config

class GlamourBase(Poll, Converter, object):
    FREQINFO = 0
    ORBITAL = 1
    RESCODEC = 2
    PIDINFO = 3
    PIDHEXINFO = 4
    VIDEOCODEC = 5
    FPS = 6
    VIDEOSIZE = 7
    IS1080 = 8
    IS720 = 9
    IS576 = 10
    IS1440 = 11
    IS2160 = 12
    IS480 = 13
    IS360 = 14
    IS240 = 15
    IS144 = 16
    ISPROGRESSIVE = 17
    ISINTERLACED = 18
    HASMPEG2 = 19
    HASAVC = 20
    HASMPEG1 = 21
    HASMPEG4VC = 22
    HASVC1 = 23
    HASVC1SM = 24
    HASHEVC = 25
    STREAMURL = 26
    STREAMTYPE = 27
    ISSTREAMING = 28


    def __init__(self, type):
        Converter.__init__(self, type)
        self.type = type
        self.short_list = True
        Poll.__init__(self)
        self.poll_interval = 1000
        self.poll_enabled = True
        self.list = []
        if "FreqInfo" in type:
            self.type = self.FREQINFO
        elif "Orbital" in type:
            self.type = self.ORBITAL
        elif "ResCodec" in type:
            self.type = self.RESCODEC 
        elif "VideoCodec" in type:
            self.type = self.VIDEOCODEC
        elif "Fps" in type:
            self.type = self.FPS
        elif "VideoSize" in type:
            self.type = self.VIDEOSIZE
        elif "PidInfo" in type:
            self.type = self.PIDINFO
        elif "PidHexInfo" in type:
            self.type = self.PIDHEXINFO
        elif "Is1080" in type:
            self.type = self.IS1080
        elif "Is720" in type:
            self.type = self.IS720
        elif "Is576" in type:
            self.type = self.IS576
        elif "Is1440" in type:
            self.type = self.IS1440
        elif "Is2160" in type:
            self.type = self.IS2160
        elif "Is480" in type:
            self.type = self.IS480
        elif "Is360" in type:
            self.type = self.IS360
        elif "Is240" in type:
            self.type = self.IS240
        elif "Is144" in type:
            self.type = self.IS144
        elif "IsProgressive" in type:
            self.type = self.ISPROGRESSIVE
        elif "IsInterlaced" in type:
            self.type = self.ISINTERLACED
        elif "HasMPEG2" in type:
            self.type = self.HASMPEG2
        elif "HasAVC" in type:
            self.type = self.HASAVC
        elif "HasMPEG1" in type:
            self.type = self.HASMPEG1
        elif "HasMPEG4VC" in type:
            self.type = self.HASMPEG4VC
        elif "HasVC1" in type:
            self.type = self.HASVC1
        elif "HasVC1SM" in type:
            self.type = self.HASVC1SM
        elif "HasHEVC" in type:
            self.type = self.HASHEVC
        elif "StreamUrl" in type:
            self.type = self.STREAMURL
        elif "StreamType" in type:
            self.type = self.STREAMTYPE
        elif "IsStreaming" in type:
            self.type = self.ISSTREAMING


######### COMMON VARIABLES #################
    def videosize(self, info):
        xresol = info.getInfo(iServiceInformation.sVideoWidth)
        yresol = info.getInfo(iServiceInformation.sVideoHeight)
        progrs = ("i", "p", "", " ")[info.getInfo(iServiceInformation.sProgressive)]
        if (xresol > 0):
            videosize = str(xresol) + "x" + str(yresol) + str(progrs)
            return videosize
        else:
            return ""

    def framerate(self, info):
        fps = info.getInfo(iServiceInformation.sFrameRate)
        if (fps < 0) or (fps == -1):
            return ""
        fps = "%6.3f" % (fps/1000.)
        return str(fps.replace(".000","")) + " fps "

    def videocodec(self, info):
        vcodec =  ("MPEG2", "AVC", "MPEG1", "MPEG4-VC", "VC1", "VC1-SM", "HEVC", "")[info.getInfo(iServiceInformation.sVideoType)]
        return str(vcodec)

    def frequency(self, tp):
        freq = (tp.get("frequency") + 500)
        if freq:
            frequency = str(int(freq) / 1000)
            return frequency
        else:
            return ""

    def terrafreq(self, tp):
        return str(int(tp.get("frequency") + 1) / 1000000)

    def channel(self, tpinfo):
        return str(tpinfo.get("channel")) or ""

    def symbolrate(self, tp):
        return str(int(tp.get("symbol_rate", 0) / 1000))

    def polarization(self, tpinfo):
        return str(tpinfo.get("polarization_abbreviation")) or ""

    def fecinfo(self, tpinfo):
        return str(tpinfo.get("fec_inner")) or ""

    def tunernumber(self, tpinfo):
        return str(tpinfo.get("tuner_number")) or ""

    def system(self, tpinfo):
        return str(tpinfo.get("system")) or ""

    def modulation(self, tpinfo):
        return str(tpinfo.get("modulation")) or ""

    def constellation(self, tpinfo):
        return str(tpinfo.get("constellation"))

    def tunersystem(self, tpinfo):
        return str(tpinfo.get("system")) or ""

    def tunertype(self, tp):
        return str(tp.get("tuner_type")) or ""

    def terrafec(self, tpinfo):
        lp = str(tpinfo.get("code_rate_lp"))
        hp = str(tpinfo.get("code_rate_hp"))
        gi = str(tpinfo.get("guard_interval"))
        return " LP: " + lp + " HP: " + hp + " GI: " + gi

    def multistream(self, tpinfo):
        isid = str(tpinfo.get("is_id", 0)) 
        plscode = str(tpinfo.get("pls_code", 0))
        plsmode = str(tpinfo.get("pls_mode", None))
        if (plsmode == "None") or (isid == "-1") or (isid == "255") or ((isid == "0") and (plscode == "1")) or ((isid == "0") and (plsmode == "Gold")):
            isid = plscode = plsmode = ""
        else:
            isid = (" IS:") + isid
            plscode = (" ") + plscode.replace("262143","")
            plsmode = (" ") + plsmode.replace("Unknown","")
        return isid + plsmode + plscode 

    def satname(self, tp):
        orbpos = tp.get("orbital_position")
        orbpos = int(orbpos)
        orbe = float(orbpos)/10.0
        orbw = float(orbpos - 3600)/10.0
        if (orbe >= 179.7) and (orbe <= 180.3):
            sat = "Intelsat 18"
        elif (orbe >= 173.5) and (orbe <= 174.5):
            sat = "Eutelsat 174A"
        elif (orbe >= 171.7) and (orbe <= 172.3):
            sat = "Eutelsat 172A,172B"
        elif (orbe >= 168.7) and (orbe <= 169.3):
            sat = "Intelsat 805"
        elif (orbe >= 165.7) and (orbe <= 166.3):
            sat = "Intelsat 19"
        elif (orbe >= 163.7) and (orbe <= 164.3):
            sat = "Optus 10"
        elif (orbe >= 161.7) and (orbe <= 162.3):
            sat = "Superbird B2/JCSat 16"
        elif (orbe >= 159.7) and (orbe <= 160.3):
            sat = "Optus D1"
        elif (orbe >= 158.7) and (orbe <= 159.3):
            sat = "ABS 6"
        elif (orbe >= 155.7) and (orbe <= 156.3):
            sat = "Optus C1,D3"
        elif (orbe >= 153.7) and (orbe <= 154.3):
            sat = "JCSat 2B"
        elif (orbe >= 151.7) and (orbe <= 152.3):
            sat = "Optus D2" 
        elif (orbe >= 149.7) and (orbe <= 150.3):
            sat = "JCSat 1B"
        elif (orbe >= 143.7) and (orbe <= 144.3):
            sat = "Superbird C2"
        elif (orbe >= 141.7) and (orbe <= 142.3):
            sat = "Apstar 9"
        elif (orbe >= 139.7) and (orbe <= 140.3):
            sat = "Express AM5,AT2"
        elif (orbe >= 137.7) and (orbe <= 138.3):
            sat = "Telstar 18"
        elif (orbe >= 135.7) and (orbe <= 136.3):
            sat = "JCSat 2A"
        elif (orbe >= 133.7) and (orbe <= 134.3):
            sat = "Apstar 6"
        elif (orbe >= 130.7) and (orbe <= 132.3):
            sat = "Vinasat 1,2/JCSat 5A"
        elif (orbe >= 128.4) and (orbe <= 128.8):
            sat = "LaoSat 1"
        elif (orbe >= 127.8) and (orbe <= 128.3):
            sat = "JCSat 3A"
        elif (orbe >= 124.8) and (orbe <= 125.3):
            sat = "ChinaSat 6A"
        elif (orbe >= 123.8) and (orbe <= 124.3):
            sat = "JCSat 4B"
        elif (orbe >= 120.8) and (orbe <= 122.5):
            sat = "AsiaSat 4"
        elif (orbe >= 119.8) and (orbe <= 120.3):
            sat = "AsiaSat 6/Thaicom 7"
        elif (orbe >= 119.2) and (orbe <= 119.7):
            sat = "Thaicom 4"
        elif (orbe >= 117.8) and (orbe <= 118.3):
            sat = "Telkom 2"
        elif (orbe >= 115.8) and (orbe <= 116.3):
            sat = "ABS 7/KoreaSat 6,7"
        elif (orbe >= 115.3) and (orbe <= 115.7):
            sat = "ChinaSat 6B"
        elif (orbe >= 112.7) and (orbe <= 113.3):
            sat = "Palapa D/KoreaSat 5"
        elif (orbe >= 110.3) and (orbe <= 110.8):
            sat = "ChinaSat 10"
        elif (orbe >= 109.7) and (orbe <= 110.2):
            sat = "BSat 3A,3C/JCSat 110R/N-Sat 110"
        elif (orbe >= 107.5) and (orbe <= 108.5):
            sat = "SES 7,9/NSS 11/Telkom 1"
        elif (orbe >= 105.3) and (orbe <= 105.8):
            sat = "AsiaSat 7"
        elif (orbe >= 104.8) and (orbe <= 105.1):
            sat = "Asiastar 1"
        elif (orbe >= 103.4) and (orbe <= 103.7):
            sat = "ChinaSat 2C"
        elif (orbe >= 102.7) and (orbe <= 103.2):
            sat = "Express AM3"
        elif (orbe >= 102.7) and (orbe <= 103.3):
            sat = "Express AM3"
        elif (orbe >= 100.0) and (orbe <= 100.7):
            sat = "AsiaSat 5"
        elif (orbe >= 97.8) and (orbe <= 98.4):
            sat = "Chinasat 11,2A"
        elif (orbe >= 97.8) and (orbe <= 98.4):
            sat = "Chinasat 11,2A"
        elif (orbe >= 96.8) and (orbe <= 97.7):
            sat = "G-Sat 9"
        elif (orbe >= 96.2) and (orbe <= 96.7):
            sat = "Express AM33"
        elif (orbe >= 94.7) and (orbe <= 95.3):
            sat = "NSS 6/SES 8"
        elif (orbe >= 93.0) and (orbe <= 93.8):
            sat = "Insat 4B/G-Sat 15"
        elif (orbe >= 92.0) and (orbe <= 92.5):
            sat = "ChinaSat 9"
        elif (orbe >= 91.3) and (orbe <= 91.8):
            sat = "Measat 3A,3B"
        elif (orbe >= 88.8) and (orbe <= 90.3):
            sat = "Yamal 401"
        elif (orbe >= 87.8) and (orbe <= 88.3):
            sat = "ST 2"
        elif (orbe >= 87.2) and (orbe <= 87.7):
            sat = "ChinaSat 12"
        elif (orbe >= 86.2) and (orbe <= 86.8):
            sat = "KazSat 2"
        elif (orbe >= 84.8) and (orbe <= 85.5):
            sat = "Intelsat 15/Horizons 2"
        elif (orbe >= 82.8) and (orbe <= 83.3):
            sat = "Insat 4A/G-Sat 10,12"
        elif (orbe >= 81.8) and (orbe <= 82.3):
            sat = "JCSat 4A"
        elif (orbe >= 81.2) and (orbe <= 81.7):
            sat = "Chinasat 1C"
        elif (orbe >= 79.8) and (orbe <= 80.4):
            sat = "Express AM22"
        elif (orbe >= 78.3) and (orbe <= 78.8):
            sat = "ThaiCom 5,6,8"
        elif (orbe >= 76.3) and (orbe <= 76.8):
            sat = "Apstar 7"
        elif (orbe >= 74.7) and (orbe <= 75.4):
            sat = "ABS 2,2A"
        elif (orbe >= 73.7) and (orbe <= 74.4):
            sat = "G-Sat 7,18"
        elif (orbe >= 71.7) and (orbe <= 72.4):
            sat = "Intelsat 22"
        elif (orbe >= 70.3) and (orbe <= 70.8):
            sat = "Eutelsat 70B"
        elif (orbe >= 69.8) and (orbe <= 70.2):
            sat = "Raduga-1M 3"
        elif (orbe >= 68.0) and (orbe <= 68.8):
            sat = "Intelsat 20"
        elif (orbe >= 65.8) and (orbe <= 66.3):
            sat = "Intelsat 17"
        elif (orbe >= 64.8) and (orbe <= 65.3):
            sat = "Amos 4"
        elif (orbe >= 63.8) and (orbe <= 64.4):
            sat = "Intelsat 906"
        elif (orbe >= 62.9) and (orbe <= 63.2):
            sat = "ComsatBW-1"
        elif (orbe >= 61.7) and (orbe <= 62.3):
            sat = "Intelsat 902"
        elif (orbe >= 60.8) and (orbe <= 61.2):
            sat = "ABS 4"
        elif (orbe >= 60.3) and (orbe <= 60.4):
            sat = "Astra 2C"
        elif (orbe >= 59.4) and (orbe <= 60.2):
            sat = "Intelsat 33e"
        elif (orbe >= 58.8) and (orbe <= 59.3):
            sat = "Eutelsat 59A"
        elif (orbe >= 58.3) and (orbe <= 58.7):
            sat = "KazSat 3"
        elif (orbe >= 56.8) and (orbe <= 57.3):
            sat = "NSS 12"
        elif (orbe >= 55.7) and (orbe <= 56.3):
            sat = "Express AT1"
        elif (orbe >= 55.0) and (orbe <= 55.4):
            sat = "Yamal 402/G-Sat 8,16"
        elif (orbe >= 54.6) and (orbe <= 54.9):
            sat = "Yamal 402"
        elif (orbe >= 52.8) and (orbe <= 53.3):
            sat = "Express AM6"
        elif (orbe >= 52.3) and (orbe <= 52.7):
            sat = "Al Yah 1"
        elif (orbe >= 51.8) and (orbe <= 52.2):
            sat = "TurkmenÄlem/MonacoSat"
        elif (orbe >= 51.2) and (orbe <= 51.7):
            sat = "Belintersat 1"
        elif (orbe >= 50.4) and (orbe <= 50.7):
            sat = "NSS 5"
        elif (orbe >= 49.7) and (orbe <= 50.3):
            sat = "Türksat 4B"
        elif (orbe >= 48.7) and (orbe <= 49.3):
            sat = "Yamal 202"
        elif (orbe >= 47.8) and (orbe <= 48.5):
            sat = "Eutelsat 48D"
        elif (orbe >= 47.6) and (orbe <= 47.7):
            sat = "Yahsat 1B"
        elif (orbe >= 47.2) and (orbe <= 47.5):
            sat = "Intelsat 10"
        elif (orbe >= 45.7) and (orbe <= 46.3):
            sat = "AzerSpace 1/Africasat 1A"
        elif (orbe >= 44.7) and (orbe <= 45.3):
            sat = "Intelsat 12,904"
        elif (orbe >= 44.4) and (orbe <= 44.6):
            sat = "Astra 1F"
        elif (orbe >= 43.9) and (orbe <= 44.1):
            sat = "Thuraya 2"
        elif (orbe >= 42.4) and (orbe <= 42.6):
            sat = "Nigcomsat 1R"
        elif (orbe >= 41.7) and (orbe <= 42.3):
            sat = "Türksat 2A,3A,4A"
        elif (orbe >= 39.8) and (orbe <= 40.3):
            sat = "Express AM7"
        elif (orbe >= 38.7) and (orbe <= 39.3):
            sat = "HellasSat 2,3"
        elif (orbe >= 37.9) and (orbe <= 38.5):
            sat = "Paksat 1R"
        elif (orbe >= 37.6) and (orbe <= 37.8):
            sat = "Athena-Fidus"
        elif (orbe >= 35.7) and (orbe <= 36.3):
            sat = "Eutelsat 36B,36C"
        elif (orbe >= 32.9) and (orbe <= 33.3):
            sat = "Eutelsat 33C,33E"
        elif (orbe >= 32.6) and (orbe <= 32.8):
            sat = "Intelsat 28"
        elif (orbe >= 31.2) and (orbe <= 31.8):
            sat = "Astra 5B"
        elif (orbe >= 30.9) and (orbe <= 31.1):
            sat = "Eutelsat 31A/Hylas 2"
        elif (orbe >= 30.7) and (orbe <= 30.8):
            sat = "Eutelsat 31A"
        elif (orbe >= 30.2) and (orbe <= 30.6):
            sat = "Arabsat 5A"
        elif (orbe >= 28.0) and (orbe <= 28.8):
            sat = "Astra 2E,2F,2G"
        elif (orbe >= 25.8) and (orbe <= 26.3):
            sat = "Badr 4,5,6,7"
        elif (orbe >= 25.0) and (orbe <= 25.7):
            sat = "Eutelsat 25B,Es'hail 1"
        elif (orbe >= 23.0) and (orbe <= 23.8):
            sat = "Astra 3B"
        elif (orbe >= 21.4) and (orbe <= 21.8):
            sat = "Eutelsat 21B"
        elif (orbe >= 20.8) and (orbe <= 21.2):
            sat = "AfriStar 1"
        elif (orbe >= 19.8) and (orbe <= 20.5):
            sat = "Arabsat 5C"
        elif (orbe >= 18.8) and (orbe <= 19.5):
            sat = "Astra 1KR,1L,1M,1N"
        elif (orbe >= 15.6) and (orbe <= 16.3):
            sat = "Eutelsat 16A"
        elif (orbe >= 12.7) and (orbe <= 13.5):
            sat = "HotBird 13B,13C,13E"
        elif (orbe >= 11.5) and (orbe <= 11.9):
            sat = "Sicral 1B"
        elif (orbe >= 9.7) and (orbe <= 10.3):
            sat = "Eutelsat 10A"
        elif (orbe >= 8.7) and (orbe <= 9.3):
            sat = "Eutelsat 9B,Ka-Sat"
        elif (orbe >= 6.7) and (orbe <= 7.3):
            sat = "Eutelsat 7A,7B"
        elif (orbe >= 4.5) and (orbe <= 5.4):
            sat = "Astra 4A/SES 5"
        elif (orbe >= 3.0) and (orbe <= 3.6):
            sat = "Eutelsat 3B"
        elif (orbe >= 2.5) and (orbe <= 2.9):
            sat = "Rascom QAF 1R"
        elif (orbe >= 1.4) and (orbe <= 2.4):
            sat = "BulgariaSat-1"
        elif (orbw <= -0.5) and (orbw >= -1.2):
            sat = "Thor 5,6,7/Intelsat 10-02"
        elif (orbw <= -2.7) and (orbw >= -3.3):
            sat = "ABS 3A"
        elif (orbw <= -3.7) and (orbw >= -4.2):
            sat = "Amos 3,7"
        elif (orbw <= -4.3) and (orbw >= -4.4):
            sat = "Amos 3,7/Thor 3"
        elif (orbw <= -4.7) and (orbw >= -5.4):
            sat = "Eutelsat 5 West A"
        elif (orbw <= -6.7) and (orbw >= -7.2):
            sat = "Nilesat 201/Eutelsat 7WA"
        elif (orbw <= -7.3) and (orbw >= -7.4):
            sat = "Eutelsat 7 West A"
        elif (orbw <= -7.5) and (orbw >= -7.7):
            sat = "Eutelsat 7WA,8WB"
        elif (orbw <= -7.8) and (orbw >= -8.3):
            sat = "Eutelsat 8 West B"
        elif (orbw <= -10.7) and (orbw >= -11.3):
            sat = "Express AM44"
        elif (orbw <= -12.0) and (orbw >= -12.8):
            sat = "Eutelsat 12 West B"
        elif (orbw <= -13.8) and (orbw >= -14.3):
            sat = "Express AM8"
        elif (orbw <= -14.8) and (orbw >= -15.3):
            sat = "Telstar 12 Vantage"  
        elif (orbw <= -17.8) and (orbw >= -18.3):
            sat = " Intelsat 37e"  
        elif (orbw <= -19.8) and (orbw >= -20.3):
            sat = "NSS 7"
        elif (orbw <= -21.8) and (orbw >= -22.4):
            sat = "SES 4"
        elif (orbw <= -24.2) and (orbw >= -24.6):
            sat = "Intelsat 905" 
        elif (orbw <= -24.7) and (orbw >= -25.2):
            sat = " AlcomSat 1" 
        elif (orbw <= -27.2) and (orbw >= -27.8):
            sat = "Intelsat 907" 
        elif (orbw <= -29.3) and (orbw >= -29.7):
            sat = "Intelsat 701"
        elif (orbw <= -29.8) and (orbw >= -30.5):
            sat = "Hispasat 30W-5,30W-6"
        elif (orbw <= -31.2) and (orbw >= -31.8):
            sat = "Intelsat 25"
        elif (orbw <= -33.3) and (orbw >= -33.7):
            sat = "Hylas 1"
        elif (orbw <= -34.2) and (orbw >= -34.8):
            sat = "Intelsat 35e"
        elif (orbw <= -35.7) and (orbw >= -36.3):
            sat = "Eutelsat 36 W1"
        elif (orbw <= -37.2) and (orbw >= -37.7):
            sat = "NSS 10/Telstar 11N"
        elif (orbw <= -40.2) and (orbw >= -40.8):
            sat = "SES 6"
        elif (orbw <= -42.7) and (orbw >= -43.5):
            sat = "Intelsat 9,32a/Sky Brasil 1"
        elif (orbw <= -44.7) and (orbw >= -45.3):
            sat = "Intelsat 14"
        elif (orbw <= -47.2) and (orbw >= -47.8):
            sat = "NSS 806"
        elif (orbw <= -49.8) and (orbw >= -50.3):
            sat = "Intelsat 29E,1R"
        elif (orbw <= -52.7) and (orbw >= -53.3):
            sat = "Intelsat 23"
        elif (orbw <= -53.7) and (orbw >= -54.3):
            sat = "Inmarsat-3 F5"
        elif (orbw <= -55.2) and (orbw >= -55.8):
            sat = "Intelsat 34"
        elif (orbw <= -57.7) and (orbw >= -58.3):
            sat = "Intelsat 16,21"
        elif (orbw <= -59.7) and (orbw >= -61.3):
            sat = "Amazonas 2,3,5"
        elif (orbw <= -61.4) and (orbw >= -61.7):
            sat = "EchoStar 12,15,16,18"
        elif (orbw <= -61.8) and (orbw >= -62.1):
            sat = "EchoStar 3"
        elif (orbw <= -62.8) and (orbw >= -63.2):
            sat = "Telstar 14R"
        elif (orbw <= -64.7) and (orbw >= -65.3):
            sat = "Eutelsat 65WA/Star One C1"
        elif (orbw <= -66.7) and (orbw >= -67.5):
            sat = "SES 10/AMC 4,6"
        elif (orbw <= -69.7) and (orbw >= -70.3):
            sat = "Star One C2,C4"
        elif (orbw <= -71.5) and (orbw >= -71.8):
            sat = "Arsat 1"
        elif (orbw <= -72.0) and (orbw >= -72.3):
            sat = "Arsat 1/AMC 3"
        elif (orbw <= -72.4) and (orbw >= -72.8):
            sat = "Nimiq 5"
        elif (orbw <= -74.7) and (orbw >= -75.3):
            sat = "Star One C3"
        elif (orbw <= -76.7) and (orbw >= -77.3):
            sat = "QuetzSat 1"
        elif (orbw <= -77.7) and (orbw >= -78.3):
            sat = "Simón Bolívar"
        elif (orbw <= -78.5) and (orbw >= -79.2):
            sat = "Sky Mexico 1"
        elif (orbw <= -80.7) and (orbw >= -81.3):
            sat = "Arsat 2"
        elif (orbw <= -81.7) and (orbw >= -82.3):
            sat = "Nimiq 4"
        elif (orbw <= -82.7) and (orbw >= -83.3):
            sat = "AMC 9"
        elif (orbw <= -83.6) and (orbw >= -83.9):
            sat = "Hispasat 84W-1"
        elif (orbw <= -84.0) and (orbw >= -84.3):
            sat = "Star One D1"
        elif (orbw <= -84.7) and (orbw >= -85.5):
            sat = "AMC 16/Sirius XM3,XM5"
        elif (orbw <= -86.0) and (orbw >= -86.5):
            sat = "Sirius FM5"
        elif (orbw <= -86.7) and (orbw >= -87.5):
            sat = "SES 2/TKSat 1"
        elif (orbw <= -88.7) and (orbw >= -89.3):
            sat = "Galaxy 28"
        elif (orbw <= -90.7) and (orbw >= -91.3):
            sat = "Nimiq 6/Galaxy 17"
        elif (orbw <= -92.7) and (orbw >= -93.4):
            sat = "Galaxy 25"
        elif (orbw <= -94.7) and (orbw >= -95.4):
            sat = "Galaxy 3C/Intelsat 30,31"
        elif (orbw <= -96.7) and (orbw >= -97.4):
            sat = "Galaxy 19/EchoStar 19"
        elif (orbw <= -98.8) and (orbw >= -99.5):
            sat = "Galaxy 16/DirecTV 11,14"
        elif (orbw <= -100.7) and (orbw >= -101.4):
            sat = "SES 1/DirecTV 8,4S"
        elif (orbw <= -102.5) and (orbw >= -102.8):
            sat = "DirecTV 15"
        elif (orbw <= -102.9) and (orbw >= -103.4):
            sat = "SES 3/DirecTV 10,12"
        elif (orbw <= -104.7) and (orbw >= -105.4):
            sat = "AMC 15,18/SES-11"
        elif (orbw <= -106.8) and (orbw >= -107.1):
            sat = "EchoStar 17"
        elif (orbw <= -107.2) and (orbw >= -107.6):
            sat = "Anik F1R,G1"
        elif (orbw <= -108.8) and (orbw >= -109.5):
            sat = "Telstar 12"
        elif (orbw <= -109.7) and (orbw >= -110.4):
            sat = "EchoStar 10,12/DirecTV 5"
        elif (orbw <= -110.8) and (orbw >= -111.5):
            sat = "Anik F2"
        elif (orbw <= -112.7) and (orbw >= -113.4):
            sat = "Eutelsat 113 West A"
        elif (orbw <= -114.6) and (orbw >= -114.8):
            sat = "Mexsat Bicentenario"
        elif (orbw <= -114.9) and (orbw >= -115.4):
            sat = "Eutelsat 115 West B"
        elif (orbw <= -116.6) and (orbw >= -117.4):
            sat = "Eutelsat 117 West A,B"
        elif (orbw <= -118.7) and (orbw >= -119.4):
            sat = "Anik F3/DTV 75/EchoStar 14"
        elif (orbw <= -120.7) and (orbw >= -121.4):
            sat = "EchoStar 9/Galaxy 23"
        elif (orbw <= -122.7) and (orbw >= -123.4):
            sat = "Galaxy 18"
        elif (orbw <= -124.7) and (orbw >= -125.4):
            sat = "AMC 21/Galaxy 14"
        elif (orbw <= -126.7) and (orbw >= -127.4):
            sat = "Galaxy 13/Horizons 1"
        elif (orbw <= -128.7) and (orbw >= -129.4):
            sat = "Ciel 2/Galaxy 12"
        elif (orbw <= -130.7) and (orbw >= -131.4):
            sat = "AMC 11"
        elif (orbw <= -132.7) and (orbw >= -133.4):
            sat = "Galaxy 15"
        elif (orbw <= -134.7) and (orbw >= -135.4):
            sat = "AMC 10"
        elif (orbw <= -138.7) and (orbw >= -139.4):
            sat = "AMC 8"
        elif (orbw <= -176.7) and (orbw >= -177.4):
            sat = "NSS 9/Yamal 300K"
        else:
            sat = "Satellite:"
        return str(sat)

    def orbital(self, tp):
        orbp = tp.get("orbital_position")
        if orbp > 1800:
            orbp = str((float(3600 - orbp))/10.0) + "°W"
        else:
            orbp = str((float(orbp))/10.0) + "°E"
        return orbp

    def reference(self):
        playref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
        if playref:
            refstr = playref.toString() or ""
            return refstr

    def streamtype(self):
        playref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
        if playref:
            refstr = playref.toString()
            strtype = refstr.replace("%3a", ":")
            if "0.0.0.0:" in strtype and (strtype.startswith("1:0:")) or "127.0.0.1:" in strtype and (strtype.startswith("1:0:")) or "localhost:" in strtype and (strtype.startswith("1:0:")):
                return "Internal TS Relay"
            if not (strtype.startswith("1:0:")):
                return "IPTV/Non-TS Stream"
            if "%3a/" in refstr and (strtype.startswith("1:0:")):
                return "IPTV/TS Stream"
            if (strtype.startswith("1:134:")):
                return "Alternative"
            else:
                return ""

    def streamurl(self):
        playref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
        if playref:
            refstr = playref.toString()
            if "%3a/" in refstr or ":/" in refstr:
                strurl = refstr.split(":")
                streamurl = strurl[10].replace("%3a",":")
                return streamurl
            else:
                return ""

    def pidstring(self, info):
        vpid = info.getInfo(iServiceInformation.sVideoPID)
        if (vpid < 0):
            vpid = ""
        else:
            vpid = "VPID:" + str(vpid).zfill(4)
        apid = info.getInfo(iServiceInformation.sAudioPID)
        if (apid < 0):
            apid = ""
        else:
            apid = "APID:" + str(apid).zfill(4)
        sid = info.getInfo(iServiceInformation.sSID)
        if (sid < 0):
            sid = ""
        else:
            sid = "SID:" + str(sid).zfill(4)
        pcrpid = info.getInfo(iServiceInformation.sPCRPID)
        if (pcrpid < 0):
            pcrpid = ""
        else:
            pcrpid = "PCR:" + str(pcrpid).zfill(4)
        pmtpid = info.getInfo(iServiceInformation.sPMTPID)
        if (pmtpid < 0):
            pmtpid = ""
        else:
            pmtpid = "PMT:" + str(pmtpid).zfill(4)
        tsid = info.getInfo(iServiceInformation.sTSID)
        if (tsid < 0):
            tsid = ""
        else:
            tsid = "TSID:" + str(tsid).zfill(4)
        onid = info.getInfo(iServiceInformation.sONID)
        if (onid < 0):
            onid = ""
        else:
            onid = "ONID:" + str(onid).zfill(4)
        if (vpid >= 0) or (apid >= 0) or (sid >= 0) or (tsid >= 0) or (onid >= 0):
            pidinfo = vpid + " " + apid + " " + sid + " " + pcrpid + " " + pmtpid + " " + tsid + " " + onid
            return pidinfo
        else:
            return ""

    def pidhexstring(self, info):
        vpid = info.getInfo(iServiceInformation.sVideoPID)
        if (vpid < 0):
            vpid = ""
        else:
            vpid = "VPID:" + str(hex(vpid)[2:]).upper().zfill(4)
        apid = info.getInfo(iServiceInformation.sAudioPID)
        if (apid < 0):
            apid = ""
        else:
            apid = "APID:" + str(hex(apid)[2:]).upper().zfill(4)
        sid = info.getInfo(iServiceInformation.sSID)
        if (sid < 0):
            sid = ""
        else:
            sid = "SID:" + str(hex(sid)[2:]).upper().zfill(4)
        pcrpid = info.getInfo(iServiceInformation.sPCRPID)
        if (pcrpid < 0):
            pcrpid = ""
        else:
            pcrpid = "PCR:" + str(hex(pcrpid)[2:]).upper().zfill(4)
        pmtpid = info.getInfo(iServiceInformation.sPMTPID)
        if (pmtpid < 0):
            pmtpid = ""
        else:
            pmtpid = "PMT:" + str(hex(pmtpid)[2:]).upper().zfill(4)
        tsid = info.getInfo(iServiceInformation.sTSID)
        if (tsid < 0):
            tsid = ""
        else:
            tsid = "TSID:" + str(hex(tsid)[2:]).upper().zfill(4)
        onid = info.getInfo(iServiceInformation.sONID)
        if (onid < 0):
            onid = ""
        else:
            onid = "ONID:" + str(hex(onid)[2:]).upper().zfill(4)
        if (vpid >= 0) or (apid >= 0) or (sid >= 0) or (tsid >= 0) or (onid >= 0):
            pidhexinfo = vpid + " " + apid + " " + sid + " " + pcrpid + " " + pmtpid + " " + tsid + " " + onid
            return pidhexinfo
        else:
            return ""

    @cached
    def getText(self):
        service = self.source.service
        info = service and service.info()
        if not info:
            return ""
        feinfo = service.frontendInfo()
        if feinfo:
            tp = feinfo.getAll(config.usage.infobar_frontend_source.value == "settings")
            if tp:
                tpinfo = ConvertToHumanReadable(tp)
            if not tp:
                tp = info.getInfoObject(iServiceInformation.sTransponderData)
                tpinfo = ConvertToHumanReadable(tp)


        if (self.type == self.FREQINFO):
            refstr = str(self.reference())
            if "%3a/" in refstr or ":/" in refstr:
                return self.streamurl()
            else:
                if "DVB-S" in self.tunertype(tp):
                    if "is_id" in tpinfo or "pls_code" in tpinfo or "pls_mode" in tpinfo:
                        return self.system(tpinfo) + " " + self.modulation(tpinfo) + " " + self.frequency(tp) + " " + self.polarization(tpinfo) + " " + self.symbolrate(tp) + " " + self.fecinfo(tpinfo) + self.multistream(tpinfo)
                    else:
                        return self.system(tpinfo) + " " + self.modulation(tpinfo) + " " + self.frequency(tp) + " " + self.polarization(tpinfo) + " " + self.symbolrate(tp) + " " + self.fecinfo(tpinfo)
                elif "DVB-C" in self.tunertype(tp):
                    return self.frequency(tp) + " Mhz " + " " + self.modulation(tpinfo) + "  SR:" + self.symbolrate(tp) + "  " + "FEC:" + self.fecinfo(tpinfo)
                elif "DVB-T" in self.tunertype(tp):
                    return self.channel(tpinfo) + " (" + self.terrafreq(tp) + " Mhz)" + " " + self.constellation(tpinfo) + self.terrafec(tpinfo)
                elif "ATSC" in self.tunertype(tp):
                    return self.terrafreq(tp) + " Mhz " + " " + self.modulation(tpinfo)
                return ""

        elif (self.type == self.ORBITAL):
            refstr = str(self.reference())
            if "%3a/" in refstr or ":/" in refstr:
                return self.streamtype()
            else:
                if "DVB-S" in self.tunertype(tp):
                    return self.satname(tp) + " (" + self.orbital(tp) + ")"
                elif "DVB-C" in self.tunertype(tp) or "DVB-T" in self.tunertype(tp) or "ATSC" in self.tunertype(tp):
                    return self.system(tpinfo)
                return ""

        elif (self.type == self.VIDEOCODEC):
            return self.videocodec(info)

        elif (self.type == self.FPS):
            return self.framerate(info)

        elif (self.type == self.VIDEOSIZE):
            return self.videosize(info)

        elif (self.type == self.RESCODEC):
            vidsize = self.videosize(info)
            fps = self.framerate(info)
            vidcodec = self.videocodec(info)
            return vidsize + "   " + fps + "   " + vidcodec

        elif (self.type == self.PIDINFO):
            return self.pidstring(info)

        elif (self.type == self.PIDHEXINFO):
            return self.pidhexstring(info)

        elif (self.type == self.STREAMURL):
            return str(self.streamurl())

        elif (self.type == self.PIDHEXINFO):
            return str(self.streamtype())
    text = property(getText)


    @cached
    def getBoolean(self):
        service = self.source.service
        info = service and service.info()
        if not info:
            return False
        else: 
            xresol = info.getInfo(iServiceInformation.sVideoWidth)
            yresol = info.getInfo(iServiceInformation.sVideoHeight)
            progrs = ("i", "p", "", " ")[info.getInfo(iServiceInformation.sProgressive)]
            vcodec =  ("MPEG2", "AVC", "MPEG1", "MPEG4-VC", "VC1", "VC1-SM", "HEVC", "")[info.getInfo(iServiceInformation.sVideoType)]
            streamurl = self.streamurl()
            if (self.type == self.IS1080):
                if (xresol >= 1880) and (xresol <= 2000) or (yresol >= 900) and (yresol <= 1090):
                    return True
                return False
            elif (self.type == self.IS720):
                if (yresol >= 640) and (yresol <= 740):
                    return True
                return False
            elif (self.type == self.IS576):
                if (yresol >= 540) and (yresol <= 580):
                    return True
                return False
            elif (self.type == self.IS1440):
                if (xresol >= 2550) and (xresol <= 2570) or (yresol >= 1430) and (yresol <= 1450):
                    return True
                return False
            elif (self.type == self.IS2160):
                if (xresol >= 3820) and (xresol <= 4100) or (yresol >= 2150) and (yresol <= 2170):
                    return True
                return False
            elif (self.type == self.IS480):
                if (yresol >= 380) and (yresol <= 500):
                    return True
                return False
            elif (self.type == self.IS360):
                if (yresol >= 320) and (yresol <= 370):
                    return True
                return False
            elif (self.type == self.IS240):
                if (yresol >= 200) and (yresol <= 260):
                    return True
                return False
            elif (self.type == self.IS144):
                if (yresol >= 130) and (yresol <= 160):
                    return True
                return False
            elif (self.type == self.ISPROGRESSIVE):
                if progrs == "p":
                    return True
                return False
            elif (self.type == self.ISINTERLACED):
                if progrs == "i":
                    return True
                return False
            elif (self.type == self.HASMPEG2):
                if vcodec == "MPEG2":
                    return True
                return False
            elif (self.type == self.HASAVC):
                if vcodec == "AVC":
                    return True
                return False
            elif (self.type == self.HASMPEG1):
                if vcodec == "MPEG1":
                    return True
                return False
            elif (self.type == self.HASMPEG4VC):
                if vcodec == "MPEG4-VC":
                    return True
                return False
            elif (self.type == self.HASVC1):
                if vcodec == "VC1":
                    return True
                return False
            elif (self.type == self.HASVC1SM):
                if vcodec == "VC1-SM":
                    return True
                return False
            elif (self.type == self.HASHEVC):
                if vcodec == "HEVC":
                    return True
                return False
            elif (self.type == self.ISSTREAMING):
                if streamurl:
                    return True
                return False

    boolean = property(getBoolean)

    def changed(self, what):
        if what[0] == self.CHANGED_SPECIFIC and what[1] == iPlayableService.evUpdatedInfo or what[0] == self.CHANGED_POLL:
            Converter.changed(self, what)