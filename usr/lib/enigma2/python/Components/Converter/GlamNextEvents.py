#GlamNextEvents converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

from Components.Converter.Converter import Converter
from Components.Element import cached
from enigma import eEPGCache, eServiceReference
from time import localtime, strftime, mktime, time
from datetime import datetime

class GlamNextEvents(Converter, object):
	EVENT_TYPES = {f"Event{i}": i - 1 for i in range(1, 11)}  # Event1 to Event10
	EVENT_TYPES.update({"PrimeTime": 10})

	DISPLAY_TYPES = {
		"titleWithDuration": 11, "onlyTitle": 12, "beginTime": 13, "endTime": 14,
		"beginEndTime": 15, "noDuration": 16, "onlyDuration": 17,
		"withDuration": 18, "showDuration": 19
	}

	def __init__(self, type):
		Converter.__init__(self, type)
		self.epgcache = eEPGCache.getInstance()
		args = type.split(',')
		if len(args) != 2:
			raise ValueError("Type must contain exactly 2 arguments")
		
		self.type = self.EVENT_TYPES.get(args[0], 0)  # Default to Event1
		self.showDuration = self.DISPLAY_TYPES.get(args[1], 18)  # Default to withDuration

	@cached
	def getText(self):
		ref = self.source.service
		info = ref and self.source.info
		if info is None:
			return ""

		curEvent = self.source.getCurrentEvent()
		if not curEvent:
			return ""
		
		if self.type < 10:
			self.epgcache.startTimeQuery(eServiceReference(ref.toString()), curEvent.getBeginTime() + curEvent.getDuration())
			nextEvents = [self.epgcache.getNextTimeEntry() for _ in range(self.type + 1)]
			nextEvent = nextEvents[-1] if nextEvents else None
		else:
			now = localtime(time())
			dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, 20, 15)
			primeTime = int(mktime(dt.timetuple()))
			self.epgcache.startTimeQuery(eServiceReference(ref.toString()), primeTime)
			nextEvent = self.epgcache.getNextTimeEntry()
			if nextEvent and nextEvent.getBeginTime() > primeTime:
				nextEvent = None

		return self.formatEvent(nextEvent) if nextEvent else ""

	def formatEvent(self, event):
		begin = strftime("%H:%M", localtime(event.getBeginTime()))
		end = strftime("%H:%M", localtime(event.getBeginTime() + event.getDuration()))
		title = event.getEventName()
		duration = "%d min" % (event.getDuration() // 60)
		
		formats = {
			18: f"{begin} - {end} {title} ({duration})",
			17: duration,
			16: f"{begin} - {end} {title}",
			12: title,
			11: f"{title} ({duration})",
			13: begin,
			14: end,
			15: f"{begin} - {end}"
		}
		return formats.get(self.showDuration, "")

	text = property(getText)
