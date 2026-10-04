#  GlamPicon renderer
#  Modded and recoded by MCelliotG for use in Glamour skins or standalone, added Python3 support
#  If you use this Renderer for other skins and rename it, please keep the first and second line adding your credits below

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap
from enigma import eServiceReference, iServiceInformation
from ServiceReference import ServiceReference
import re, unicodedata
import os.path

try:
	import NavigationInstance
except ImportError:
	NavigationInstance = None

class GlamPicon(Renderer):
	searchPaths = ("/media/usb/%s/", "/media/usb2/%s/", "/%s/", "/%sx/", "/usr/share/enigma2/%s/", "/usr/%s/", "/media/hdd/%s/", "/media/usb/XPicons/%s/", "/usr/share/enigma2/XPicons/%s/", "/media/hdd/XPicons/%s/", "/media/ba/%s/", "/media/cf/%s/")
	def __init__(self):
		Renderer.__init__(self)
		self.path = "picon"
		self.nameCache = {}
		self.pngname = ""
		self._pngkey = None

	def applySkin(self, desktop, parent):
		attribs = []
		for attrib, value in self.skinAttributes:
			if attrib == "path":
				self.path = value
			else:
				attribs.append((attrib, value))

		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap

	def changed(self, what):
		if not self.instance:
			return
		if what and what[0] == self.CHANGED_CLEAR:
			self.pngname = ""
			self._pngkey = None
			self.instance.hide()
			return

		text = getattr(self.source, "text", "") or ""
		sname = text.upper()
		pos = sname.rfind(":")
		if pos != -1:
			sname = sname[:pos].rstrip(":").replace(":", "_")
		sname = sname.split("_HTTP")[0]

		# DAB logos are dynamic: do not put them in the static picon cache.
		pngname = self.getDABImage(text)
		if not pngname:
			pngname = self.nameCache.get(sname, "")
			if pngname and not os.path.exists(pngname):
				self.nameCache.pop(sname, None)
				pngname = ""
			if not pngname:
				pngname = self.findPicon(sname) if sname else ""
				if not pngname and sname:
					fields = sname.split("_", 3)
					if len(fields) > 2 and fields[2] != "2":
						fields[2] = "1"
					if fields[0] in ("4097", "5002"):
						fields[0] = "1"
					pngname = self.findPicon("_".join(fields))
				if not pngname and text:
					try:
						name = ServiceReference(text).getServiceName() or ""
						name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("ASCII")
						name = re.sub("[^a-z0-9]", "", name.replace("&", "and").replace("+", "plus").replace("*", "star").lower())
						if name:
							pngname = self.findPicon(name)
							if not pngname and len(name) > 2 and name.endswith("hd"):
								pngname = self.findPicon(name[:-2])
					except (TypeError, ValueError, AttributeError):
						pass
				if pngname:
					self.nameCache[sname] = pngname

		if not pngname:
			self.pngname = ""
			self._pngkey = None
			self.instance.hide()
			return
		try:
			stat = os.stat(pngname)
			pngkey = (pngname, getattr(stat, "st_mtime_ns", stat.st_mtime), stat.st_size, stat.st_ino)
		except OSError:
			self.pngname = ""
			self._pngkey = None
			self.instance.hide()
			return
		if self._pngkey != pngkey:
			self.instance.setScale(1)
			self.instance.setPixmapFromFile(pngname)
			self.pngname = pngname
			self._pngkey = pngkey
		self.instance.show()

	def findPicon(self, serviceName):
		for path in self.searchPaths:
			pngname = path % self.path + serviceName + ".png"
			if os.path.exists(pngname):
				return pngname

		return ""

	def getDABImage(self, serviceName):
		dabType = getattr(eServiceReference, "idServiceDAB", None)
		imageTag = getattr(iServiceInformation, "sTagImage", None)
		navigation = getattr(NavigationInstance, "instance", None)
		if dabType is None or imageTag is None or navigation is None:
			return ""
		try:
			ref = eServiceReference(serviceName or "")
			if ref.type != dabType:
				return ""
			playingRef = navigation.getCurrentlyPlayingServiceReference()
			if not playingRef or playingRef.toString().split(":", 10)[:10] != ref.toString().split(":", 10)[:10]:
				return ""
			service = navigation.getCurrentService()
			info = service and service.info()
			image = info and info.getInfoString(imageTag) or ""
			return image if image and os.path.exists(image) else ""
		except Exception:
			return ""
