# GlamCPU converter (Python 3)
# Modded and recoded by MCelliotG for use in Glamour skins or standalone
# If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached

class GlamCPU(Converter, object):
	CPU_ALL = -2
	CPU_TOTAL = -1

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

	def gotPercentage(self, list):
		self.percentlist = list
		self.changed((self.CHANGED_POLL,))

	@cached
	def getText(self):
		if not self.percentlist:
			return ""
		
		cpu_count = len(self.percentlist)
		res = self.sfmt[:]
		
		for i in range(16):
			if f"${i}" in res:
				res = res.replace(f"${i}", f"{self.percentlist[i]}%" if i < cpu_count else "")
		
		res = res.replace("$?", str(cpu_count - 1))
		
		if self.sfmt in ["All", "Default"]:
			if self.format_type == "Separator":
				return f"CPU: {self.percentlist[0]}% (" + " | ".join(f"{p}%" for p in self.percentlist[1:]) + ")"
			elif self.format_type == "Newline":
				return f"Total: {self.percentlist[0]}%\n" + "\n".join(f"C{i}: {p}%" for i, p in enumerate(self.percentlist[1:], 1))
			elif self.format_type == "Full":
				return f"Total: {self.percentlist[0]}% " + " ".join(f"Core{i}: {p}%" for i, p in enumerate(self.percentlist[1:], 1))
			else:
				core_loads = " ".join(f"{p}%" for p in self.percentlist[1:])
				return f"CPU: {self.percentlist[0]}% ({core_loads})" if core_loads else f"CPU: {self.percentlist[0]}%"
		
		return res.strip()

	@cached
	def getValue(self):
		try:
			return self.percentlist[0] if self.sfmt in ["All", "Default"] else self.percentlist[int(self.sfmt)]
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
			fd = open("/proc/stat", "r")
			for l in fd:
				if l.startswith("cpu"):
					total = busy = 0
					tmp = l.split()
					for i in range(1, len(tmp)):
						tmp[i] = int(tmp[i])
						total += tmp[i]
					busy = total - tmp[4] - tmp[5]
					res.append([tmp[0], total, busy])
			fd.close()
		except:
			pass
		return res

	def poll(self):
		prev_info, self.__curr_info = self.__curr_info, self.getCpusInfo()
		if len(self.__callbacks):
			info = []
			for i in range(len(self.__curr_info)):
				try:
					p = 100 * (self.__curr_info[i][2] - prev_info[i][2]) // (self.__curr_info[i][1] - prev_info[i][1])
				except ZeroDivisionError:
					p = 0
				info.append(p)
			for f in self.__callbacks:
				f(info)

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
