#  GlamTP renderer
#  Modded and recoded by MCelliotG for use in Glamour skins or standalone
#  If you use this Renderer for other skins and rename it, please keep the first and second line adding your credits below

from Renderer import Renderer
from enigma import eLabel, eTimer
from Components.VariableText import VariableText
from enigma import eServiceCenter, iServiceInformation, eDVBFrontendParametersSatellite
from Tools.Transponder import ConvertToHumanReadable

class GlamTP(VariableText, Renderer):
    __module__ = __name__

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
        if self.instance:
            if (what[0] == self.CHANGED_CLEAR):
                self.text = ""
            else:
                service = self.source.service
                info = eServiceCenter.getInstance().info(service)
                if (info and service):
                    tp = info.getInfoObject(service, iServiceInformation.sTransponderData)
                    tpinfo = ConvertToHumanReadable(tp)
                    refstr = self.source.service.toString()
                    curref = refstr.replace("%3a", ":")
                    streamtype = streamurl = freq = ch = pol = sys = mod = const = fec = sr = orbpos = isid = plsmode = plscode = ""
                    try:
                        if curref.startswith("1:7:"):
                            curref = ""
                        if "%3a/" in refstr or ":/" in refstr:
                            strurl = refstr.split(":")
                            streamurl = strurl[10].replace("%3a",":")
                        if refstr.startswith("1:0:2"):
                            streamtype = "Radio "
                        elif not curref.startswith("1:0:") and "%3a/" in refstr:
                            streamtype = "Stream "
                        elif curref.startswith("1:0:") and "%3a/" in refstr:
                            if "0.0.0.0:" in curref or "127.0.0.1:" in curref or "localhost:" in curref:
                                streamtype = "TS Relay "
                            else:
                                streamtype = "TS Stream "
                        elif curref.startswith("1:134:"):
                            streamtype = "Alternative "
                        else:
                            streamurl = streamtype = ""
                        if "channel" in tpinfo: 
                            try:
                                ch = (str(tpinfo.get("channel")) + "/")
                            except:
                                ch = ""
                        if "system" in tp:
                            try:
                                sys = (str(tpinfo.get("system")) + " ")
                                if "DVB-S" in sys or "DVB-C" in sys:
                                    freq = (str(int(tp["frequency"]) / 1000))
                                elif "DVB-T" in sys or "ATSC" in sys:
                                    freq = (str(int(tp["frequency"]) / 1000000) + " Mhz ")
                                else:
                                    freq = ""
                            except:
                                sys = ""
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
                                pol = ""
                        if "constellation" in tp:
                            try:
                                const = (str(tpinfo.get("constellation")) + " ")
                            except:
                                const = ""
                        if "fec_inner" in tp:
                            try:
                                fec = (str(tpinfo.get("fec_inner")) + " ")
                            except:
                                fec = ""
                        if "symbol_rate" in tp:
                            sr = (str(int(tp["symbol_rate"]) / 1000) + " ")
                        if "orbital_position" in tp:
                            orbpos = (int(tp["orbital_position"]))
                            if orbpos > 1800:
                              orbpos = (str((float(3600 - orbpos))/10.0) + "°W ")
                            else:
                              orbpos = (str((float(orbpos))/10.0) + "°E ")
                        if "is_id" in tp or "pls_code" in tp or "pls_mode" in tp:
                            isid = str(tpinfo.get("is_id", 0))
                            plscode = str(tpinfo.get("pls_code", 0))
                            plsmode = str(tpinfo.get("pls_mode", None))
                            if (plsmode == "None") or (isid == "-1") or (isid == "255") or ((isid == "0") and (plscode == "1")) or ((isid == "0") and (plsmode == "Gold")):
                                isid = plscode = plsmode = ""
                            else:
                                isid = ("IS:") + isid
                                plscode = (" ") + plscode.replace("262143","")
                                plsmode = (" ") + plsmode.replace("Unknown","")
                    except:
                        pass
                    self.text = streamtype + streamurl + orbpos + ch + freq + pol + sys + mod + sr + fec + const + isid + plsmode + plscode
                text_width = self.instance.calculateSize().width()
                if (self.instance and (text_width > self.sizeX)):
                    self.x = len(self.text.decode("utf8")) 
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
            self.text = txttmp.encode("utf8","ignore").replace("/n","").replace("/r","")
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
                self.text = self.text[:-3] + "..."
        if self.status is not "end":
            self.moveTimerText.start(150)


