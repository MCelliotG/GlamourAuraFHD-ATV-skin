# GlamourNetInfo converter (python 3)
# Fully coded by MCelliotG, optimized and enhanced for Enigma2 performance
# If you use this converter for other skins and rename it, please keep the lines above adding your credits below

import os
import time
import socket
import struct
import fcntl
from json import loads

from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from enigma import eConsoleAppContainer

SIOCGIFADDR = 0x8915


class GlamourNetInfo(Poll, Converter):

	# Time intervals (seconds)
	EXTERNAL_IP_INTERVAL = 60
	WPACLI_INTERVAL = 8
	WG_INTERVAL = 5

	IFACES_CACHE_TTL = 20
	WIRELESS_CACHE_TTL = 3
	INET6_CACHE_TTL = 3

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)

		self.raw_type = type.strip()

		# Parse fields
		self._fields, self._sep = self._parse_fields_and_sep(self.raw_type)

		# Internal network state
		self._net_type = "offline"          # "wifi", "ethernet", "offline"
		self._net_status = "not connected"  # "connected", "not connected", "connecting"
		self._internal_ip = ""
		self._last_internal_ip = ""
		self._external_ip = ""
		self._external_ip_ts = 0

		self._ip_type = "ipv4"
		self._has_ipv6 = "0"

		self._eth_speed = None
		self._eth_carrier = "0"

		# WiFi
		self._wifi_percent = 0
		self._wifi_bars = 0
		self._wifi_rssi = None
		self._wifi_freq = None
		self._wifi_speed = None
		self._wifi_channel = None
		self._wifi_bandid = None

		# ISP / Country
		self._isp_name = ""
		self._isp_cc = ""

		# Async containers
		self._extip_buf = ""
		self._extip_running = False
		self._container_extip = eConsoleAppContainer()
		self._container_extip.dataAvail.append(self._onExtIpData)
		self._container_extip.appClosed.append(self._onExtIpClosed)

		self._wpa_buf = ""
		self._wpa_running = False
		self._wpa_last_ts = 0
		self._container_wpa = eConsoleAppContainer()
		self._container_wpa.dataAvail.append(self._onWpaData)
		self._container_wpa.appClosed.append(self._onWpaClosed)

		self._wg_buf = ""
		self._wg_running = False
		self._wg_last_ts = 0
		self._wg_endpoint = ""
		self._container_wg = eConsoleAppContainer()
		self._container_wg.dataAvail.append(self._onWgData)
		self._container_wg.appClosed.append(self._onWgClosed)

		# Caches
		self._ifaces_cache = []
		self._ifaces_cache_ts = 0

		self._wireless_cache = {}
		self._wireless_cache_ts = 0

		self._inet6_cache = {}
		self._inet6_cache_ts = 0

		# Output cache
		self._cache_key = None
		self._cache_value = ""

		# Whether we need WAN/ISP state:
		# ICON επίσης απαιτεί WAN λογική για ethernet_con / no_ethernet / no_wifi / no_inet
		self._need_external = any(
			k in ("EXTERNALIP", "ISPNAME", "ISPCOUNTRY", "COUNTRY", "ICON")
			for k in self._fields
		)

		# Field mapping
		self._mapping = self._build_mapping()

		# Base poll; adaptive logic applied inside _update_network()
		self.poll_interval = 1500
		self.poll_enabled = True

	# ---------------------------------------------------------
	# Field parsing
	# ---------------------------------------------------------

	def _parse_fields_and_sep(self, raw):
		fields_part = raw
		sep = ", "

		if ";" in raw:
			fields_part, opts = raw.split(";", 1)
			fields_part = fields_part.strip()
			opts = opts.strip().lower()

			idx = opts.find("sep=")
			if idx != -1:
				s = opts[idx + 4:].lstrip()
				if s:
					if s[0] in ("'", '"'):
						q = s[0]
						end = s.find(q, 1)
						if end != -1:
							sep = s[1:end]
					else:
						end = s.find(" ")
						sep = s if end == -1 else s[:end]

		fields = [f.strip().upper() for f in fields_part.split(",") if f.strip()]
		if not fields:
			fields = ["INTERNALIP"]

		return fields, sep

	# ---------------------------------------------------------
	# Helper: reset WAN state
	# ---------------------------------------------------------

	def _reset_external(self):
		self._external_ip = ""
		self._external_ip_ts = 0
		self._isp_name = ""
		self._isp_cc = ""
		self._extip_running = False
		try:
			self._container_extip.kill()
		except:
			pass

	# ---------------------------------------------------------
	# Network values
	# ---------------------------------------------------------

	def _list_interfaces(self):
		now = time.time()
		if now - self._ifaces_cache_ts < self.IFACES_CACHE_TTL and self._ifaces_cache:
			return self._ifaces_cache

		try:
			ifaces = os.listdir("/sys/class/net")
		except:
			ifaces = []

		self._ifaces_cache = ifaces
		self._ifaces_cache_ts = now
		return ifaces

	def _operstate(self, iface):
		try:
			with open(f"/sys/class/net/{iface}/operstate") as f:
				return f.read().strip()
		except:
			return "down"

	def _has_carrier(self, iface):
		return self._operstate(iface) == "up"

	def _get_ipv4(self, iface):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			req = struct.pack('256s', iface[:15].encode())
			res = fcntl.ioctl(s.fileno(), SIOCGIFADDR, req)
			return socket.inet_ntoa(res[20:24])
		except:
			return ""

	# IPv6
	def _refresh_inet6_cache(self):
		now = time.time()
		if now - self._inet6_cache_ts < self.INET6_CACHE_TTL and self._inet6_cache:
			return

		cache = {}
		try:
			with open("/proc/net/if_inet6") as f:
				for ln in f:
					parts = ln.split()
					if len(parts) >= 6:
						raw = parts[0]
						iface = parts[5]
						hexes = [raw[i:i + 4] for i in range(0, 32, 4)]
						cache[iface] = ":".join(hexes)
		except:
			cache = {}

		self._inet6_cache = cache
		self._inet6_cache_ts = now

	def _get_ipv6(self, iface):
		self._refresh_inet6_cache()
		return self._inet6_cache.get(iface, "")

	# Ethernet speed
	def _get_eth_speed(self, iface):
		try:
			with open(f"/sys/class/net/{iface}/speed") as f:
				return int(f.read())
		except:
			return None

	# ---------------------------------------------------------
	# Wireless / WPA
	# ---------------------------------------------------------

	def _read_wireless(self):
		"""
		Ελαφρύ /proc/net/wireless reader.
		Εκτελείται μόνο όταν ΔΕΝ έχουμε ήδη RSSI από wpa_cli.
		"""
		if self._wifi_rssi is not None:
			# RSSI ήδη γνωστό → δεν χρειάζεται scan
			return self._wireless_cache

		now = time.time()
		if now - self._wireless_cache_ts < self.WIRELESS_CACHE_TTL and self._wireless_cache:
			return self._wireless_cache

		res = {}
		try:
			with open("/proc/net/wireless") as f:
				lines = f.readlines()[2:]
				for ln in lines:
					p = ln.split()
					if not p:
						continue
					iface = p[0].strip(":")
					try:
						q = float(p[2].strip("."))
					except:
						q = 0.0
					res[iface] = q
		except:
			res = {}

		self._wireless_cache = res
		self._wireless_cache_ts = now
		return res

	def _map_quality(self, q):
		try:
			return int(max(0, min(100, (q / 70.0) * 100)))
		except:
			return 0

	def _rssi_to_percent(self, r):
		try:
			return int(max(0, min(100, (r + 100) * 2)))
		except:
			return 0

	def _bars(self, p):
		if p <= 0: return 0
		if p <= 25: return 1
		if p <= 50: return 2
		if p <= 75: return 3
		return 4

	def _freq_band(self, f):
		if f is None: return None
		if 2400 <= f <= 2500: return "24"
		if 4900 <= f <= 5899: return "5"
		if 5925 <= f <= 7125: return "6"
		return None

	def _freq_channel(self, f):
		if f is None: return None
		try:
			if f >= 5000:
				return int((f - 5000) / 5)
			if 2400 <= f <= 2500:
				return int((f - 2407) / 5)
		except:
			return None
		return None

	# WPA CLI async
	def _start_wpa(self, iface):
		if self._wpa_running:
			return
		now = time.time()
		if now - self._wpa_last_ts < self.WPACLI_INTERVAL:
			return

		self._wpa_running = True
		self._wpa_last_ts = now
		self._wpa_buf = ""

		try:
			self._container_wpa.execute(f"wpa_cli -i {iface} signal_poll")
		except:
			self._wpa_running = False

	def _onWpaData(self, data):
		try:
			self._wpa_buf += data.decode("utf-8", "ignore")
		except:
			pass

	def _onWpaClosed(self, retval):
		self._wpa_running = False
		buf = self._wpa_buf.strip()
		self._wpa_buf = ""
		if not buf:
			return

		rssi = None
		freq = None
		speed = None

		for ln in buf.splitlines():
			ln = ln.strip()
			if not ln:
				continue
			up = ln.upper()
			if up.startswith("RSSI="):
				try:
					rssi = int(ln.split("=", 1)[1])
				except:
					pass
			elif up.startswith("FREQUENCY="):
				try:
					freq = int(ln.split("=", 1)[1])
				except:
					pass
			elif up.startswith("LINKSPEED="):
				try:
					speed = int(ln.split("=", 1)[1])
				except:
					pass

		if rssi is not None:
			self._wifi_rssi = rssi
		if freq is not None:
			self._wifi_freq = freq
			self._wifi_bandid = self._freq_band(freq)
			self._wifi_channel = self._freq_channel(freq)
		if speed is not None:
			self._wifi_speed = speed

		Converter.changed(self, (self.CHANGED_POLL,))

	# ---------------------------------------------------------
	# External IP + ISP (single ip-api.com call)
	# ---------------------------------------------------------

	def _fetch_external_ip(self, force=False):
		if not self._need_external:
			return

		if not self._internal_ip or self._net_type == "offline":
			return

		now = time.time()

		if not force and self._external_ip_ts and (now - self._external_ip_ts) < self.EXTERNAL_IP_INTERVAL:
			return

		if self._extip_running:
			return

		self._extip_running = True
		self._extip_buf = ""

		cmd = 'wget -qO- "http://ip-api.com/json/?fields=status,message,country,countryCode,query,isp" || echo'
		try:
			self._container_extip.execute(cmd)
		except:
			self._extip_running = False

	def _onExtIpData(self, data):
		try:
			self._extip_buf += data.decode("utf-8", "ignore")
		except:
			pass

	def _onExtIpClosed(self, retval):
		self._extip_running = False

		self._external_ip_ts = time.time()
		out = self._extip_buf.strip()
		self._extip_buf = ""

		def mark_no_internet():
			self._external_ip = ""
			self._isp_name = ""
			self._isp_cc = ""
			if self._internal_ip:
				self._net_status = "not connected"
			else:
				self._net_status = "not connected"

		if not out:
			mark_no_internet()
			Converter.changed(self, (self.CHANGED_POLL,))
			return

		try:
			data = loads(out)
		except:
			mark_no_internet()
			Converter.changed(self, (self.CHANGED_POLL,))
			return

		if not isinstance(data, dict) or data.get("status") != "success":
			mark_no_internet()
			Converter.changed(self, (self.CHANGED_POLL,))
			return

		# Επιτυχία
		self._external_ip = data.get("query", "") or ""
		raw_isp = data.get("isp") or ""
		self._isp_name = raw_isp.replace("\\", "")

		cc = data.get("countryCode") or data.get("country") or ""
		self._isp_cc = cc

		if self._internal_ip:
			self._net_status = "connected"
		else:
			self._net_status = "not connected"

		Converter.changed(self, (self.CHANGED_POLL,))

	# ---------------------------------------------------------
	# WireGuard
	# ---------------------------------------------------------

	def _start_wg(self):
		if self._wg_running:
			return
		now = time.time()
		if now - self._wg_last_ts < self.WG_INTERVAL:
			return

		self._wg_running = True
		self._wg_last_ts = now
		self._wg_buf = ""

		try:
			self._container_wg.execute("wg show wg0 endpoints")
		except:
			self._wg_running = False

	def _onWgData(self, data):
		try:
			self._wg_buf += data.decode("utf-8", "ignore")
		except:
			pass

	def _onWgClosed(self, retval):
		self._wg_running = False
		out = self._wg_buf.strip()
		self._wg_buf = ""

		endpoint = ""
		if out:
			ln = out.splitlines()[0].strip()
			parts = ln.split()
			if len(parts) >= 2:
				endpoint = parts[1]

		if endpoint != self._wg_endpoint:
			self._wg_endpoint = endpoint
			# Αλλάζει endpoint → θεωρούμε ότι αλλάζει και public IP
			self._reset_external()
			self._fetch_external_ip(force=True)
			Converter.changed(self, (self.CHANGED_POLL,))

	# ---------------------------------------------------------
	# Poll
	# ---------------------------------------------------------

	def poll(self):
		try:
			self._start_wg()
		except:
			pass

		self._update_network()

	def _update_network(self):
		ifaces = self._list_interfaces()

		wifi = None
		eth = None

		for iface in ifaces:
			if iface == "lo":
				continue
			is_wifi = iface.startswith("wlan") or iface.startswith("wl")
			is_eth = iface.startswith("eth") or iface.startswith("en")

			if not (is_wifi or is_eth):
				continue

			if not self._has_carrier(iface):
				continue

			if is_wifi and wifi is None:
				wifi = iface
			elif is_eth and eth is None:
				eth = iface

			if wifi and eth:
				break

		self._last_internal_ip = self._internal_ip
		self._internal_ip = ""
		self._has_ipv6 = "0"
		self._ip_type = "ipv4"
		self._eth_carrier = "0"
		self._eth_speed = None

		self._wifi_percent = 0
		self._wifi_bars = 0

		# Προεπιλογή: τίποτα συνδεδεμένο
		self._net_type = "offline"
		self._net_status = "not connected"

		# -----------------------------
		# WiFi
		# -----------------------------
		if wifi:
			self._net_type = "wifi"
			ipv4 = self._get_ipv4(wifi)
			ipv6 = self._get_ipv6(wifi)

			if ipv4 or ipv6:
				self._internal_ip = ipv4
				if ipv6:
					self._has_ipv6 = "1"
					self._ip_type = "dual"

				# Αν άλλαξε η LAN IP καθαρίζουμε full WAN state
				if self._internal_ip != self._last_internal_ip:
					self._reset_external()

				# Έχουμε IP → LAN OK
				if self._need_external:
					if self._external_ip:
						self._net_status = "connected"
					elif self._extip_running or not self._external_ip_ts:
						self._net_status = "connecting"
					else:
						self._net_status = "not connected"
				else:
					self._net_status = "connected"

				qmap = self._read_wireless()
				q = qmap.get(wifi, 0)
				if q > 0:
					self._wifi_percent = self._map_quality(q)
				else:
					if self._wifi_rssi is not None:
						self._wifi_percent = self._rssi_to_percent(self._wifi_rssi)
					else:
						self._wifi_percent = 0
						self._start_wpa(wifi)

				self._wifi_bars = self._bars(self._wifi_percent)
			else:
				# carrier αλλά χωρίς IP
				self._internal_ip = ""
				self._reset_external()
				self._net_status = "not connected"

			# Adaptive poll for wifi
			self.poll_interval = 1500

		# -----------------------------
		# Ethernet
		# -----------------------------
		elif eth:
			self._net_type = "ethernet"
			ipv4 = self._get_ipv4(eth)
			ipv6 = self._get_ipv6(eth)

			if ipv4 or ipv6:
				self._internal_ip = ipv4
				if ipv6:
					self._has_ipv6 = "1"
					self._ip_type = "dual"

				self._eth_carrier = "1"
				self._eth_speed = self._get_eth_speed(eth)

				# Αν άλλαξε η LAN IP καθαρίζουμε full WAN state
				if self._internal_ip != self._last_internal_ip:
					self._reset_external()

				if self._need_external:
					if self._external_ip:
						self._net_status = "connected"
					elif self._extip_running or not self._external_ip_ts:
						self._net_status = "connecting"
					else:
						self._net_status = "not connected"
				else:
					self._net_status = "connected"
			else:
				# carrier αλλά χωρίς IP
				self._internal_ip = ""
				self._reset_external()
				self._eth_carrier = "1"
				self._net_status = "not connected"

			# Adaptive poll for ethernet
			self.poll_interval = 4000

		else:
			# Καθόλου carrier → πλήρες offline
			self._net_type = "offline"
			self._net_status = "not connected"
			self._internal_ip = ""
			self._reset_external()
			self.poll_interval = 5000

		# External IP logic:
		if self._net_type != "offline" and self._internal_ip and self._need_external:
			now = time.time()
			# Αν δεν έχουμε ξαναδοκιμάσει ή έχει λήξει το TTL → κάνε fetch
			if (not self._external_ip_ts) or ((now - self._external_ip_ts) >= self.EXTERNAL_IP_INTERVAL):
				force = not self._external_ip_ts
				self._fetch_external_ip(force=force)
		else:
			if self._net_type == "offline":
				self._net_status = "not connected"
			if not self._need_external:
				pass
			else:
				self._reset_external()

		Converter.changed(self, (self.CHANGED_POLL,))

	# ---------------------------------------------------------
	# Field mapping & helpers
	# ---------------------------------------------------------

	def _icon_for_state(self):
		# Χωρίς internal IP → no_inet
		if not self._internal_ip:
			return "no_inet"

		# Ethernet προτεραιότητα
		if self._net_type == "ethernet":
			if self._net_status == "connected":
				return "ethernet"
			elif self._net_status == "connecting":
				return "ethernet_con"
			else:
				return "no_ethernet"

		# WiFi
		if self._net_type == "wifi":
			if self._net_status == "connected":
				return f"wifi_{self._wifi_bars}"
			elif self._net_status == "connecting":
				return "wifi_con"
			else:
				return "no_wifi"

		return "no_inet"

	def _value_internal_ip(self):
		if self._internal_ip:
			return self._internal_ip
		return "not connected"

	def _value_external_ip(self):
		if not self._need_external:
			return ""
		if self._external_ip:
			return self._external_ip
		if self._net_status == "connecting":
			return "connecting..."
		return "not connected"

	def _value_ispname(self):
		if not self._need_external:
			return ""
		if self._isp_name:
			return self._isp_name
		if self._net_status == "connecting":
			return "connecting..."
		return "not connected"

	def _build_mapping(self):
		return {
			"ICON":       lambda s: s._icon_for_state(),
			"INTERNALIP": lambda s: s._value_internal_ip(),
			"EXTERNALIP": lambda s: s._value_external_ip(),
			"NETTYPE":    lambda s: s._net_type,
			"NETSTATUS":  lambda s: s._net_status,

			"WIFIPERCENT":      lambda s: str(s._wifi_percent),
			"WIFIBARS":         lambda s: str(s._wifi_bars),
			"WIFIRSSI":         lambda s: f"{s._wifi_rssi} dBm" if s._wifi_rssi is not None else "",
			"WIFIRSSIVALUE":    lambda s: str(s._wifi_rssi) if s._wifi_rssi is not None else "",
			"WIFILINKSPEED":    lambda s: f"{s._wifi_speed} Mbps" if s._wifi_speed else "",
			"WIFILINKSPEEDVALUE": lambda s: str(s._wifi_speed) if s._wifi_speed else "",
			"WIFIFREQUENCY":    lambda s: f"{s._wifi_freq} MHz" if s._wifi_freq else "",
			"WIFIBAND":         lambda s: s._wifi_bandid or "",
			"WIFIBANDICON":     lambda s: f"wifi_band_{s._wifi_bandid}" if s._wifi_bandid else "",
			"WIFICHANNEL":      lambda s: str(s._wifi_channel) if s._wifi_channel else "",

			"ETHSPEED":      lambda s: f"{s._eth_speed} Mbps" if s._eth_speed else "",
			"ETHSPEEDVALUE": lambda s: str(s._eth_speed) if s._eth_speed else "",
			"ETHCARRIER":    lambda s: s._eth_carrier,

			"IPTYPE":   lambda s: s._ip_type,
			"HASIPV6":  lambda s: s._has_ipv6,

			"ISPNAME":     lambda s: s._value_ispname(),
			"ISPCOUNTRY":  lambda s: s._isp_cc,
			"COUNTRY":     lambda s: s._isp_cc,
		}

	def _value_for_key(self, key):
		f = self._mapping.get(key)
		if not f:
			return ""
		try:
			return f(self) or ""
		except:
			return ""

	# ---------------------------------------------------------
	# Output
	# ---------------------------------------------------------

	def _cache_tuple(self):
		return (
			tuple(self._fields),
			self._sep,
			self._internal_ip,
			self._external_ip,
			self._net_type,
			self._net_status,
			self._wifi_percent,
			self._wifi_bars,
			self._wifi_rssi,
			self._wifi_speed,
			self._wifi_freq,
			self._wifi_channel,
			self._eth_speed,
			self._eth_carrier,
			self._ip_type,
			self._has_ipv6,
			self._isp_name,
			self._isp_cc,
		)

	def getText(self):
		key = self._cache_tuple()
		if key == self._cache_key:
			return self._cache_value

		out = []
		for k in self._fields:
			val = self._value_for_key(k)
			if val:
				out.append(val)

		res = self._sep.join(out)

		self._cache_key = key
		self._cache_value = res
		return res

	text = property(getText)

	def changed(self, what):
		if what[0] == self.CHANGED_POLL:
			self.downstream_elements.changed(what)
