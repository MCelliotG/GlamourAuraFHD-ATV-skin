﻿# -*- coding: utf-8 -*-
# by digiteng...07.2021, 
# 08.2021(stb lang support),
# 09.2021 mini fixes
# © Provided that digiteng rights are protected, all or part of the code can be used, modified...
# russian and py3 support by sunriser...
# downloading in the background while zaping...
# by beber...03.2022,
# 03.2022 several enhancements : several renders with one queue thread, google search (incl. molotov for france) + autosearch & autoclean thread ...
# 02.2023 greek language and utf-8 compatibility enhancements by MCelliotG

from __future__ import absolute_import
from __future__ import print_function
from Components.Renderer.Renderer import Renderer
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Event import Event
from Components.Sources.EventInfo import EventInfo
from ServiceReference import ServiceReference
from Components.Sources.CurrentService import CurrentService
from enigma import ePixmap, eTimer, loadJPG, eEPGCache
from Components.Renderer.GlamPosterXDT import GlamPosterXDT
import NavigationInstance
import os
import sys
import re
import time
import socket
from Components.config import config
PY3 = (sys.version_info[0] == 3)
try:
	if PY3:
		import queue
		from _thread import start_new_thread
	else:
		import Queue
		from thread import start_new_thread
except:
	pass

epgcache = eEPGCache.getInstance()

try:
	from Components.config import config
	lng = config.osd.language.value
except:
	lng = None
	pass

apdb = dict()
#
# SET YOUR PREFERRED BOUQUET FOR AUTOMATIC POSTER GENERATION
# WITH THE NUMBER OF ITEMS EXPECTED (BLANK LINE IN BOUQUET CONSIDERED)
# IF NOT SET OR WRONG FILE THE AUTOMATIC POSTER GENERATION WILL WORK FOR
# THE CHANNELS THAT YOU ARE VIEWING IN THE ENIGMA SESSION
#
autobouquet_file = '/etc/enigma2/userbouquet.favourites.tv'
autobouquet_count = 32
# Short script for Automatic poster generation on your preferred bouquet
if not os.path.exists(autobouquet_file):
	autobouquet_file = None
	autobouquet_count = 0
else:
	with open(autobouquet_file, 'r') as f:
		lines = f.readlines()
	if autobouquet_count > len(lines):
		autobouquet_count = len(lines)
	for i in range(autobouquet_count):
		if '#SERVICE' in lines[i]:
			line = lines[i][9:].strip().split(':')
			if len(line) == 11:
				value = ':'.join((line[3], line[4], line[5], line[6]))
				if value != '0:0:0:0':
					service = ':'.join((line[0], line[1], line[2],line[3], line[4], line[5], line[6],line[7], line[8], line[9], line[10]))
					apdb[i] = service


path_folder = "/tmp/poster/"
if os.path.isdir("/media/hdd"):
	path_folder = "/media/hdd/poster/"
elif os.path.isdir("/media/usb"):
	path_folder = "/media/usb/poster/" 
elif os.path.isdir("/media/mmc"):
	path_folder = "/media/mmc/poster/"  
if not os.path.isdir(path_folder):
	os.makedirs(path_folder)

REGEX = re.compile(
		r'\s\*\d{4}\Z|' # remove ( *1234)
		r'([\(\[]).*?([\)\]])|'
		r'(\.\s{1,}\").+|' # remove (. "xxx)
		r'(\?\s{1,}\").+|' # remove (? "xxx)
		r'(\.{2,}\Z)|' # remove (..)
		r'\b(?=[MDCLXVIΙ])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})([IΙ]X|[IΙ]V|V?[IΙ]{0,3})\b\.?|' # remove roman numbers
		r'(: odc.\d+)|'
		r'(\d+: odc.\d+)|'
		r'(\d+ odc.\d+)|(:)|'
		r'( -(.*?).*)|(,)|'
		r'!|'
		r'/.*|'
		r'\|\s[0-9]+\+|'
		r'[0-9]+\+|'
		r'\s\d{4}\Z|'
		r'(\"|\"\.|\"\,|\.)\s.+|'
		r'\"|:|'
		r'Премьера\.\s|'
		r'(х|Х|м|М|т|Т|д|Д)/ф\s|'
		r'(х|Х|м|М|т|Т|д|Д)/с\s|'
		r'\s(с|С)(езон|ерия|-н|-я)\s.+|'
		r'\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\.\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\s(ч|ч\.|с\.|с)\s\d{1,3}.+|'
		r'\d{1,3}(-я|-й|\sс-н).+|', re.DOTALL)

def convtext(text):
	text = text.replace('\xc2\x86', '')
	text = text.replace('\xc2\x87', '')
	text = REGEX.sub('', text)
	text = re.sub(r"[-,!/\":]",' ',text)# replace (- or , or ! or / or " or :) by space
	text = re.sub(r'\s{1,}', ' ', text)# replace multiple space by one space
	text = text.strip()
	text = text.lower()
	return str(text)
	

if PY3:
	pdb = queue.LifoQueue()
