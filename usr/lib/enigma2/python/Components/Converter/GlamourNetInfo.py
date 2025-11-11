# GlamourNetInfo converter (Python 3)
# Fully coded by MCelliotG for use in Glamour skins or standalone universal E2
# Ethernet-first & Full WiFi Interface Polling
# If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

import os
import shlex
import time
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll
from enigma import eConsoleAppContainer

class GlamourNetInfo(Poll, Converter):
	ICON = 0
	INTERNAL_IP = 1
	EXTERNAL_IP = 2
	NET_TYPE = 3
	NET_STATUS = 4
	WIFI_PERCENT = 5
	WIFI_BARS = 6
	WIFI_RSSI = 7
	WIFI_RSSI_VALUE = 8
	WIFI_LINKSPEED = 9
	WIFI_LINKSPEED_VALUE = 10
	WIFI_FREQUENCY = 11
	WIFI_BAND = 12
	WIFI_BAND_ICON = 13
	WIFI_CHANNEL = 14
	ETH_SPEED = 15
	ETH_SPEED_VALUE = 16
	ETH_CARRIER = 17
	IP_TYPE = 18
	HAS_IPV6 = 19

	EXTERNAL_IP_INTERVAL = 20*60  # 20 minutes
	WIFI_REFRESH_INTERVAL = 2	 # seconds

	def __init__(self, type, wifi_interval=None, external_ip_interval=None):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.type = self.getType(type)

		# Custom intervals
		self.WIFI_REFRESH_INTERVAL = wifi_interval or self.WIFI_REFRESH_INTERVAL
		self.EXTERNAL_IP_INTERVAL = external_ip_interval or self.EXTERNAL_IP_INTERVAL

		# Containers
		self._container_iface = eConsoleAppContainer()
		self._container_iface.dataAvail.append(self._onIfaceData)
		self._container_iface.appClosed.append(self._onIfaceFetched)

		self._container_external_ip = eConsoleAppContainer()
		self._container_external_ip.dataAvail.append(self._onExternalIPData)
		self._container_external_ip.appClosed.append(self._onExternalIPFetched)

		# Cached values
		self._internal_ip = ""
		self._external_ip = ""
		self._external_ip_ts = 0
		self._iface_buffer = ""
		self._external_ip_buffer = ""
		self._eth_carrier = "0"
		self._eth_speed = None
		self._net_type = "offline"
		self._net_status = "no_carrier"
		self._ip_type = "ipv4"
		self._has_ipv6 = "0"
		self._wifi_percent = 0
		self._wifi_bars = 0
		self._wifi_rssi = None
		self._wifi_freq = None
		self._wifi_channel = None
		self._wifi_bandid = None
		self._wifi_speed = None
		self._last_status = None
		self._last_wifi_update = 0

		# Start polling
		self.poll_interval = 1000
		self.poll_enabled = True
		self.poll()

	def getType(self, type):
		m = {
			"Icon": self.ICON,
			"InternalIP": self.INTERNAL_IP,
			"ExternalIP": self.EXTERNAL_IP,
			"NetType": self.NET_TYPE,
			"NetStatus": self.NET_STATUS,
			"WifiPercent": self.WIFI_PERCENT,
			"WifiBars": self.WIFI_BARS,
			"WifiRSSI": self.WIFI_RSSI,
			"WifiRSSIValue": self.WIFI_RSSI_VALUE,
			"WifiLinkSpeed": self.WIFI_LINKSPEED,
			"WifiLinkSpeedValue": self.WIFI_LINKSPEED_VALUE,
			"WifiFrequency": self.WIFI_FREQUENCY,
			"WifiBand": self.WIFI_BAND,
			"WifiBandIcon": self.WIFI_BAND_ICON,
			"WifiChannel": self.WIFI_CHANNEL,
			"EthSpeed": self.ETH_SPEED,
			"EthSpeedValue": self.ETH_SPEED_VALUE,
			"EthCarrier": self.ETH_CARRIER,
			"IPType": self.IP_TYPE,
			"HasIPv6": self.HAS_IPV6
		}
		return m.get(type.split(",")[0], self.ICON)

	# External IP
	def _fetch_external_ip(self):
		now = time.time()
		# If external ip exists and it's fresh, skip
		# (but if external_ip_ts was set to 0 elsewhere, this will run)
		if now - self._external_ip_ts < self.EXTERNAL_IP_INTERVAL and self._external_ip:
			return
		cmd = "wget -qO- https://api.ipify.org"
		self._external_ip_buffer = ""
		try:
			self._container_external_ip.execute(cmd)
		except:
			# container failed — bail silently
			self._extip_running = False

	def _onExternalIPData(self, data):
		try:
			self._external_ip_buffer += data.decode("utf-8", "ignore")
		except:
			pass

	def _onExternalIPFetched(self, retval):
		val = self._external_ip_buffer.strip()
		self._external_ip_buffer = ""
		if val and not val.startswith("/bin/sh:"):
			self._external_ip = val
		else:
			self._external_ip = ""
		self._external_ip_ts = time.time()
		Converter.changed(self, (self.CHANGED_POLL,))

	# Interface polling
	def _fetch_iface_info(self, iface, is_wifi=False):
		# rate-limit wifi intensive queries
		now = time.time()
		update_wifi = is_wifi and (now - self._last_wifi_update > self.WIFI_REFRESH_INTERVAL)
		# For wifi: only skip if not time yet
		if is_wifi and not update_wifi:
			return

		# build command: ipv4 + ipv6, and wpa_cli only for wifi
		cmd = f"/sbin/ip -4 addr show dev {shlex.quote(iface)} ; /sbin/ip -6 addr show dev {shlex.quote(iface)}"
		if is_wifi:
			cmd += f" ; wpa_cli -i {shlex.quote(iface)} signal_poll"
			self._last_wifi_update = now

		self._iface_buffer = ""
		try:
			self._container_iface.execute(cmd)
		except:
			# container execute failed — ignore
			pass

	def _onIfaceData(self, data):
		try:
			self._iface_buffer += data.decode("utf-8", "ignore")
		except:
			pass

	def _onIfaceFetched(self, retval):
		# keep previous internal ip to detect changes
		prev_internal = self._internal_ip

		lines = self._iface_buffer.splitlines()
		# Clear only those fields which will be re-parsed
		new_internal = ""
		new_has_ipv6 = "0"
		new_ip_type = "ipv4"
		new_wifi_rssi = None
		new_wifi_freq = None
		new_wifi_speed = None

		for line in lines:
			line = line.strip()
			if line.startswith("inet "):
				new_internal = line.split()[1].split("/")[0]
			if line.startswith("inet6") and "scope global" in line:
				new_has_ipv6 = "1"
				new_ip_type = "dual"
			if "=" in line:
				k,v = line.split("=",1)
				if k=="RSSI":
					try: new_wifi_rssi = int(v)
					except: pass
				if k=="FREQUENCY":
					try: new_wifi_freq = int(v)
					except: pass
				if k=="LINKSPEED":
					try: new_wifi_speed = int(v)
					except: pass

		# apply parsed results
		self._internal_ip = new_internal
		self._has_ipv6 = new_has_ipv6
		self._ip_type = new_ip_type
		if new_wifi_rssi is not None:
			self._wifi_rssi = new_wifi_rssi
		if new_wifi_freq is not None:
			self._wifi_freq = new_wifi_freq
		if new_wifi_speed is not None:
			self._wifi_speed = new_wifi_speed

		# update band/channel if freq present
		if self._wifi_freq:
			self._wifi_bandid = self._freq_to_band(self._wifi_freq)
			self._wifi_channel = self._freq_to_channel(self._wifi_freq)

		# update wifi percent/bars (reads /proc/net/wireless)
		self._update_wifi_percent()

		# If internal IP changed -> force external IP refresh or clear
		if prev_internal != self._internal_ip:
			# Log.w("[GlamourNetInfo] internal IP changed from %s to %s" % (prev_internal, self._internal_ip))
			if self._internal_ip:
				# acquired an IP — force external fetch by resetting timestamp
				self._external_ip_ts = 0
				self._fetch_external_ip()
			else:
				# lost IP — clear external immediately
				self._external_ip = ""
				self._external_ip_ts = 0

		Converter.changed(self, (self.CHANGED_POLL,))

	# WiFi helpers
	def _update_wifi_percent(self):
		try:
			with open("/proc/net/wireless") as f:
				lines = f.readlines()[2:]
				found = False
				for line in lines:
					parts = line.split()
					if parts:
						# use iface quality mapping if available; convert to percent roughly
						# If proc has multiple interfaces, last value overrides
						self._wifi_percent = max(0, min(100, int((float(parts[2]) + 100)*2)))
						self._wifi_bars = self._percent_to_bars(self._wifi_percent)
						found = True
				if not found:
					# leave previous percent if none found
					pass
		except:
			# on error, keep previous values
			pass

	def _percent_to_bars(self, p):
		if p <= 0: return 0
		if p <= 25: return 1
		if p <= 50: return 2
		if p <= 75: return 3
		return 4

	def _freq_to_band(self, freq):
		if 2400 <= freq <= 2500: return "24"
		if 4900 <= freq <= 5899: return "5"
		if 5925 <= freq <= 7125: return "6"
		return None

	def _freq_to_channel(self, freq):
		try:
			return int((freq - 5000)/5) if freq else None
		except:
			return None

	# Network update
	def _update_network_info(self):
		ifaces = os.listdir("/sys/class/net")
		eth_if = None
		wifi_if = None
		# Determine active interfaces
		for iface in ifaces:
			state = self._operstate(iface)
			if iface.startswith("eth") or iface.startswith("en"):
				if state=="up" and not eth_if:
					eth_if = iface
			elif iface.startswith("wlan") or iface.startswith("wl"):
				if state=="up" and not wifi_if:
					wifi_if = iface

		# Ethernet preferred
		status = (eth_if, wifi_if)
		if status != self._last_status:
			# status changed -> update cached state
			self._last_status = status
			if eth_if:
				self._net_type = "ethernet"
				self._net_status = "connected"
				self._eth_carrier = "1"
				self._eth_speed = self._get_eth_speed(eth_if)
				# refresh internal ip for that iface
				# call iface info container (async) to parse ipv4/6
				self._fetch_iface_info(eth_if, is_wifi=False)
				# ipv6 will be parsed in _onIfaceFetched
			elif wifi_if:
				self._net_type = "wifi"
				self._net_status = "connected"
				self._eth_carrier = "0"
				self._eth_speed = None
				# always fetch iface info (wifi) when status changes
				self._fetch_iface_info(wifi_if, is_wifi=True)
			else:
				self._net_type = "offline"
				self._net_status = "no_carrier"
				self._eth_carrier = "0"
				self._eth_speed = None
				self._internal_ip = ""
				self._has_ipv6 = "0"
				self._ip_type = "ipv4"
		else:
			# status unchanged: still, ensure we refresh iface info for wifi periodically
			if wifi_if:
				# this call is rate-limited inside by WIFI_REFRESH_INTERVAL
				self._fetch_iface_info(wifi_if, is_wifi=True)
			elif eth_if:
				# for ethernet, occasional refresh (no heavy cost)
				self._fetch_iface_info(eth_if, is_wifi=False)

		# External IP fetch (guarded by interval) — will be forced if internal IP changed by _onIfaceFetched
		if self._net_type != "offline":
			self._fetch_external_ip()

		Converter.changed(self, (self.CHANGED_POLL,))

	def _operstate(self, iface):
		try:
			with open(f"/sys/class/net/{iface}/operstate") as f:
				return f.read().strip()
		except:
			return "down"

	def _get_eth_speed(self, iface):
		try:
			with open(f"/sys/class/net/{iface}/speed") as f:
				return int(f.read().strip())
		except:
			return None

	def _get_ip_for_iface(self, iface):
		# kept for compatibility but not used in main flow
		try:
			out = os.popen(f"/sbin/ip -4 addr show dev {shlex.quote(iface)}").read()
			for line in out.splitlines():
				if line.strip().startswith("inet "):
					return line.split()[1].split("/")[0]
		except:
			pass
		return ""

	def _get_ipv6_for_iface(self, iface):
		# kept for compatibility but not used in main flow
		try:
			out = os.popen(f"/sbin/ip -6 addr show dev {shlex.quote(iface)}").read()
			for line in out.splitlines():
				line = line.strip()
				if line.startswith("inet6") and "scope global" in line:
					return line.split()[1].split("/")[0]
		except:
			pass
		return ""

	# Poll
	def poll(self):
		self._update_network_info()

	# Output
	@cached
	def getText(self):
		t = self.type
		if t == self.ICON:
			if self._net_type=="wifi": return "wifi_%d"%self._wifi_bars
			if self._net_type=="ethernet": return "ethernet"
			return "no_inet"
		if t == self.INTERNAL_IP: return self._internal_ip if self._internal_ip else "not connected"
		if t == self.EXTERNAL_IP: return self._external_ip if self._external_ip else "not connected"
		if t == self.NET_TYPE: return self._net_type
		if t == self.NET_STATUS: return self._net_status
		if t == self.WIFI_PERCENT: return str(self._wifi_percent)
		if t == self.WIFI_BARS: return str(self._wifi_bars)
		if t == self.WIFI_RSSI: return ("%s dBm"%self._wifi_rssi) if self._wifi_rssi else ""
		if t == self.WIFI_RSSI_VALUE: return str(self._wifi_rssi) if self._wifi_rssi else ""
		if t == self.WIFI_LINKSPEED: return ("%s Mbps"%self._wifi_speed) if self._wifi_speed else ""
		if t == self.WIFI_LINKSPEED_VALUE: return str(self._wifi_speed) if self._wifi_speed else ""
		if t == self.WIFI_FREQUENCY: return ("%s MHz"%self._wifi_freq) if self._wifi_freq else ""
		if t == self.WIFI_BAND: return self._wifi_bandid or ""
		if t == self.WIFI_BAND_ICON: return "wifi_band_%s"%self._wifi_bandid if self._wifi_bandid else ""
		if t == self.WIFI_CHANNEL: return str(self._wifi_channel) if self._wifi_channel else ""
		if t == self.ETH_SPEED: return ("%s Mbps"%self._eth_speed) if self._eth_speed else ""
		if t == self.ETH_SPEED_VALUE: return str(self._eth_speed) if self._eth_speed else ""
		if t == self.ETH_CARRIER: return self._eth_carrier
		if t == self.HAS_IPV6: return self._has_ipv6
		if t == self.IP_TYPE: return self._ip_type
		return ""

	text = property(getText)
