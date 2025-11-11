# GlamNetIcon Universal network icon renderer for Enigma2
# Fully recoded by MCelliotG for use in Glamour skins or standalone
# Uses the same path resolving mechanism as GlamAudioIcon with full debug logging
# If you use this Renderer for other skins and rename it, please keep the first and second line adding your credits below

from os.path import exists, join
from enigma import ePixmap
from Components.Renderer.Renderer import Renderer
from Tools.Directories import SCOPE_GUISKIN, resolveFilename

class GlamNetIcon(Renderer):
	searchPaths = (
		resolveFilename(SCOPE_GUISKIN),
		"/usr/share/enigma2/skin_default/"
	)

	def __init__(self):
		Renderer.__init__(self)
		self.size = None
		self.cache = {}
		self.pngname = ""
		self.path = ""
		print("[GlamNetIcon] Renderer initialized.")

	def applySkin(self, desktop, parent):
		attribs = []
		for (attrib, value) in self.skinAttributes:
			if attrib == "path":
				self.path = join(value, "")  # ensure trailing slash if relative
				print(f"[GlamNetIcon] applySkin: path='{self.path}'")
			else:
				attribs.append((attrib, value))

			if attrib == "size":
				s = value.split(",")
				if len(s) == 2:
					self.size = f"{s[0]}x{s[1]}"
					print(f"[GlamNetIcon] applySkin: size='{self.size}'")

		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap

	def _findIcon(self, name):
		if not name:
			print("[GlamNetIcon] _findIcon: empty name")
			return ""

		print(f"[GlamNetIcon] _findIcon: searching for '{name}'")

		pngname = ""

		# 1) Absolute path
		if self.path.startswith("/"):
			pngname = f"{self.path}{name}.png"
			print(f"[GlamNetIcon] Trying absolute path: {pngname}")
			if exists(pngname):
				print("[GlamNetIcon] Found absolute path")
				return pngname

		# 2) In active skin folder (resolved by SCOPE_GUISKIN)
		for base in self.searchPaths:
			full = f"{base}{self.path}{name}.png"
			print(f"[GlamNetIcon] Trying skin path: {full}")

			if exists(full):
				print("[GlamNetIcon] Found in skin")
				return full

		print("[GlamNetIcon] Not found")
		return ""

	def changed(self, what):
		if not self.instance:
			print("[GlamNetIcon] changed(): instance is None")
			return

		value = (self.source.text or "").strip()
		print(f"[GlamNetIcon] changed(): converter returned '{value}'")

		if not value:
			print("[GlamNetIcon] Empty value -> hide")
			self.instance.hide()
			return

		pngname = self.cache.get(value, "")
		if not pngname:
			pngname = self._findIcon(value)
			if pngname:
				self.cache[value] = pngname

		if not pngname:
			print("[GlamNetIcon] Icon not found -> hide")
			self.instance.hide()
			return

		# If icon changed, load new pixmap
		if self.pngname != pngname:
			print(f"[GlamNetIcon] Showing icon: {pngname}")
			self.instance.setPixmapFromFile(pngname)
			self.pngname = pngname

		self.instance.show()