else:
	pdb = Queue.LifoQueue()

class PosterDB(GlamPosterXDT):
	def __init__(self):
		GlamPosterXDT.__init__(self)
		self.logdbg = None

	def run(self):
		self.logDB("[QUEUE] : Initialized")
		while True:
			canal = pdb.get()
			self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0],canal[1],canal[2],canal[5]))
			dwn_poster = path_folder + canal[5] + ".jpg"
			if os.path.exists(dwn_poster):
				os.utime(dwn_poster, (time.time(), time.time()))
			if lng == "fr_FR":
				if not os.path.exists(dwn_poster):
					val, log = self.search_molotov_google(dwn_poster,canal[5],canal[4],canal[3],canal[0])
					self.logDB(log)
				if not os.path.exists(dwn_poster):
					val, log = self.search_programmetv_google(dwn_poster,canal[5],canal[4],canal[3],canal[0])
					self.logDB(log)
			if not os.path.exists(dwn_poster):
				val, log = self.search_imdb(dwn_poster,canal[5],canal[4],canal[3])
				self.logDB(log)
			if not os.path.exists(dwn_poster):
				val, log = self.search_tmdb(dwn_poster,canal[5],canal[4],canal[3])
				self.logDB(log)
			if not os.path.exists(dwn_poster):
				val, log = self.search_tvdb(dwn_poster,canal[5],canal[4],canal[3])
				self.logDB(log)
			if not os.path.exists(dwn_poster):
				val, log = self.search_google(dwn_poster,canal[5],canal[4],canal[3],canal[0])
				self.logDB(log)
			pdb.task_done()

	def logDB(self, logmsg):
		if self.logdbg:
			w = open(path_folder + "PosterDB.log", "a+")
			w.write("%s\n"%logmsg)
			w.close()

threadDB = PosterDB()
threadDB.start()

class PosterAutoDB(GlamPosterXDT):
	def __init__(self):
		GlamPosterXDT.__init__(self)
		self.logdbg = None

	def run(self):
		self.logAutoDB("[AutoDB] *** Initialized")
		while True:
			time.sleep(7200) # 7200 - Start every 2 hours
			self.logAutoDB("[AutoDB] *** Running ***")
			# AUTO ADD NEW FILES - 1440 (24 hours ahead)
			for service in apdb.values():
				try:
					events = epgcache.lookupEvent(['IBDCTESX', (service, 0, -1, 1440)])
					newfd = 0
					newcn = None
					for evt in events:
						canal = [None,None,None,None,None,None]
						canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
						if evt[1]==None or evt[4]==None or evt[5]==None or evt[6]==None:
							self.logAutoDB("[AutoDB] *** missing epg for {}".format(canal[0]))
						else:
							canal[1] = evt[1]
							canal[2] = evt[4]
							canal[3] = evt[5]
							canal[4] = evt[6]
							canal[5] = convtext(canal[2])
							#self.logAutoDB("[AutoDB] : {} : {}-{} ({})".format(canal[0],canal[1],canal[2],canal[5]))
							dwn_poster = path_folder + canal[5] + ".jpg"
							if os.path.exists(dwn_poster):
								os.utime(dwn_poster, (time.time(), time.time()))
							if lng == "fr_FR":
								if not os.path.exists(dwn_poster):
									val, log = self.search_molotov_google(dwn_poster,canal[5],canal[4],canal[3],canal[0])
									if val and log.find("SUCCESS"):
										newfd = newfd + 1
								if not os.path.exists(dwn_poster):
									val, log = self.search_programmetv_google(dwn_poster,canal[5],canal[4],canal[3],canal[0])
									if val and log.find("SUCCESS"):
										newfd = newfd + 1
							if not os.path.exists(dwn_poster):
								val, log = self.search_imdb(dwn_poster,canal[2],canal[4],canal[3],canal[0])
								if val and log.find("SUCCESS"):
									newfd = newfd + 1
							if not os.path.exists(dwn_poster):
								val, log = self.search_tmdb(dwn_poster,canal[2],canal[4],canal[3],canal[0])
								if val and log.find("SUCCESS"):
									newfd = newfd + 1
							if not os.path.exists(dwn_poster):
								val, log = self.search_tvdb(dwn_poster,canal[2],canal[4],canal[3],canal[0])
								if val and log.find("SUCCESS"):
									newfd = newfd + 1
							if not os.path.exists(dwn_poster):
								val, log = self.search_google(dwn_poster,canal[2],canal[4],canal[3],canal[0])
								if val and log.find("SUCCESS"):
									newfd = newfd + 1
						newcn = canal[0]
					self.logAutoDB("[AutoDB] {} new file(s) added ({})".format(newfd,newcn))
				except Exception as e:
					self.logAutoDB("[AutoDB] *** service error : {} ({})".format(service,e))
			# AUTO REMOVE OLD FILES
			now_tm = time.time()
			emptyfd = 0
			oldfd = 0
			for f in os.listdir(path_folder):
				diff_tm = now_tm - os.path.getmtime(path_folder+f)
				if diff_tm > 120 and os.path.getsize(path_folder+f) == 0: # Detect empty files > 2 minutes
					os.remove(path_folder+f)
					emptyfd = emptyfd + 1
				if diff_tm > 259200: # Detect old files > 3 days old
					os.remove(path_folder+f)
					oldfd = oldfd + 1
			self.logAutoDB("[AutoDB] {} old file(s) removed".format(oldfd))
			self.logAutoDB("[AutoDB] {} empty file(s) removed".format(emptyfd))
			self.logAutoDB("[AutoDB] *** Stopping ***")

	def logAutoDB(self, logmsg):
		if self.logdbg:
			w = open(path_folder + "PosterAutoDB.log", "a+")
			w.write("%s\n"%logmsg)
			w.close()

