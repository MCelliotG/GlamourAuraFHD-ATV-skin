#GlamourExtra converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone
#If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

import os
import re
from time import monotonic
from Components.Converter.Converter import Converter 
from Components.Element import cached 
from Components.Converter.Poll import Poll
from enigma import eConsoleAppContainer 

class GlamourExtra(Poll, Converter):
	TEMPERATURE = 0
	HDDTEMP = 1
	CPULOAD = 2
	CPUSPEED = 3
	FANINFO = 4
	UPTIME = 5

	TYPE_MAPPING = {
		"CPULoad": CPULOAD,
		"CPUSpeed": CPUSPEED,
		"Temperature": TEMPERATURE,
		"Uptime": UPTIME,
		"HDDTemp": HDDTEMP,
		"FanInfo": FANINFO
	}
	TEMPERATURE_PATHS = {
		"System": "/proc/stb/sensors/temp0/value",
		"Board": "/proc/stb/fp/temp_sensor",
		"CPU": "/sys/devices/virtual/thermal/thermal_zone0/temp",
		"AVS": "/proc/stb/fp/temp_sensor_avs"
	}
	FAN_PATHS = {
		"Speed": "/proc/stb/fp/fan_speed",
		"V": "/proc/stb/fp/fan_vlt",
		"PWM": "/proc/stb/fp/fan_pwm"
	}

	HDD_POLL_INTERVAL = 60000
	HDD_COMMAND = "hddtemp -n -q -u C /dev/sda"

	CPU_MHZ_PATTERN = re.compile(r"cpu MHz\s+:\s+([\d.]+)")

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.container = None
		self._destroyed = False
		self._hddRunning = False
		self._lastHddStart = None
		self.type = self.getType(type)
		self.hddtemp = "Waiting for HDD Temp Data..."

		if self.type == self.HDDTEMP:
			self.container = eConsoleAppContainer()
			self._hddChunks = []
			self.container.appClosed.append(self.runFinished)
			self.container.dataAvail.append(self.dataAvail)
			self.poll_interval = self.HDD_POLL_INTERVAL
			self._startHddMeasurement()
		elif self.type == self.UPTIME:
			self.poll_interval = 1000
		else:
			self.poll_interval = 7000

		self.poll_enabled = True

	def getType(self, type):
		mapping = self.TYPE_MAPPING
		return mapping.get(type.split(",")[0], None)

	def _startHddMeasurement(self):
		if self._destroyed or self.container is None or self._hddRunning:
			return
		now = monotonic()
		if self._lastHddStart is not None and now - self._lastHddStart < self.HDD_POLL_INTERVAL / 1000.0:
			return
		self._lastHddStart = now
		self._hddChunks = []
		self._hddRunning = True
		try:
			failed = self.container.execute(self.HDD_COMMAND)
		except Exception:
			failed = True
		if failed:
			self._hddRunning = False
			self.hddtemp = "HDD Temp: N/A"

	def dataAvail(self, strData):
		if self._destroyed or not self._hddRunning:
			return
		if isinstance(strData, str):
			strData = strData.encode("utf-8")
		self._hddChunks.append(strData)

	def runFinished(self, retval):
		if self._destroyed:
			return
		output = b"".join(self._hddChunks).decode("utf-8", "ignore").strip()
		self._hddChunks = []
		self._hddRunning = False
		if "No such file or directory" in output or "not found" in output:
			self.hddtemp = "HDD Temp: N/A"
		elif output.isdigit():
			temp_value = int(output)
			self.hddtemp = f"HDD Temp: {temp_value}°C" if temp_value > 0 else "HDD idle or N/A"
		else:
			self.hddtemp = "HDD idle or N/A"
		Converter.changed(self, (self.CHANGED_POLL,))

	def poll(self):
		if self._destroyed:
			return
		if self.type == self.HDDTEMP:
			self._startHddMeasurement()
		self.changed((self.CHANGED_POLL,))

	@cached
	def getText(self):
		if self.type == self.CPULOAD:
			return self.getCpuLoad()
		elif self.type == self.TEMPERATURE:
			return self.getTemperature()
		elif self.type == self.HDDTEMP:
			return self.hddtemp
		elif self.type == self.CPUSPEED:
			return self.getCpuSpeed()
		elif self.type == self.FANINFO:
			return self.getFanInfo()
		elif self.type == self.UPTIME:
			return self.getUptime()
		return "N/A"

	def getCpuLoad(self):
		try:
			with open("/proc/loadavg", "r") as f:
				return f"CPU Load: {f.readline().split()[0]}"
		except:
			return "CPU Load: N/A"

	def getTemperature(self):
		temps = {}
		paths = self.TEMPERATURE_PATHS
		
		for label, path in paths.items():
			if os.path.exists(path):
				try:
					with open(path, "r") as f:
						temp = f.read().strip()
						if temp.isdigit():
							temps[label] = f"{int(temp) // (1000 if label == 'CPU' else 1)}°C"
				except:
					pass
		hisi_path = "/proc/hisi/msp/pm_cpu"
		if os.path.exists(hisi_path):
			try:
				with open(hisi_path, "r") as f:
					for line in f:
						parts = [x.strip() for x in line.strip().split(":")]
						if parts[0] == "Tsensor":
							ctemp = parts[1].split("=")[-1].split()[0]
							temps["HISI CPU"] = f"{ctemp}°C"
			except:
				pass

		if not temps:
			return "Temperature: N/A"
		
		return "  ".join(f"{k}: {v}" for k, v in temps.items())

	def getCpuSpeed(self):
		try:
			with open("/proc/cpuinfo", "r") as f:
				match = self.CPU_MHZ_PATTERN.search(f.read())
				if match:
					return f"CPU Speed: {int(float(match.group(1)))} MHz"
			try:
				with open("/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency", "rb") as f:
					data = f.read()
					if not data:
						raise ValueError("Empty clock frequency")
					freq = int.from_bytes(data, "big") // 1000000
					return f"CPU Speed: {freq} MHz"
			except FileNotFoundError:
				pass
			with open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", "r") as f:
				return f"CPU Speed: {int(f.read().strip()) // 1000} MHz"
		except Exception:
			return "CPU Speed: N/A"

	def getFanInfo(self):
		paths = self.FAN_PATHS
		fan_data = {label: "N/A" for label in paths}
		found = False
		for label, path in paths.items():
			if os.path.exists(path):
				try:
					with open(path, "r") as f:
						value = f.read().strip()
						if value:
							fan_data[label] = value
							found = True
				except:
					pass
		return "Fan Info: N/A" if not found else "Fan: " + "  ".join(f"{k}: {v}" for k, v in fan_data.items())

	def getUptime(self):
		try:
			with open("/proc/uptime", "r") as f:
				total_seconds = int(float(f.readline().split()[0]))
		except:
			return "Uptime: N/A"

		days, remainder = divmod(total_seconds, 86400)
		hours, remainder = divmod(remainder, 3600)
		minutes, seconds = divmod(remainder, 60)
		return f"Uptime: {days}d {hours}h {minutes}m {seconds}s"

	text = property(getText)

	def changed(self, what):
		Converter.changed(self, what)

	def destroy(self):
		self._destroyed = True
		if self.container is not None:
			for callbacks, callback in ((self.container.appClosed, self.runFinished), (self.container.dataAvail, self.dataAvail)):
				if callback in callbacks:
					callbacks.remove(callback)
			if self._hddRunning:
				try:
					self.container.kill()
				except (AttributeError, RuntimeError):
					pass
			self.container = None
		self._hddRunning = False
		self._hddChunks = []
		Poll.destroy(self)
