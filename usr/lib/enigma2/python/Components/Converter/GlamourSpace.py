#GlamourSpace converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

import os
import re
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll
from os import statvfs

SIZE_UNITS = ("B", "KB", "MB", "GB", "TB", "PB", "EB")

class GlamourSpace(Poll, Converter):
	MEMTOTAL, MEMFREE, SWAPTOTAL, SWAPFREE, USBSPACE, HDDSPACE, FLASHINFO, DATASPACE, NETSPACE, RAMINFO, SWAPINFO, BUFFERINFO = range(12)

	TYPE_MAPPING = {
		"MemTotal": MEMTOTAL,
		"MemFree": MEMFREE,
		"SwapTotal": SWAPTOTAL,
		"SwapFree": SWAPFREE,
		"USBSpace": USBSPACE,
		"HDDSpace": HDDSPACE,
		"RAMInfo": RAMINFO,
		"SwapInfo": SWAPINFO,
		"NetSpace": NETSPACE,
		"DataSpace": DATASPACE,
		"FlashInfo": FLASHINFO,
		"BufferInfo": BUFFERINFO
	}

	MEMORY_FIELDS = {
		MEMTOTAL: ("Mem", "MemTotal"),
		MEMFREE: ("Mem", "MemFree"),
		SWAPTOTAL: ("Swap", "SwapTotal"),
		SWAPFREE: ("Swap", "SwapFree"),
	}
	DISK_ENTRIES = {
		USBSPACE: ("USB", "/media/usb"),
		HDDSPACE: ("HDD", "/media/hdd"),
		FLASHINFO: ("Flash", "/"),
		DATASPACE: ("Data", "/data"),
	}

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)

		type = type.split(",")
		self.shortFormat = "Short" in type
		self.fullFormat = "Full" in type
		self.mainFormat = "Main" in type
		self.simpleFormat = "Simple" in type

		self.type = self.TYPE_MAPPING.get(type[0])
		self.poll_interval = 5000 if self.type in (self.FLASHINFO, self.BUFFERINFO, self.DATASPACE, self.HDDSPACE, self.USBSPACE, self.NETSPACE) else 1000
		self.poll_enabled = True

	@cached
	def getText(self):
		if self.type == self.NETSPACE:
			mount_point = self.getNetworkMount()
			if not mount_point:
				return "NetHDD: N/A"
			return self.getDiskUsage(mount_point, "NetHDD")

		if self.type in (self.RAMINFO, self.SWAPINFO, self.BUFFERINFO):
			return self.getMemoryInfo()

		if self.type in self.MEMORY_FIELDS:
			return self.getMemoryInfo()

		entry = self.DISK_ENTRIES.get(self.type)
		if entry:
			label, path = entry
			return self.getDiskUsage(path, label)

		return "N/A"

	NETWORK_FILESYSTEMS = frozenset(("nfs", "nfs4", "cifs", "smb3", "smbfs", "fuse.sshfs", "sshfs", "davfs", "davfs2", "fuse.davfs"))

	@staticmethod
	def _decodeMountPath(value):
		return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)

	def getNetworkMount(self):
		"""Find the mounted network filesystem used as /media/hdd, not another share."""
		try:
			hdd_path = os.path.realpath("/media/hdd")
			selected_mount = None
			selected_type = None
			with open("/proc/mounts", "r") as mounts:
				for line in mounts:
					fields = line.split()
					if len(fields) < 3:
						continue
					mount_path = os.path.normpath(self._decodeMountPath(fields[1]))
					if not mount_path.startswith("/"):
						continue
					# The most specific mount wins, including a local filesystem
					# mounted inside a network share.
					prefix = mount_path.rstrip("/") + "/"
					if hdd_path == mount_path or hdd_path.startswith(prefix):
						if selected_mount is None or len(mount_path) >= len(selected_mount):
							selected_mount, selected_type = mount_path, fields[2].lower()
			if selected_type in self.NETWORK_FILESYSTEMS:
				return selected_mount
		except (OSError, ValueError):
			pass
		return None

	def getDiskUsage(self, path, label):
		try:
			if not os.path.ismount(path):
				return f"{label}: N/A"
			st = statvfs(path)
			total = (st.f_blocks * st.f_frsize) // 1024
			free = (st.f_bavail * st.f_frsize) // 1024
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
		except (OSError, ValueError, TypeError, ArithmeticError):
			return f"{label}: N/A"

	def getMemoryInfo(self):
		try:
			with open("/proc/meminfo", "r") as f:
				meminfo = {}
				for line in f:
					parts = line.split()
					if len(parts) > 1:
						meminfo[parts[0].rstrip(":")] = int(parts[1])

			field = self.MEMORY_FIELDS.get(self.type)
			if field:
				label, key = field
				return f"{label}: {self.formatSize(meminfo.get(key, 0))}"
			if self.type == self.BUFFERINFO:
				return f"Buffer: {self.formatSize(meminfo.get('Buffers', 0))}"
			if self.type == self.RAMINFO:
				label, total_key, free_key = "RAM", "MemTotal", "MemFree"
			else:
				label, total_key, free_key = "Swap", "SwapTotal", "SwapFree"
			total = meminfo.get(total_key, 0)
			free = meminfo.get(free_key, 0)
			return f"{label}: Total {self.formatSize(total)}, Used {self.formatSize(total - free)}, Free {self.formatSize(free)}"

		except (OSError, ValueError, KeyError):
			return "Memory Info: N/A"

	def formatSize(self, value, unit_index=1):
		while value >= 1024 and unit_index < len(SIZE_UNITS) - 1:
			value /= 1024.0
			unit_index += 1
		if unit_index == 1:
			formatted_value = f"{value:.3g}"
		else:
			formatted_value = f"{value:.2f}"
		return f"{formatted_value} {SIZE_UNITS[unit_index]}"

	text = property(getText)
