#GlamourNextEvents converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

from Components.Converter.Converter import Converter
from Components.Element import cached
from enigma import eEPGCache, eServiceReference
from time import localtime, strftime, mktime, time
from datetime import datetime

class GlamourNextEvents(Converter, object):
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
		
		# Keep the historical type values; PrimeTime is tracked separately
		# because Event11 also has the zero-based index 10.
		self.isPrimeTime = args[0] == "PrimeTime"
		self.type = self.EVENT_TYPES.get(args[0], 0)
		if not self.isPrimeTime and args[0].startswith("Event"):
			number = args[0][5:]
			if number.isascii() and number.isdecimal():
				try:
					index = int(number)
				except ValueError:
					index = 0
				if index > 0:
					self.type = index - 1
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
		
		if not self.isPrimeTime:
			self.epgcache.startTimeQuery(eServiceReference(ref.toString()), curEvent.getBeginTime() + curEvent.getDuration())
			nextEvent = None
			for _ in range(self.type + 1):
				nextEvent = self.epgcache.getNextTimeEntry()
				if not nextEvent:
					break
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
		mode = self.showDuration
		if mode == 12:
			return event.getEventName()
		if mode not in (11, 13, 14, 15, 16, 17, 18):
			return ""

		if mode in (11, 17):
			duration = "%d min" % (event.getDuration() // 60)
			return duration if mode == 17 else f"{event.getEventName()} ({duration})"

		begin_time = event.getBeginTime()
		if mode == 13:
			return strftime("%H:%M", localtime(begin_time))
		duration_seconds = event.getDuration()
		end = strftime("%H:%M", localtime(begin_time + duration_seconds))
		if mode == 14:
			return end
		begin = strftime("%H:%M", localtime(begin_time))
		if mode == 15:
			return f"{begin} - {end}"
		title = event.getEventName()
		if mode == 16:
			return f"{begin} - {end} {title}"
		duration = "%d min" % (duration_seconds // 60)
		return f"{begin} - {end} {title} ({duration})"

	text = property(getText)
