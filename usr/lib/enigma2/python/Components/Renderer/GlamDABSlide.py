# GlamDABSlide renderer (Python 3)
# Created for Glamour skins by MCelliotG with OpenATV DAB slideshow support.

from os import stat
from struct import unpack

from Components.Renderer.Renderer import Renderer
from Components.config import config
from enigma import ePixmap, ePoint, eSize, eTimer, eServiceReference, iServiceInformation


def imageSize(path):
    """Read PNG/JPEG dimensions without external image dependencies."""
    try:
        with open(path, "rb") as image:
            header = image.read(24)
            if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) == 24:
                return unpack(">II", header[16:24])
            if not header.startswith(b"\xff\xd8"):
                return 0, 0
            image.seek(2)
            while True:
                marker = image.read(1)
                if not marker:
                    break
                if marker != b"\xff":
                    continue
                while marker == b"\xff":
                    marker = image.read(1)
                if not marker or marker in (b"\xd9", b"\xda"):
                    break
                if marker in (b"\xd8", b"\x01") or 0xd0 <= marker[0] <= 0xd7:
                    continue
                lengthData = image.read(2)
                if len(lengthData) != 2:
                    break
                length = unpack(">H", lengthData)[0]
                if length < 2:
                    break
                if marker[0] in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7,
                                 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf):
                    frame = image.read(5)
                    if len(frame) == 5:
                        height, width = unpack(">HH", frame[1:])
                        return width, height
                    break
                image.seek(length - 2, 1)
    except (OSError, ValueError):
        pass
    return 0, 0


class GlamDABSlide(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.signature = None
        self.box = None
        self.timer = eTimer()
        self.timer.callback.append(self.updateSlide)

    def applySkin(self, desktop, parent):
        result = Renderer.applySkin(self, desktop, parent)
        if self.instance is not None:
            position = self.instance.position()
            size = self.instance.size()
            self.box = (position.x(), position.y(), size.width(), size.height())
            self.signature = None
            self.updateSlide()
        return result

    def postWidgetCreate(self, instance):
        instance.hide()

    def preWidgetRemove(self, instance):
        self.timer.stop()
        self.signature = None
        self.box = None
        instance.hide()

    def hideSlide(self):
        self.signature = None
        if self.instance is not None:
            self.instance.hide()

    def changed(self, what):
        self.timer.stop()
        if what[0] == self.CHANGED_CLEAR:
            self.hideSlide()
        else:
            self.updateSlide()

    def updateSlide(self):
        self.timer.stop()
        if self.instance is None or self.box is None:
            return
        try:
            field = getattr(iServiceInformation, "sTagPreviewImage", None)
            service = getattr(self.source, "service", None)
            info = service.info() if service is not None else None
            if field is None or info is None:
                self.hideSlide()
                return
            ref = info.getInfoString(iServiceInformation.sServiceref) or ""
            dabType = getattr(eServiceReference, "idServiceDAB", 4115)
            if not ref or eServiceReference(ref).type != dabType:
                self.hideSlide()
                return
            dabConfig = getattr(config, "dab", None)
            slideshow = getattr(dabConfig, "slideshow", None)
            if slideshow is not None and not slideshow.value:
                self.hideSlide()
                return
            path = info.getInfoString(field) or ""
            if not isinstance(path, str) or not path:
                self.hideSlide()
                return
            status = stat(path)
            signature = (ref, path, status.st_mtime_ns, status.st_size)
            if signature != self.signature:
                width, height = imageSize(path)
                if width <= 0 or height <= 0:
                    self.hideSlide()
                    return
                left, top, boxWidth, boxHeight = self.box
                scale = min(float(boxWidth) / width, float(boxHeight) / height)
                targetWidth = max(1, int(width * scale))
                targetHeight = max(1, int(height * scale))
                self.instance.hide()
                self.instance.move(ePoint(left + (boxWidth - targetWidth) // 2,
                                          top + (boxHeight - targetHeight) // 2))
                self.instance.resize(eSize(targetWidth, targetHeight))
                self.instance.setScale(1)
                try:
                    self.instance.setPixmapFromFile(path, True)
                except TypeError:
                    self.instance.setPixmapFromFile(path)
                self.signature = signature
                self.instance.show()
        except (AttributeError, TypeError, ValueError, RuntimeError, OSError):
            self.hideSlide()
        finally:
            # Also detect replacement/removal of an image at the same path.
            if self.instance is not None:
                self.timer.start(1000, True)
