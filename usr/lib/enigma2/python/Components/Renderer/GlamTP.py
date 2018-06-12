#  GlamTP renderer
#  Modded and recoded by MCelliotG for use in Glamour skins or standalone
#  If you use this Renderer for other skins and rename it, please keep the first and second line adding your credits below

from Renderer import Renderer
from enigma import eLabel
from Components.VariableText import VariableText
from enigma import eServiceCenter, iServiceInformation, eDVBFrontendParametersSatellite
from Tools.Transponder import ConvertToHumanReadable
class GlamTP(VariableText, Renderer):
    __module__ = __name__

    def __init__(self):
        Renderer.__init__(self)
        VariableText.__init__(self)


    GUI_WIDGET = eLabel

    def connect(self, source):
        Renderer.connect(self, source)
        self.changed((self.CHANGED_DEFAULT))


    def changed(self, what):
        if self.instance:
            if (what[0] == self.CHANGED_CLEAR):
                self.text = " "
            else:
                service = self.source.service
                info = eServiceCenter.getInstance().info(service)
                if (info and service):
                    tp = info.getInfoObject(service, iServiceInformation.sTransponderData)
                    tpinfo = ConvertToHumanReadable(tp)
                    refstr = str(self.source.service.toString())
                    curref = refstr.replace("%3a", ":")
                    streamtype = streamurl = freq = terra = ch = pol = sys = mod = const = fec = sr = orbpos = ""
                    try:
                        if curref.startswith("1:7:"):
                            curref = ""
                        if "%3a/" in refstr or ":/" in refstr:
                            strurl = refstr.split(":")
                            streamurl = strurl[10].replace("%3a",":")
                        if refstr.startswith("1:0:2"):
                            streamtype = "Radio"
                        elif not curref.startswith("1:0:") and "%3a/" in refstr:
                            streamtype = "Stream"
                        elif curref.startswith("1:0:") and "%3a/" in refstr:
                            if "0.0.0.0:" in curref or "127.0.0.1:" in curref or "localhost:" in curref:
                                streamtype = "TS Relay"
                            else:
                                streamtype = "TS Stream"
                        elif curref.startswith("1:134:"):
                            streamtype = "Alternative"
                        else:
                            streamurl = streamtype = ""
                        if "channel" in tpinfo: 
                            try:
                                ch = (str(tpinfo.get("channel")) + "/")
                            except:
                                ch = " "
                        if "system" in tp:
                            try:
                                sys = (str(tpinfo.get("system")) + " ")
                                if "DVB-S" in sys or "DVB-C" in sys:
                                    freq = (str(int(tp["frequency"]) / 1000) + " ")
                                elif "DVB-T" in sys or "ATSC" in sys:
                                    terra = (str(int(tp["frequency"]) / 1000000) + " Mhz ")
                                else:
                                    freq = terra = " "
                            except:
                                sys = " N/A "
                        if "modulation" in tp: 
                            try:
                                mod = (str(tpinfo.get("modulation")) + " ")
                            except:
                                mod = " " 
                        if "polarization" in tp:
                            try:
                                pol = {eDVBFrontendParametersSatellite.Polarisation_Horizontal: "H ",
                                 eDVBFrontendParametersSatellite.Polarisation_Vertical: "V ",
                                 eDVBFrontendParametersSatellite.Polarisation_CircularLeft: "L ",
                                 eDVBFrontendParametersSatellite.Polarisation_CircularRight: "R "}[tp["polarization"]]
                            except:
                                pol = " N/A "
                        if "constellation" in tp:
                            try:
                                const = (str(tpinfo.get("constellation")) + " ")
                            except:
                                const = " "
                        if "fec_inner" in tp:
                            try:
                                fec = (str(tpinfo.get("fec_inner")) + " ")
                            except:
                                fec = " N/A "
                        if "symbol_rate" in tp:
                            sr = (str(int(tp["symbol_rate"]) / 1000) + " ")
                        if "orbital_position" in tp:
                            orbpos = (int(tp["orbital_position"]))
                            if orbpos > 1800:
                              orbpos = (str((float(3600 - orbpos))/10.0) + "°W ")
                            else:
                              orbpos = (str((float(orbpos))/10.0) + "°E ")
                    except:
                        pass
                    self.text = (streamtype + " " + streamurl + orbpos + ch + freq + terra + pol + sys + mod + sr + fec + const)