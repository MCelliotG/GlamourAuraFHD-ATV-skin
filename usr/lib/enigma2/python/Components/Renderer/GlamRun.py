#	GlamRun renderer (Python 3)
#	Initial work by vlamo and Dr. Best
# Modded and recoded by MCelliotG for use in Glamour skins or standalone
# If you use this Renderer for other skins and rename it, please keep the first and second line adding your credits below

from enigma import eWidget, eLabel, eTimer, ePoint, eSize, gFont, \
	RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_HALIGN_RIGHT, RT_HALIGN_BLOCK, \
	RT_VALIGN_TOP, RT_VALIGN_CENTER, RT_VALIGN_BOTTOM, RT_WRAP

from Components.Renderer.Renderer import Renderer
from skin import parseColor, parseFont

# Constants for scroll type and direction
NONE = 0
RUNNING = 1
SWIMMING = 2
AUTO = 3

LEFT = 0
RIGHT = 1
TOP = 2
BOTTOM = 3

class GlamRun(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.type = NONE
		self.txfont = gFont("Regular", 14)
		self.soffset = (0, 0)
		self.txtflags = 0
		self.txtext = ""
		self.scroll_label = self.mTimer = self.mStartPoint = None
		self.X = self.Y = self.W = self.H = self.mStartDelay = 0
		self.mAlways = 1
		self.mStep = 1
		self.mStepTimeout = 50
		self.direction = LEFT
		self.mLoopTimeout = self.mOneShot = 0
		self.mRepeat = 0
		self.mPageDelay = self.mPageLength = 0
		self.lineHeight = 0
		self.mShown = 0
		self.ellipsis = False  # New attribute for ellipsis

	GUI_WIDGET = eWidget

	def postWidgetCreate(self, instance):
		for attrib, value in self.skinAttributes:
			if attrib == "size":
				self.W, self.H = map(int, value.split(','))
		self.instance.move(ePoint(0, 0))
		self.instance.resize(eSize(self.W, self.H))
		self.scroll_label = eLabel(instance)
		self.mTimer = eTimer()
		self.mTimer.callback.append(self.movingLoop)

	def preWidgetRemove(self, instance):
		self.mTimer.stop()
		self.mTimer.callback.remove(self.movingLoop)
		self.mTimer = None
		self.scroll_label = None

	def applySkin(self, desktop, screen):
		def retValue(val, limit, default, min_flag=False):
			try:
				x = int(val)
				return min(limit, x) if min_flag else max(limit, x)
			except:
				return default

		def setWrapFlag(attrib, value):
			if (attrib.lower() == "wrap" and value == "0") or (attrib.lower() == "nowrap" and value != "0"):
				self.txtflags &= ~RT_WRAP
			else:
				self.txtflags |= RT_WRAP

		self.halign = valign = eLabel.alignLeft
		if self.skinAttributes:
			attribs = []
			for attrib, value in self.skinAttributes:
				match attrib:
					case "font":
						self.txfont = parseFont(value, ((1, 1), (1, 1)))
					case "foregroundColor":
						self.scroll_label.setForegroundColor(parseColor(value))
					case "shadowColor" | "borderColor":
						self.scroll_label.setShadowColor(parseColor(value))
					case "shadowOffset":
						self.soffset = tuple(map(int, value.split(',')))
						self.scroll_label.setShadowOffset(ePoint(self.soffset))
					case "borderWidth":
						self.soffset = (-int(value), -int(value))
					case "valign" if value in ("top", "center", "bottom"):
						valign = {"top": eLabel.alignTop, "center": eLabel.alignCenter, "bottom": eLabel.alignBottom}[value]
						self.txtflags |= {"top": RT_VALIGN_TOP, "center": RT_VALIGN_CENTER, "bottom": RT_VALIGN_BOTTOM}[value]
					case "halign" if value in ("left", "center", "right", "block"):
						self.halign = {"left": eLabel.alignLeft, "center": eLabel.alignCenter, "right": eLabel.alignRight, "block": eLabel.alignBlock}[value]
						self.txtflags |= {"left": RT_HALIGN_LEFT, "center": RT_HALIGN_CENTER, "right": RT_HALIGN_RIGHT, "block": RT_HALIGN_BLOCK}[value]
					case "noWrap":
						setWrapFlag(attrib, value)
					case "options":
						for opt, val in (o.split('=', 1) if '=' in o else (o.strip(), "") for o in value.split(',')):
							if not opt:
								continue
							match opt:
								case "wrap" | "nowrap":
									setWrapFlag(opt, val)
								case "movetype" if val in ("none", "running", "swimming"):
									self.type = {"none": NONE, "running": RUNNING, "swimming": SWIMMING}[val]
								case "direction" if val in ("left", "right", "top", "bottom"):
									self.direction = {"left": LEFT, "right": RIGHT, "top": TOP, "bottom": BOTTOM}[val]
								case "step" if val:
									self.mStep = retValue(val, 1, self.mStep)
								case "steptime" if val:
									self.mStepTimeout = retValue(val, 25, self.mStepTimeout)
								case "startdelay" if val:
									self.mStartDelay = retValue(val, 0, self.mStartDelay)
								case "pause" if val:
									self.mLoopTimeout = retValue(val, 0, self.mLoopTimeout)
								case "oneshot" if val:
									self.mOneShot = retValue(val, 0, self.mOneShot)
								case "repeat" if val:
									self.mRepeat = retValue(val, 0, self.mRepeat)
								case "always" if val:
									self.mAlways = retValue(val, 0, self.mAlways)
								case "startpoint" if val:
									self.mStartPoint = int(val)
								case "pagedelay" if val:
									self.mPageDelay = retValue(val, 0, self.mPageDelay)
								case "pagelength" if val:
									self.mPageLength = retValue(val, 0, self.mPageLength)
								case "ellipsis" if val:
									self.ellipsis = int(val)
									print(f"[GlamRun] Ellipsis enabled: {self.ellipsis}")
					case _:
						attribs.append((attrib, value))
						match attrib:
							case "backgroundColor":
								self.scroll_label.setBackgroundColor(parseColor(value))
							case "transparent":
								self.scroll_label.setTransparent(int(value))
			self.skinAttributes = attribs

		ret = Renderer.applySkin(self, desktop, screen)

		if self.mOneShot:
			self.mOneShot = max(self.mStepTimeout, self.mOneShot)
		if self.mLoopTimeout:
			self.mLoopTimeout = max(self.mStepTimeout, self.mLoopTimeout)
		if self.mPageDelay:
			self.mPageDelay = max(self.mStepTimeout, self.mPageDelay)

		self.scroll_label.setFont(self.txfont)
		if not (self.txtflags & RT_WRAP):
			self.scroll_label.setNoWrap(1)
		self.scroll_label.setVAlign(valign)
		self.scroll_label.setHAlign(self.halign)
		self.scroll_label.move(ePoint(0, 0))
		self.scroll_label.resize(eSize(self.W, self.H))

		if self.direction in (TOP, BOTTOM):
			from enigma import fontRenderClass
			flh = int(fontRenderClass.getInstance().getLineHeight(self.txfont) or self.txfont.pointSize / 6 + self.txfont.pointSize)
			self.scroll_label.setText("WQq")
			if flh > self.scroll_label.calculateSize().height():
				self.lineHeight = flh
			self.scroll_label.setText("")
		return ret

	def doSuspend(self, suspended):
		self.mShown = 1 - suspended
		if suspended:
			self.changed((self.CHANGED_CLEAR,))
		else:
			self.changed((self.CHANGED_DEFAULT,))

	def connect(self, source):
		Renderer.connect(self, source)

	def changed(self, what):
		if self.mTimer is not None:
			self.mTimer.stop()
		if what[0] == self.CHANGED_CLEAR:
			self.txtext = ""
			if self.instance:
				self.scroll_label.setText("")
		else:
			if self.mShown:
				self.txtext = self.source.text or ""
				if self.instance and not self.calcMoving():
					self.scroll_label.resize(eSize(self.W, self.H))
					self.moveLabel(self.X, self.Y)

	def moveLabel(self, X, Y):
		self.scroll_label.move(ePoint(X - self.soffset[0], Y - self.soffset[1]))

	def applyEllipsis(self):
		if not self.ellipsis:
			return

		text_size = self.scroll_label.calculateSize()
		text_width = text_size.width()
		text_height = text_size.height()

		if self.direction in (LEFT, RIGHT):
			if text_width <= self.W:
				return

			# Calculate the visible text based on the widget width
			visible_chars = int((self.W / text_width) * len(self.txtext))
			visible_text = self.txtext[:visible_chars]

			# Find the last space in the visible text
			last_space_index = visible_text.rfind(' ')
			if last_space_index != -1:
				visible_text = visible_text[:last_space_index] + "..."
			else:
				visible_text = visible_text + "..."

			self.scroll_label.setText(visible_text)
			self.scroll_label.resize(eSize(self.W, self.H))

		elif self.direction in (TOP, BOTTOM):
			if text_height <= self.H:
				return

			# Calculate the visible lines based on the widget height
			line_height = self.lineHeight if self.lineHeight else self.txfont.pointSize
			visible_lines = int(self.H / line_height)
			lines = self.txtext.split('\n')
			visible_text = '\n'.join(lines[:visible_lines])

			# Add ellipsis to the last visible line
			if len(lines) > visible_lines:
				last_line = lines[visible_lines - 1]
				if len(last_line) > 0:
					visible_text = visible_text[:-len(last_line)] + last_line[:10] + "..."  # Adjust as needed

			self.scroll_label.setText(visible_text)
			self.scroll_label.resize(eSize(self.W, self.H))

	def calcMoving(self):
		self.X = self.Y = 0
		if not (self.txtflags & RT_WRAP):
			self.txtext = self.txtext.replace("\n", " ").replace("\r", " ")

		self.scroll_label.setText(self.txtext)

		if self.txtext == "" or self.type == NONE or self.scroll_label is None:
			return False

		if self.direction in (LEFT, RIGHT) or not (self.txtflags & RT_WRAP):
			self.scroll_label.resize(eSize(self.txfont.pointSize * len(self.txtext), self.H))

		text_size = self.scroll_label.calculateSize()
		text_width = text_size.width()
		text_height = text_size.height()

		if self.direction in (LEFT, RIGHT) or not (self.txtflags & RT_WRAP):
			text_width += 10

		self.mStop = None
		if self.lineHeight and self.direction in (TOP, BOTTOM):
			text_height = max(text_height, (text_height + self.lineHeight - 1) // self.lineHeight * self.lineHeight)

		if self.direction in (LEFT, RIGHT):
			if not self.mAlways and text_width <= self.W:
				return False
			if self.type == RUNNING:
				self.A = self.X - text_width - self.soffset[0] - abs(self.mStep)
				self.B = self.W - self.soffset[0] + abs(self.mStep)
				if self.direction == LEFT:
					self.mStep = -abs(self.mStep)
					self.mStop = self.X
					self.P = self.B
				else:
					self.mStep = abs(self.mStep)
					self.mStop = self.B - text_width + self.soffset[0] - self.mStep
					self.P = self.A
				if self.mStartPoint is not None:
					if self.direction == LEFT:
						self.mStop = self.P = max(self.A, min(self.W, self.mStartPoint))
					else:
						self.mStop = self.P = max(self.A, min(self.B, self.mStartPoint - text_width + self.soffset[0]))
			elif self.type == SWIMMING:
				if text_width < self.W:
					self.A = self.X + 1
					self.B = self.W - text_width - 1
					if self.halign == LEFT:
						self.P = self.A
						self.mStep = abs(self.mStep)
					elif self.halign == RIGHT:
						self.P = self.B
						self.mStep = -abs(self.mStep)
					else:
						self.P = self.B // 2
						self.mStep = abs(self.mStep) if self.direction == RIGHT else -abs(self.mStep)
				else:
					if text_width == self.W:
						text_width += max(2, text_width // 20)
					self.A = self.W - text_width
					self.B = self.X
					if self.halign == LEFT:
						self.P = self.B
						self.mStep = -abs(self.mStep)
					elif self.halign == RIGHT:
						self.P = self.A
						self.mStep = abs(self.mStep)
					else:
						self.P = self.A // 2
						self.mStep = abs(self.mStep) if self.direction == RIGHT else -abs(self.mStep)
			else:
				return False
		elif self.direction in (TOP, BOTTOM):
			if not self.mAlways and text_height <= self.H:
				return False
			if self.type == RUNNING:
				self.A = self.Y - text_height - self.soffset[1] - abs(self.mStep)
				self.B = self.H - self.soffset[1] + abs(self.mStep)
				if self.direction == TOP:
					self.mStep = -abs(self.mStep)
					self.mStop = self.Y
					self.P = self.B
				else:
					self.mStep = abs(self.mStep)
					self.mStop = self.B - text_height + self.soffset[1] - self.mStep
					self.P = self.A
				if self.mStartPoint is not None:
					if self.direction == TOP:
						self.mStop = self.P = max(self.A, min(self.H, self.mStartPoint))
					else:
						self.mStop = self.P = max(self.A, min(self.B, self.mStartPoint - text_height + self.soffset[1]))
			elif self.type == SWIMMING:
				if text_height < self.H:
					self.A = self.Y
					self.B = self.H - text_height
					if self.direction == TOP:
						self.P = self.B
						self.mStep = -abs(self.mStep)
					else:
						self.P = self.A
						self.mStep = abs(self.mStep)
				else:
					if text_height == self.H:
						text_height += max(2, text_height // 40)
					self.A = self.H - text_height
					self.B = self.Y
					if self.direction == TOP:
						self.P = self.B
						self.mStep = -abs(self.mStep)
						self.mStop = self.B
					else:
						self.P = self.A
						self.mStep = abs(self.mStep)
						self.mStop = self.A
			else:
				return False
		else:
			return False

		self.xW = max(self.W, text_width)
		self.xH = max(self.H, text_height)

		self.scroll_label.resize(eSize(self.xW, self.xH))

		if self.mStartDelay:
			if self.direction in (LEFT, RIGHT):
				self.moveLabel(self.P, self.Y)
			else:
				self.moveLabel(self.X, self.P)

		self.mCount = self.mRepeat
		self.mTimer.start(self.mStartDelay, True)
		print(f"[GlamRun] Timer started with delay: {self.mStartDelay}")
		return True

	def movingLoop(self):
		if self.A <= self.P <= self.B:
			if self.direction in (LEFT, RIGHT):
				self.moveLabel(self.P, self.Y)
			else:
				self.moveLabel(self.X, self.P)

			timeout = self.mStepTimeout
			if self.mStop is not None and self.mStop + abs(self.mStep) > self.P >= self.mStop:
				if self.type == RUNNING and self.mOneShot > 0:
					if self.mRepeat > 0 and self.mCount - 1 <= 0:
						self.applyEllipsis()  # Apply ellipsis when repeat count reaches 0
						return
					timeout = self.mOneShot
				elif self.type == SWIMMING and self.mPageLength > 0 and self.mPageDelay > 0:
					if self.direction == TOP and self.mStep < 0:
						self.mStop -= self.mPageLength
						if self.mStop < self.A:
							self.mStop = self.B
						timeout = self.mPageDelay
					elif self.direction == BOTTOM and self.mStep > 0:
						self.mStop += self.mPageLength
						if self.mStop > self.B:
							self.mStop = self.A
						timeout = self.mPageDelay
		else:
			if self.mRepeat > 0:
				print(f"[GlamRun] movingLoop: Repeat count: {self.mCount}")
				self.mCount -= 1
				if self.mCount == 0:
					print("[GlamRun] movingLoop: Repeat count reached 0, applying ellipsis.")
					self.applyEllipsis()  # Apply ellipsis when repeat count reaches 0
					return

				timeout = self.mLoopTimeout
				if self.type == RUNNING:
					if self.P < self.A:
						self.P = self.B + abs(self.mStep)
					else:
						self.P = self.A - abs(self.mStep)
				else:
					self.mStep = -self.mStep

		self.P += self.mStep
		self.mTimer.start(timeout, True)