﻿#GlamourSpace converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

import os
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll
from os import statvfs

SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]

class GlamourSpace(Poll, Converter):
	MEMTOTAL, MEMFREE, SWAPTOTAL, SWAPFREE, USBSPACE, HDDSPACE, FLASHINFO, DATASPACE, NETSPACE, RAMINFO, SWAPINFO = range(11)

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)

		type = type.split(",")
		self.shortFormat = "Short" in type
		self.fullFormat = "Full" in type
		self.mainFormat = "Main" in type
		self.simpleFormat = "Simple" in type

		type_mapping = {
			"MemTotal": self.MEMTOTAL,
			"MemFree": self.MEMFREE,
			"SwapTotal": self.SWAPTOTAL,
			"SwapFree": self.SWAPFREE,
			"USBSpace": self.USBSPACE,
			"HDDSpace": self.HDDSPACE,
			"RAMInfo": self.RAMINFO,
			"SwapInfo": self.SWAPINFO,
			"NetSpace": self.NETSPACE,
			"DataSpace": self.DATASPACE,
			"FlashInfo": self.FLASHINFO
		}
		
		self.type = type_mapping.get(type[0], None)
		self.poll_interval = 5000 if self.type in (self.FLASHINFO, self.DATASPACE, self.HDDSPACE, self.USBSPACE, self.NETSPACE) else 1000
		self.poll_enabled = True

	@cached
	def getText(self):
		if self.type == self.NETSPACE:
			mount_point = self.getNetworkMount()
			if not mount_point:
				return "NetHDD: N/A"
			return self.getDiskUsage(mount_point, "NetHDD")
		
		if self.type in (self.RAMINFO, self.SWAPINFO):
			return self.getMemoryInfo()

		entry_mapping = {
			self.MEMTOTAL: ("Mem", "/proc/meminfo"),
			self.MEMFREE: ("Mem", "/proc/meminfo"),
			self.SWAPTOTAL: ("Swap", "/proc/meminfo"),
			self.SWAPFREE: ("Swap", "/proc/meminfo"),
			self.USBSPACE: ("USB", "/media/usb"),
			self.HDDSPACE: ("HDD", "/media/hdd"),
			self.FLASHINFO: ("Flash", "/"),
			self.DATASPACE: ("Data", "/data")
		}
		
		if self.type in entry_mapping:
			label, path = entry_mapping[self.type]
			return self.getDiskUsage(path, label)

		return "N/A"

	def getNetworkMount(self):
		try:
			for entry in os.scandir("/media/net"):
				if entry.is_dir():
					return entry.path
		except:
			pass
		return None

	def getDiskUsage(self, path, label):
		if not os.path.ismount(path):
			return f"{label}: N/A"

		try:
			st = statvfs(path)
			total = st.f_blocks * st.f_frsize
			free = st.f_bavail * st.f_frsize
			used = total - free
			percent = (used * 100) // total if total > 0 else 0
			
			if self.shortFormat:
				return f"{label}: {percent}%, {self.formatSize(free)} Free"
			elif self.mainFormat:
				return f"{label}: {self.formatSize(free)} Free, {self.formatSize(used)} Used, {self.formatSize(total)} Total"
			elif self.simpleFormat:
				return f"{label}: {percent}% ({self.formatSize(free)} Free, {self.formatSize(total)} Total)"
			elif self.fullFormat:
				return f"{label}: {percent}% ({self.formatSize(free)} Free, {self.formatSize(used)} Used, {self.formatSize(total)} Total)"
			else:
				return f"{label}: {self.formatSize(total)} ({self.formatSize(used)} Used, {self.formatSize(free)} Free)"
		except:
			return f"{label}: N/A"

	def getMemoryInfo(self):
		try:
			with open("/proc/meminfo", "r") as f:
				meminfo = {line.split(":")[0]: int(line.split()[1]) for line in f if len(line.split()) > 1}
				ram = f"RAM: Total {meminfo.get('MemTotal', 0) // 1024} MB, Used {((meminfo.get('MemTotal', 0) - meminfo.get('MemFree', 0)) // 1024)} MB, Free {meminfo.get('MemFree', 0) // 1024} MB"
				swap = f"Swap: Total {meminfo.get('SwapTotal', 0) // 1024} MB, Used {((meminfo.get('SwapTotal', 0) - meminfo.get('SwapFree', 0)) // 1024)} MB, Free {meminfo.get('SwapFree', 0) // 1024} MB"
				return ram if self.type == self.RAMINFO else swap
		except:
			return "Memory Info: N/A"

	def formatSize(self, value, unit_index=0):
		while value >= 1024 and unit_index < len(SIZE_UNITS) - 1:
			value /= 1024.0
			unit_index += 1
		return f"{value:.2f} {SIZE_UNITS[unit_index]}"

	text = property(getText)
