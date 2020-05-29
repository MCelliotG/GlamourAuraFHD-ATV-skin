#  GlamourExtra Converter
#  Modded and recoded by MCelliotG for use in Glamour skins or standalone
#  HDDtemp new detection added by betacentauri, many thanks!!!
#  If you use this Converter for other skins and rename it, please keep the first and second line adding your credits below

from Components.Converter.Converter import Converter 
from Components.Element import cached 
from Poll import Poll
from enigma import eConsoleAppContainer 
from os import system, path, popen
from Tools.Directories import fileExists

class GlamourExtra(Poll, Converter):
	TEMPERATURE = 0
	HDDTEMP = 1
	CPULOAD = 2
	CPUSPEED = 3
	FANINFO = 4
	UPTIME = 5


	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.container = eConsoleAppContainer()
		type = type.split(",")
		self.short_list = True
		self.list = []
		self.shortFormat = "Short" in type
		if "CPULoad" in type:
			self.type = self.CPULOAD
		elif "CPUSpeed" in type:
			self.type = self.CPUSPEED
		elif "Temperature" in type:
			self.type = self.TEMPERATURE
		elif "Uptime" in type:
			self.type = self.UPTIME
		elif "HDDTemp" in type:
			self.type = self.HDDTEMP
			self.hddtemp_output = ""
			self.hddtemp = "Waiting for HDD Temp Data..."
			self.container.appClosed.append(self.runFinished)
			self.container.dataAvail.append(self.dataAvail)
			self.container.execute("hddtemp -n -q /dev/sda")
		elif "FanInfo" in type:
			self.type = self.FANINFO
		if "HDDTemp" in type:
			self.poll_interval = 500
		else:
			self.poll_interval = 7000
		self.poll_enabled = True


	def dataAvail(self, strData):
		self.hddtemp_output = self.hddtemp_output + strData

	def runFinished(self, retval):
		temp = str(self.hddtemp_output)
		if "No such file or directory" in temp or "not found" in temp:
			htemp = ""
			self.hddtemp = "HDD Temp: N/A"
		else:
			htemp = str(int(temp))
			if htemp == "0" or htemp is None:
				self.hddtemp = "HDD idle or N/A"
			else:
				self.hddtemp = "HDD Temp: " + htemp + "°C"

	@cached
	def getText(self):
		if (self.type == self.CPULOAD):
			cpuload = ""
			if fileExists("/proc/loadavg"):
				try:
					with open("/proc/loadavg", "r") as l:
						load = l.readline(4)
				except:
					load = ""
				cpuload = load.replace("\n", "").replace(" ","")
				return "CPU Load: %s" % cpuload

		elif (self.type == self.TEMPERATURE):
			systemp = ""
			cputemp = ""
			try:
				if fileExists("/proc/stb/sensors/temp0/value"):
					with open("/proc/stb/sensors/temp0/value") as stemp:
						systemp = "Sys Temp: " + stemp.readline().replace("\n", "") + "°C"
				elif fileExists("/proc/stb/fp/temp_sensor"):
					with open("/proc/stb/fp/temp_sensor") as stemp:
						systemp = "Board: " + stemp.readline().replace("\n", "") + "°C"
				if fileExists("/proc/stb/fp/temp_sensor_avs"):
					with open("/proc/stb/fp/temp_sensor_avs") as ctemp:
						cputemp = ctemp.readline().replace("\n", "") + "°C"
				elif fileExists("/sys/devices/virtual/thermal/thermal_zone0/temp"):
					with open("/sys/devices/virtual/thermal/thermal_zone0/temp") as ctemp:
						cputemp = ctemp.read()[:2].replace("\n", "") + "°C"
				elif fileExists("/proc/hisi/msp/pm_cpu"):
					for line in open("/proc/hisi/msp/pm_cpu").readlines():
						line = [x.strip() for x in line.strip().split(":")]
						if line[0] in ("Tsensor"):
							ctemp = line[1].split("=")
							ctemp = line[1].split(" ")
							cputemp = ctemp[2] + "°C"
			except:
				pass
			if systemp == "" and cputemp == "":
				return "Temperature: N/A"
			if systemp == "":
				return "CPU Temp: " + cputemp
			if cputemp == "":
				return systemp
			return systemp + "  " + "CPU: " + cputemp

		elif (self.type == self.HDDTEMP):
			return self.hddtemp

		elif (self.type == self.CPUSPEED):
			try:
				cpuspeed = 0
				for line in open("/proc/cpuinfo").readlines():
					line = [x.strip() for x in line.strip().split(":")]
					if line[0] == "cpu MHz":
						 cpuspeed = "%1.0f" % float(line[1])
				if not cpuspeed:
					try:
						cpuspeed = int(open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq").read()) / 1000
					except:
						try:
							import binascii
							cpuspeed = int(int(binascii.hexlify(open("/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency", "rb").read()), 16) / 100000000) * 100
						except:
							cpuspeed = "-"
				return "CPU Speed: %s MHz" % cpuspeed
			except:
				return ""

		if (self.type == self.FANINFO):
			fs = ""
			fv = ""
			fp = ""
			try:
				if fileExists("/proc/stb/fp/fan_speed"):
					with open("/proc/stb/fp/fan_speed", "r") as fs:
						fs = str(fs.readline().strip())
				if fileExists("/proc/stb/fp/fan_vlt"):
					with open("/proc/stb/fp/fan_vlt", "r") as fv:
						fv = str(int(fv.readline().strip(), 16))
				if fileExists("/proc/stb/fp/fan_pwm"):
					with open("/proc/stb/fp/fan_pwm", "r") as fp:
						fp = str(int(fp.readline().strip(), 16))
			except:
				pass
			if fs == "":
				return "Fan Info: N/A"
			if self.shortFormat:
				return "%s - %sV - P:%s" % (fs, fv, fp)
			else:
				return "Speed: %s V: %s PWM: %s" % (fs, fv, fp)

		elif (self.type == self.UPTIME):
			try:
				with open("/proc/uptime", "r") as up:
					uptime_info = up.read().split()
			except:
				return "Uptime: N/A"
				uptime_info = None
			if uptime_info is not None:
				total_seconds = float(uptime_info[0])
				MINUTE = 60
				HOUR = MINUTE * 60
				DAY = HOUR * 24
				days = str(int(total_seconds / DAY))
				hours = str(int(total_seconds % DAY / HOUR))
				minutes = str(int(total_seconds % HOUR / MINUTE))
				seconds = str(int(total_seconds % MINUTE))
				uptime = ""
				if self.shortFormat:
					uptime = "%sd %sh %sm %ss" % (days, hours, minutes, seconds)
				else:
					if days > "0":
						uptime += days + " " + (days == "1" and "day" or "days") + ", "
					if len(uptime) > 0 or hours > "0":
						uptime += hours + " " + (hours == "1" and "hr" or "hrs") + ", "
					if len(uptime) > 0 or minutes > "0":
						uptime += minutes + " " + (minutes == "1" and "min" or "mins")
				return "Uptime: %s" % uptime

		return text

	text = property(getText)

	def changed(self, what):
		if what[0] == self.CHANGED_POLL:
			self.downstream_elements.changed(what)
