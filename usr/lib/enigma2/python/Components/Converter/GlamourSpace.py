#	GlamourSpace converter
#	Modded and recoded by MCelliotG for use in Glamour skins or standalone, added Python3 support
#	If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

from __future__ import absolute_import, division
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll
import os
from os import popen, statvfs, path
SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]

class GlamourSpace(Poll, Converter):
	MEMTOTAL = 0
	MEMFREE = 1
	SWAPTOTAL = 2
	SWAPFREE = 3
	USBSPACE = 4
	HDDSPACE = 5
	FLASHINFO = 6
	DATASPACE = 7
	NETSPACE = 8
	RAMINFO = 9
	SWAPINFO = 10

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		type = type.split(",")
		self.shortFormat = "Short" in type
		self.fullFormat = "Full" in type
		self.mainFormat = "Main" in type
		self.simpleFormat = "Simple" in type
		if "MemTotal" in type:
			self.type = self.MEMTOTAL
		elif "MemFree" in type:
			self.type = self.MEMFREE
		elif "SwapTotal" in type:
			self.type = self.SWAPTOTAL
		elif "SwapFree" in type:
			self.type = self.SWAPFREE
		elif "USBSpace" in type:
			self.type = self.USBSPACE
		elif "HDDSpace" in type:
			self.type = self.HDDSPACE
		elif "RAMInfo" in type:
			self.type = self.RAMINFO
		elif "SwapInfo" in type:
			self.type = self.SWAPINFO
		elif "NetSpace" in type:
			self.type = self.NETSPACE
		elif "DataSpace" in type:
			self.type = self.DATASPACE
		elif "FlashInfo" in type:
			self.type = self.FLASHINFO
		if self.type in (self.FLASHINFO, self.DATASPACE, self.HDDSPACE, self.USBSPACE, self.NETSPACE):
			self.poll_interval = 5000
		else:
			self.poll_interval = 1000
		self.poll_enabled = True


	@cached
	def getText(self):
		text = "N/A"

		if (self.type == self.RAMINFO):
			ramfree = ""
			ramavail = ""
			ramtotal = ""
			try:
				if os.path.exists("/proc/meminfo"):
					with open("/proc/meminfo") as ram:
						raminfo = ram.readlines()
						for lines in raminfo:
							lisp = lines.split()
							if (lisp[0].startswith("MemFree:")):
								ramfree = str(float(lisp[1]) // 1024)
								ramfree = "%.6s MB Free, " % ramfree
							if (lisp[0].startswith("MemAvailable:")):
								ramavail = str(float(lisp[1]) // 1024)
								ramavail = "%.6s MB Avail. " % ramavail
							if (lisp[0].startswith("MemTotal:")):
								ramtotal = str(int(lisp[1]) // 1024)
								ramtotal = "%s MB Total " % ramtotal 
			except:
				pass
			if ramfree == "" and ramavail == "" and ramtotal == "":
				return "N/A"
			return "RAM: " + ramfree + ramavail + ramtotal

		elif (self.type == self.SWAPINFO):
			swapfree = ""
			swapcached = ""
			swaptotal = ""
			try:
				if os.path.exists("/proc/meminfo"):
					with open("/proc/meminfo") as swp:
						swpinfo = swp.readlines()
						for lines in swpinfo:
							lisp = lines.split()
							if (lisp[0].startswith("SwapFree:")):
								swapfree = str(int(lisp[1]) // 1024)
								swapfree = "%s MB Free, " % swapfree
							if (lisp[0].startswith("SwapCached:")):
								swapcached = str(int(lisp[1]) // 1024)
								swapcached = "%s MB Cached, " % swapcached
							if (lisp[0].startswith("SwapTotal:")):
								swaptotal = str(int(lisp[1]) // 1024)
								swaptotal = "%s MB Total " % swaptotal
			except:
				pass
			if swapfree == "" and swaptotal == "":
				return "N/A"
			elif self.fullFormat:
				return "Swap: %s %s %s" % (swapfree, swapcached, swaptotal)
			else:
			 return "Swap: %s %s" % (swapfree, swaptotal)

		else:
			entry = {self.MEMTOTAL: ("Mem", "Mem", "Ram"),
			 self.MEMFREE: ("Mem", "Mem", "Ram"),
			 self.SWAPTOTAL: ("Swap", "Swap", "Swap"),
			 self.SWAPFREE: ("Swap", "Swap", "Swap"),
			 self.USBSPACE: ("/media/usb", "/media/usb", "USB"),
			 self.HDDSPACE: ("/media/hdd", "/media/hdd", "HDD"),
			 self.NETSPACE: ("/media/net/hdd", "/media/net/hdd", "LanHDD"),
			 self.FLASHINFO: ("/", "/usr/lib/enigma2/python/Plugins/Extensions/OpenMultiboot", "Flash"),
			 self.DATASPACE: ("/data", "/var/volatile", "Data")}[self.type]
			if self.type in (self.USBSPACE, self.HDDSPACE, self.FLASHINFO, self.DATASPACE, self.NETSPACE):
				lisp = self.getDiskInfo(entry[0])
			elif self.type in (self.MEMTOTAL, self.MEMFREE, self.SWAPTOTAL, self.SWAPFREE):
				lisf = self.getMemInfo(entry[0])
			if lisp[0] == 0 and (self.type == self.FLASHINFO) or lisp[0] == 0 and (self.type == self.DATASPACE):
				lisf = self.getDiskInfo(entry[1])
			else:
				lisf = self.getDiskInfo(entry[0])
			if lisf[0] == 0:
				text = "%s: N/A" % entry[2]
			elif self.shortFormat:
				text = "%s: %s%%, %s Free" % (entry[2], lisf[3], self.getSizeStr(lisf[2]))
			elif self.mainFormat:
				text = "%s: %s Free, %s Used, %s Total" % (entry[2], self.getSizeStr(lisf[2]), self.getSizeStr(lisf[1]), self.getSizeStr(lisf[0]))
			elif self.simpleFormat:
				text = "%s: %s%% (%s Free, %s Total)" % (entry[2], lisf[3], self.getSizeStr(lisf[2]), self.getSizeStr(lisf[0]))
			elif self.fullFormat:
				text = "%s: %s%% (%s Free, %s Used, %s Total)" % (entry[2], lisf[3], self.getSizeStr(lisf[2]), self.getSizeStr(lisf[1]), self.getSizeStr(lisf[0]))
			else:
				text = "%s: %s (%s Used, %s Free)" % (entry[2], self.getSizeStr(lisf[0]), self.getSizeStr(lisf[1]), self.getSizeStr(lisf[2]))
		return text

	@cached
	def getValue(self):
		result = 0
		if self.type in (self.MEMTOTAL, self.MEMFREE, self.SWAPTOTAL, self.SWAPFREE):
			entry = {self.MEMTOTAL: "Mem",
			 self.MEMFREE: "Mem",
			 self.SWAPTOTAL: "Swap",
			 self.SWAPFREE: "Swap"}[self.type]
			result = self.getMemInfo(entry)[3]
		elif self.type in (self.USBSPACE, self.HDDSPACE, self.FLASHINFO, self.DATASPACE, self.NETSPACE):
			path = {self.USBSPACE: "/media/usb",
			 self.HDDSPACE: "/media/hdd",
			 self.NETSPACE: "/media/net/hdd",
			 self.FLASHINFO: "/",
			 self.DATASPACE: "/data"}[self.type]
			result = self.getDiskInfo(path)[3]
		return result

	text = property(getText)
	value = property(getValue)
	range = 100


	def getMemInfo(self, value):
		result = [0,
		 0,
		 0,
		 0]
		try:
			check = 0
			with open("/proc/meminfo") as fd:
				for line in fd:
					if value + "Total" in line:
						check += 1
						result[0] = int(line.split()[1]) * 1024
					elif value + "Free" in line:
						check += 1
						result[2] = int(line.split()[1]) * 1024
					if check > 1:
						if result[0] > 0:
							result[1] = result[0] - result[2]
							result[3] = result[1] * 100 // result[0]
						break
		except:
			pass

		return result

	def getDiskInfo(self, path):

		def isMountPoint():
			try:
				with open("/proc/mounts", "r") as fd:
					for line in fd:
						l = line.split()
						if len(l) > 1 and l[1] == path:
							return True
			except:
				return None
			return False

		result = [0,
		 0,
		 0,
		 0]
		if isMountPoint():
			try:
				st = statvfs(path)
			except:
				st = None

			if st != None and 0 not in (st.f_bsize, st.f_blocks):
				result[0] = st.f_bsize * st.f_blocks
				result[2] = st.f_bsize * st.f_bavail
				result[1] = result[0] - result[2]
				result[3] = result[1] * 100 // result[0]
		return result

	def getSizeStr(self, value, u = 0):
		fractal = 0
		if value >= 1024:
			fmt = "%(size)u.%(frac)d %(unit)s"
			while value >= 1024 and u < len(SIZE_UNITS):
				value, mod = divmod(value, 1024)
				fractal = mod * 10 // 1024
				u += 1

		else:
			fmt = "%(size)u %(unit)s"
		return fmt % {"size": value,
		 "frac": fractal,
		 "unit": SIZE_UNITS[u]}

	def doSuspend(self, suspended):
		if suspended:
			self.poll_enabled = False
		else:
			self.downstream_elements.changed((self.CHANGED_POLL,))
			self.poll_enabled = True