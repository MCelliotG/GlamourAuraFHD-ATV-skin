# GlamBaseIcons - common base renderer for SVG/PNG icons
# Used by GlamNetIcon, GlamAudioIcon, and any future Glam-* icon renderers
# Coded by MCelliotG for use in Glamour skins or standalone
# If you use this Renderer for other skins and rename it, please keep the lines above adding your credits below

from os.path import exists, join
from enigma import ePixmap
from Components.Renderer.Renderer import Renderer
from Tools.Directories import SCOPE_GUISKIN, resolveFilename


class GlamBaseIcons(Renderer):
	searchPaths = (
		resolveFilename(SCOPE_GUISKIN),
		"/usr/share/enigma2/skin_default/"
	)

	GUI_WIDGET = ePixmap

	def __init__(self):
		Renderer.__init__(self)
		self.size = None
		self.cache = {}		# name -> full path (svg or png)
		self.currentIcon = ""  # last shown icon path
		self.path = ""
		print("[GlamBaseIcons] Base icon renderer initialized")

	def applySkin(self, desktop, parent):
		attribs = []
		for (attrib, value) in self.skinAttributes:
			if attrib == "path":
				self.path = join(value, "")
				print(f"[GlamBaseIcons] applySkin: path='{self.path}'")
			elif attrib == "size":
				parts = value.split(",")
				if len(parts) == 2:
					self.size = (int(parts[0]), int(parts[1]))
					print(f"[GlamBaseIcons] applySkin: size={self.size}")
				attribs.append((attrib, value))
			else:
				attribs.append((attrib, value))

		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	def _tryIcon(self, base, name, ext):
		full = f"{base}{self.path}{name}.{ext}"
		print(f"[GlamBaseIcons] Trying {ext.upper()}: {full}")
		return full if exists(full) else ""

	def findIcon(self, name):
		if not name:
			print("[GlamBaseIcons] findIcon: empty name")
			return ""

		lname = name.lower()
		if lname == "unknown":
			print(f"[GlamBaseIcons] Ignoring unknown '{name}'")
			return ""

		print(f"[GlamBaseIcons] findIcon: searching for '{name}'")

		# 1) Absolute paths
		if self.path.startswith("/"):
			svg = f"{self.path}{name}.svg"
			print(f"[GlamBaseIcons] Absolute SVG: {svg}")
			if exists(svg):
				print("[GlamBaseIcons] Found absolute SVG")
				return svg

			png = f"{self.path}{name}.png"
			print(f"[GlamBaseIcons] Absolute PNG: {png}")
			if exists(png):
				print("[GlamBaseIcons] Found absolute PNG")
				return png

		# 2) Search in active skin + skin_default
		for base in self.searchPaths:
			svg = self._tryIcon(base, name, "svg")
			if svg:
				print("[GlamBaseIcons] Found SVG in searchPaths")
				return svg

			png = self._tryIcon(base, name, "png")
			if png:
				print("[GlamBaseIcons] Found PNG in searchPaths")
				return png

		print("[GlamBaseIcons] Icon not found:", name)
		return ""

	def _loadPixmap(self, path):
		try:
			print(f"[GlamBaseIcons] Loading icon: {path}")
			self.instance.setPixmapFromFile(path)
		except Exception as e:
			print("[GlamBaseIcons] ERROR loading icon:", e)

	def changed(self, what):
		if not self.instance:
			print("[GlamBaseIcons] changed(): instance is None")
			return

		if what[0] == self.CHANGED_CLEAR:
			print("[GlamBaseIcons] CHANGED_CLEAR -> hide")
			self.instance.hide()
			return

		value = (self.source.text or "").strip()
		print(f"[GlamBaseIcons] changed(): source text='{value}'")

		if not value:
			print("[GlamBaseIcons] Empty value -> hide")
			self.instance.hide()
			return

		iconPath = self.cache.get(value, "")
		if not iconPath:
			iconPath = self.findIcon(value)
			if iconPath:
				self.cache[value] = iconPath

		if not iconPath:
			print("[GlamBaseIcons] Icon not found -> hide")
			self.instance.hide()
			return

		if iconPath != self.currentIcon:
			self._loadPixmap(iconPath)
			self.currentIcon = iconPath

		self.instance.show()