threadAutoDB = PosterAutoDB()
threadAutoDB.start()

class GlamPosterX(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.nxts = 0
		self.canal = [None,None,None,None,None,None]
		self.oldCanal = None
		self.intCheck()
		self.timer = eTimer()
		self.timer.callback.append(self.showPoster)
		self.logdbg = None

	def applySkin(self, desktop, parent):
		attribs = []
		for (attrib, value,) in self.skinAttributes:
			if attrib == "nexts":
				self.nxts = int(value)
			attribs.append((attrib, value))
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	def intCheck(self):
		try:
			socket.setdefaulttimeout(1)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
			return True
		except:
			return

	GUI_WIDGET = ePixmap
	def changed(self, what):
		if not self.instance:
			return
		if what[0] == self.CHANGED_CLEAR:
			self.instance.hide()
		if what[0] != self.CHANGED_CLEAR:
			servicetype = None
			try:
				service = None
				if isinstance(self.source, ServiceEvent): # source="ServiceEvent"
					service = self.source.getCurrentService()
					servicetype = "ServiceEvent"
				elif isinstance(self.source, CurrentService): # source="session.CurrentService"
					service = self.source.getCurrentServiceRef()
					servicetype = "CurrentService"
				elif isinstance(self.source, EventInfo): # source="session.Event_Now" or source="session.Event_Next"
					service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
					servicetype = "EventInfo"
				elif isinstance(self.source, Event): # source="Event"
					if self.nxts:
						service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
					else:
						self.canal[0] = None
						self.canal[1] = self.source.event.getBeginTime()
						self.canal[2] = self.source.event.getEventName()
						self.canal[3] = self.source.event.getExtendedDescription()
						self.canal[4] = self.source.event.getShortDescription()
						self.canal[5] = convtext(self.canal[2])
					servicetype = "Event"
				if service:
					events = epgcache.lookupEvent(['IBDCTESX', (service.toString(), 0, -1, -1)])
					self.canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
					self.canal[1] = events[self.nxts][1]
					self.canal[2] = events[self.nxts][4]
					self.canal[3] = events[self.nxts][5]
					self.canal[4] = events[self.nxts][6]
					self.canal[5] = convtext(self.canal[2])
					if not autobouquet_file:
						if not apdb.has_key(self.canal[0]):
							apdb[self.canal[0]] = service.toString()
			except Exception as e:
				self.logPoster("Error (service) : "+str(e))
				self.instance.hide()
				return
			if not servicetype:
				self.logPoster("Error service type undefined")
				self.instance.hide()
				return
			try:
				curCanal = "{}-{}".format(self.canal[1],self.canal[2])
				if curCanal == self.oldCanal:
					return
				self.oldCanal = curCanal
				self.logPoster("Service : {} [{}] : {} : {}".format(servicetype,self.nxts,self.canal[0],self.oldCanal))
				pstrNm = path_folder + self.canal[5] + ".jpg"
				if os.path.exists(pstrNm):
					self.timer.start(100, True)
				else:
					canal = self.canal[:]
					pdb.put(canal)
					start_new_thread(self.waitPoster, ())
			except Exception as e:
				self.logPoster("Error (eFile) : "+str(e))
				self.instance.hide()
				return


	def showPoster(self):
		self.instance.hide()
		if self.canal[5]:
			pstrNm = path_folder + self.canal[5] + ".jpg"
			if os.path.exists(pstrNm):
				self.logPoster("[LOAD : showPoster] {}".format(pstrNm))
				self.instance.setPixmap(loadJPG(pstrNm))
				self.instance.setScale(2)
				self.instance.show()

	def waitPoster(self):
		self.instance.hide()
		if self.canal[5]:
			pstrNm = path_folder + self.canal[5] + ".jpg"
			loop = 300
			found = None
			self.logPoster("[LOOP : waitPoster] {}".format(pstrNm))
			while loop>=0:
				if os.path.exists(pstrNm):
					if os.path.getsize(pstrNm) > 0:
						loop = 0
						found = True
				time.sleep(0.6)
				loop = loop - 1
			if found:
				self.timer.start(10, True)

	def logPoster(self, logmsg):
		if self.logdbg:
			w = open(path_folder + "GlamPosterX.log", "a+")
			w.write("%s\n"%logmsg)
			w.close() 