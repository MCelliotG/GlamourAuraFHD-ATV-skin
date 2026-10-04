# GlamourCPU converter (Python 3)
# Modded and recoded by MCelliotG for use in Glamour skins or standalone
# If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

import re

from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached

class GlamourCPU(Converter, object):
	CPU_ALL = -2
	CPU_TOTAL = -1
	PLACEHOLDER = re.compile(r"\$(\d+|\?)")

	def __init__(self, type):
		Converter.__init__(self, type)
		self.percentlist = []
		self.format_type = "Default"
		self.sfmt = type.strip()
		
		if "," in type:
			parts = type.split(",")
			self.sfmt = parts[0].strip()
			self.format_type = parts[1].strip()
		
	def doSuspend(self, suspended):
		if suspended:
			cpuUsageMonitor.disconnectCallback(self.gotPercentage)
		else:
			cpuUsageMonitor.connectCallback(self.gotPercentage)

	def destroy(self):
		cpuUsageMonitor.disconnectCallback(self.gotPercentage)
		Converter.destroy(self)

	def gotPercentage(self, list):
		self.percentlist = list
		self.changed((self.CHANGED_POLL,))

	@cached
	def getText(self):
		if not self.percentlist:
			return ""
		
		if self.sfmt in ("All", "Default"):
			if self.format_type == "Separator":
				return f"CPU: {self.percentlist[0]}% (" + " | ".join(f"{p}%" for p in self.percentlist[1:]) + ")"
			elif self.format_type == "Newline":
				return f"Total: {self.percentlist[0]}%\n" + "\n".join(f"C{i}: {p}%" for i, p in enumerate(self.percentlist[1:], 1))
			elif self.format_type == "Full":
				return f"Total: {self.percentlist[0]}% " + " ".join(f"Core{i}: {p}%" for i, p in enumerate(self.percentlist[1:], 1))
			else:
				core_loads = " ".join(f"{p}%" for p in self.percentlist[1:])
				return f"CPU: {self.percentlist[0]}% ({core_loads})" if core_loads else f"CPU: {self.percentlist[0]}%"
		
		def replace(match):
			key = match.group(1)
			if key == "?":
				return str(len(self.percentlist) - 1)
			try:
				index = int(key)
			except ValueError:
				return ""
			return f"{self.percentlist[index]}%" if index < len(self.percentlist) else ""
		return self.PLACEHOLDER.sub(replace, self.sfmt).strip()

	@cached
	def getValue(self):
		try:
			return self.percentlist[0] if self.sfmt in ("All", "Default") else self.percentlist[int(self.sfmt)]
		except (IndexError, ValueError):
			return 0

	text = property(getText)
	value = property(getValue)
	range = 100

class CpuUsageMonitor(Poll, object):
	def __init__(self):
		Poll.__init__(self)
		self.__callbacks = []
		self.__curr_info = self.getCpusInfo()
		self.poll_interval = 500

	def getCpusCount(self):
		return len(self.__curr_info) - 1

	def getCpusInfo(self):
		res = []
		try:
			with open("/proc/stat", "r") as fd:
				for line in fd:
					if not line.startswith("cpu"):
						continue
					fields = line.split()
					if not fields or (fields[0] != "cpu" and not fields[0][3:].isdigit()):
						continue
					try:
						values = [int(value) for value in fields[1:]]
						if len(values) < 4:
							continue
						total = sum(values)
						idle = values[3] + (values[4] if len(values) > 4 else 0)
						res.append([fields[0], total, total - idle])
					except ValueError:
						continue
		except OSError:
			pass
		return res

	def poll(self):
		if not self.__callbacks:
			return
		current = self.getCpusInfo()
		if not current:
			# Preserve the last valid reading; do not compare against an empty snapshot.
			return
		previous = {entry[0]: entry for entry in self.__curr_info}
		self.__curr_info = current
		info = []
		for name, total, busy in current:
			old = previous.get(name)
			percent = 0
			if old is not None:
				delta_total, delta_busy = total - old[1], busy - old[2]
				if delta_total > 0 and delta_busy >= 0:
					percent = max(0, min(100, 100 * delta_busy // delta_total))
			info.append(percent)
		for callback in tuple(self.__callbacks):
			callback(info)

	def connectCallback(self, func):
		if func not in self.__callbacks:
			self.__callbacks.append(func)
		if not self.poll_enabled:
			self.poll()
			self.poll_enabled = True

	def disconnectCallback(self, func):
		if func in self.__callbacks:
			self.__callbacks.remove(func)
		if not len(self.__callbacks) and self.poll_enabled:
			self.poll_enabled = False

cpuUsageMonitor = CpuUsageMonitor()
