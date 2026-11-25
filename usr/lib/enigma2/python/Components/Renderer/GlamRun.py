# GlamRun renderer for Enigma2 / OpenATV (Python 3)
# Initial work by vlamo and Dr. Best
# Modded and recoded by MCelliotG for use in Glamour skins or standalone
# Smooth seamless rendering refactor (2026)
# Please preserve the original credits when redistributing this renderer.
#
# RUNNING options: movetype, direction, speed (px/s), startdelay (ms),
# repeat (0=infinite), gap (px), wrap/nowrap, always, ellipsis.
# Frame timing is internal (~60 Hz); step, steptime, fps and smooth are retired.

from time import monotonic

from enigma import (
    eWidget, eLabel, eTimer, ePoint, eSize, gFont,
    RT_WRAP,
)
from Components.Renderer.Renderer import Renderer
from skin import parseColor, parseFont

NONE, RUNNING = 0, 1
LEFT, RIGHT, TOP, BOTTOM = 0, 1, 2, 3


class GlamRun(Renderer):
    GUI_WIDGET = eWidget
    FRAME_MS = 17                     # approx. 60 Hz; no XML fps setting
    MAX_DELTA = 0.12                 # avoid a huge jump after a GUI stall
    DEFAULT_HORIZONTAL_SPEED = 80.0  # px/s
    DEFAULT_VERTICAL_SPEED = 40.0    # px/s
    DEFAULT_GAP = 300                # px; capped to half of viewport

    def __init__(self):
        Renderer.__init__(self)
        self.type = NONE
        self.direction = LEFT
        self.txfont = gFont('Regular', 14)
        self.txtflags = 0
        self.halign = eLabel.alignLeft
        self.soffset = (0, 0)
        self.W = self.H = 0
        self.mShown = 0

        self.speed = None
        self.startdelay = 0
        self.repeat = 0
        self.gap = self.DEFAULT_GAP
        self.always = False
        self.ellipsis = False

        self.txtext = ''
        self._source_text = None
        self.scroll_label = None
        self.seamlessLabel = None
        self.mTimer = None
        self.lineHeight = 0
        self._active = False
        self._phase = 0.0
        self._period = 0
        self._last_time = None
        self._last_pixel = None
        self._cycles_left = 0

    def postWidgetCreate(self, instance):
        for name, value in (self.skinAttributes or []):
            if name == 'size':
                self.W, self.H = map(int, value.split(','))
        instance.move(ePoint(0, 0))
        instance.resize(eSize(self.W, self.H))
        self.scroll_label = eLabel(instance)
        self.seamlessLabel = eLabel(instance)
        self.seamlessLabel.hide()
        self.mTimer = eTimer()
        self.mTimer.callback.append(self.movingLoop)

    def preWidgetRemove(self, instance):
        self._stop()
        if self.mTimer is not None:
            try:
                self.mTimer.callback.remove(self.movingLoop)
            except ValueError:
                pass
        self.mTimer = None
        self.scroll_label = None
        self.seamlessLabel = None

    @staticmethod
    def _nonnegative(value, default):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _boolean(value, implicit=True):
        if value == '':
            return implicit
        return str(value).lower() not in ('0', 'false', 'no', 'off')

    def _wrap_option(self, key, value):
        if (key.lower() == 'wrap' and value == '0') or (key.lower() == 'nowrap' and value != '0'):
            self.txtflags &= ~RT_WRAP
        else:
            self.txtflags |= RT_WRAP

    def _read_options(self, options):
        for raw in options.split(','):
            raw = raw.strip()
            if not raw:
                continue
            key, separator, value = raw.partition('=')
            key, value = key.strip(), value.strip() if separator else ''
            if key in ('wrap', 'nowrap'):
                self._wrap_option(key, value)
            elif key == 'movetype' and value in ('none', 'running'):
                self.type = {'none': NONE, 'running': RUNNING}[value]
            elif key == 'direction' and value in ('left', 'right', 'top', 'bottom'):
                self.direction = {'left': LEFT, 'right': RIGHT, 'top': TOP, 'bottom': BOTTOM}[value]
            elif key == 'speed':
                try:
                    speed = float(value)
                    if 1 <= speed <= 1000 and speed == speed:  # exclude NaN
                        self.speed = speed
                except ValueError:
                    pass
            elif key == 'startdelay':
                self.startdelay = self._nonnegative(value, self.startdelay)
            elif key == 'repeat':
                self.repeat = self._nonnegative(value, self.repeat)
            elif key == 'gap':
                self.gap = self._nonnegative(value, self.gap)
            elif key == 'always':
                self.always = self._boolean(value)
            elif key == 'ellipsis':
                self.ellipsis = self._boolean(value)

    def applySkin(self, desktop, screen):
        valign = eLabel.alignTop
        haligns = {
            'left': eLabel.alignLeft, 'center': eLabel.alignCenter,
            'right': eLabel.alignRight, 'block': eLabel.alignBlock,
        }
        valigns = {
            'top': eLabel.alignTop, 'center': eLabel.alignCenter,
            'bottom': eLabel.alignBottom,
        }
        inherited = []
        for name, value in (self.skinAttributes or []):
            if name == 'font':
                self.txfont = parseFont(value, ((1, 1), (1, 1)))
            elif name == 'foregroundColor':
                color = parseColor(value)
                self.scroll_label.setForegroundColor(color)
                self.seamlessLabel.setForegroundColor(color)
            elif name in ('shadowColor', 'borderColor'):
                color = parseColor(value)
                self.scroll_label.setShadowColor(color)
                self.seamlessLabel.setShadowColor(color)
            elif name == 'shadowOffset':
                self.soffset = tuple(map(int, value.split(',')))
                offset = ePoint(self.soffset)
                self.scroll_label.setShadowOffset(offset)
                self.seamlessLabel.setShadowOffset(offset)
            elif name == 'borderWidth':
                border = int(value)
                self.soffset = (-border, -border)
            elif name == 'halign' and value in haligns:
                self.halign = haligns[value]
            elif name == 'valign' and value in valigns:
                valign = valigns[value]
            elif name == 'noWrap':
                self._wrap_option(name, value)
            elif name == 'options':
                self._read_options(value)
            else:
                inherited.append((name, value))
                if name == 'backgroundColor':
                    color = parseColor(value)
                    self.scroll_label.setBackgroundColor(color)
                    self.seamlessLabel.setBackgroundColor(color)
                elif name == 'transparent':
                    transparent = int(value)
                    self.scroll_label.setTransparent(transparent)
                    self.seamlessLabel.setTransparent(transparent)

        self.skinAttributes = inherited
        result = Renderer.applySkin(self, desktop, screen)
        for label in (self.scroll_label, self.seamlessLabel):
            label.setFont(self.txfont)
            label.setNoWrap(0 if self.txtflags & RT_WRAP else 1)
            label.setHAlign(self.halign)
            label.setVAlign(valign)
        self.scroll_label.move(ePoint(0, 0))
        self.scroll_label.resize(eSize(self.W, self.H))
        if self.direction in (TOP, BOTTOM):
            from enigma import fontRenderClass
            font = fontRenderClass.getInstance()
            line_height = int(font.getLineHeight(self.txfont) or
                              self.txfont.pointSize / 6 + self.txfont.pointSize)
            self.scroll_label.setText('WQq')
            if line_height > self.scroll_label.calculateSize().height():
                self.lineHeight = line_height
            self.scroll_label.setText('')
        return result

    def doSuspend(self, suspended):
        self.mShown = 0 if suspended else 1
        self.changed((self.CHANGED_CLEAR if suspended else self.CHANGED_DEFAULT,))

    def connect(self, source):
        Renderer.connect(self, source)

    def _stop(self):
        if self.mTimer is not None:
            self.mTimer.stop()
        self._active = False
        self._last_time = None
        self._last_pixel = None
        if self.seamlessLabel is not None:
            self.seamlessLabel.hide()

    def changed(self, what):
        if what[0] == self.CHANGED_CLEAR:
            self._stop()
            self._source_text = None
            self.txtext = ''
            if self.scroll_label is not None:
                self.scroll_label.setText('')
            return
        if not self.mShown or self.instance is None or self.scroll_label is None:
            return
        value = self.source.text or ''
        if not isinstance(value, str):
            value = str(value)
        if value == self._source_text:
            return  # do not restart running text on unrelated source updates
        self._source_text = value
        self._stop()
        self.txtext = value
        self._layout()

    def _move(self, label, x, y):
        label.move(ePoint(int(x) - self.soffset[0], int(y) - self.soffset[1]))

    def _layout(self):
        self.scroll_label.resize(eSize(self.W, self.H))
        text = self.txtext
        if not (self.txtflags & RT_WRAP):
            text = text.replace('\n', ' ').replace('\r', ' ')
        self.txtext = text
        self.scroll_label.setText(text)
        self._move(self.scroll_label, 0, 0)
        if not text or self.type != RUNNING:
            return

        horizontal = self.direction in (LEFT, RIGHT)
        if horizontal or not (self.txtflags & RT_WRAP):
            # Use a generously sized temporary label for accurate text width.
            self.scroll_label.resize(eSize(max(self.W, self.txfont.pointSize * len(text)), self.H))
        dimensions = self.scroll_label.calculateSize()
        text_width = max(1, int(dimensions.width()))
        text_height = max(1, int(dimensions.height()))
        if self.lineHeight and not horizontal:
            text_height = ((text_height + self.lineHeight - 1) //
                           self.lineHeight) * self.lineHeight

        viewport = self.W if horizontal else self.H
        extent = text_width if horizontal else text_height
        if not self.always and extent <= viewport:
            self.scroll_label.resize(eSize(self.W, self.H))
            return

        width = max(self.W, text_width) if horizontal or not (self.txtflags & RT_WRAP) else self.W
        height = max(self.H, text_height) if horizontal else text_height
        size = eSize(max(1, width), max(1, height))
        self.scroll_label.resize(size)
        self.seamlessLabel.resize(size)
        self.seamlessLabel.setText(text)

        # Keep some part of a copy visible while the next copy approaches.
        # A gap smaller than the viewport prevents the entire widget going blank.
        effective_gap = min(self.gap, max(0, viewport // 2))
        self._period = extent + effective_gap
        self._phase = 0.0
        self._last_pixel = None
        self._cycles_left = self.repeat
        self._active = True
        self.seamlessLabel.show()
        self._paint()
        self.mTimer.start(self.startdelay, True)

    def _paint(self):
        pixel = int(round(self._phase))
        if pixel == self._last_pixel:
            return
        if self.direction in (LEFT, TOP):
            first, second = -pixel, self._period - pixel
        else:
            first, second = pixel, pixel - self._period
        if self.direction in (LEFT, RIGHT):
            self._move(self.scroll_label, first, 0)
            self._move(self.seamlessLabel, second, 0)
        else:
            self._move(self.scroll_label, 0, first)
            self._move(self.seamlessLabel, 0, second)
        self._last_pixel = pixel

    def movingLoop(self):
        if not self._active or self.mTimer is None:
            return
        now = monotonic()
        if self._last_time is None:
            self._last_time = now
        else:
            dt = min(self.MAX_DELTA, max(0.0, now - self._last_time))
            self._last_time = now
            speed = self.speed if self.speed is not None else (
                self.DEFAULT_HORIZONTAL_SPEED if self.direction in (LEFT, RIGHT)
                else self.DEFAULT_VERTICAL_SPEED)
            self._phase += speed * dt
            if self._phase >= self._period:
                completed = int(self._phase // self._period)
                if self.repeat:
                    self._cycles_left -= completed
                    if self._cycles_left <= 0:
                        self._finish()
                        return
                self._phase %= self._period
            self._paint()
        self.mTimer.start(self.FRAME_MS, True)

    def _finish(self):
        self._stop()
        self._move(self.scroll_label, 0, 0)
        self._add_ellipsis()

    def _add_ellipsis(self):
        if not self.ellipsis or not self.txtext:
            return
        if self.direction not in (LEFT, RIGHT):
            return  # Preserve wrapped descriptions exactly as authored.
        # Determine a fitting prefix by measuring actual font glyphs, once only.
        original = self.txtext
        if self.scroll_label.calculateSize().width() <= self.W:
            return
        lo, hi = 0, len(original)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            self.scroll_label.setText(original[:mid].rstrip() + '...')
            if self.scroll_label.calculateSize().width() <= self.W:
                lo = mid
            else:
                hi = mid - 1
        self.scroll_label.setText(original[:lo].rstrip() + '...')
        self.scroll_label.resize(eSize(self.W, self.H))
