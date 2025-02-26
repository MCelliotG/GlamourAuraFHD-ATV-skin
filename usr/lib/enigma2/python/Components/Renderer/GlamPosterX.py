# -*- coding: utf-8 -*-
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
import NavigationInstance
import os
import sys
import re
import time
import socket
import requests
import threading
from PIL import Image
try:
	from urllib.parse import quote
except ImportError:
	from urllib import quote
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


tmdb_api = "3c3efcf47c3577558812bb9d64019d65"
tvdb_api = "a99d487bb3426e5f3a60dea6d3d3c7ef"

isz="300,450"

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


class PosterDB(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.logdbg = None
		self.checkMovie = ["film", "movie", "фильм", "кино", "ταινία", "película", "cinéma", "cine", "cinema", "filma", "φιλμ", "σινεμά", "adventure", "περιπέτεια", "κινηματογράφος", "comedy", "κωμωδία" ]
		self.checkTV = [ "serial", "series", "serie", "serien", "série", "séries", "serious", "σειρά",
			"folge", "episodio", "episode", "épisode", "l'épisode", "επεισόδιο", "σεζόν", "ep.", "animation",
			"staffel", "soap", "doku", "tv", "talk", "show", "news", "factual", "entertainment", "telenovela", 
			"dokumentation", "dokutainment", "documentary", "ντοκιμαντέρ", "informercial", "information", "sitcom", "reality", 
			"program", "magazine", "ειδήσεις", "mittagsmagazin", "т/с", "м/с", "сезон", "с-н", "эпизод", "сериал", "серия",
			"εκπομπή", "actualité", "discussion", "interview", "débat", "émission", "divertissement", "jeu", "τηλεπαιχνίδι", "magasine",
			"information", "météo", "καιρός", "journal", "sport", "αθλητικά", "culture", "infos", "feuilleton", "téléréalité",
			"société", "clips", "concert", "santé", "éducation", "variété" ]

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

	def search_tmdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
		try:
			year = None
			url_tmdb = ""
			poster = None
			chkType, fd = self.checkType(shortdesc,fulldesc)
			if chkType=="":
				srch="multi"
			elif chkType.startswith("movie"):
				srch="movie"
			else:
				srch="tv"
			try:
				if re.findall('19\d{2}|20\d{2}', title):
					year = re.findall('19\d{2}|20\d{2}', fd)[1]
				else:
					year = re.findall('19\d{2}|20\d{2}', fd)[0]
			except:
				year = ""
				pass
			url_tmdb = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(srch, tmdb_api, quote(title))
			if year:
				url_tmdb += "&year={}".format(year)
			if lng:
				url_tmdb += "&language={}".format(lng[:-3])
			poster = requests.get(url_tmdb).json()
			if poster and poster['results'] and poster['results'][0] and poster['results'][0]['poster_path']:
				url_poster = "https://image.tmdb.org/t/p/w{}{}".format(str(isz.split(",")[0]), poster['results'][0]['poster_path'])
				self.savePoster(dwn_poster, url_poster)
				return True, "[SUCCESS : tmdb] {} [{}-{}] => {} => {}".format(title,chkType,year,url_tmdb,url_poster)
			else:
				return False, "[SKIP : tmdb] {} [{}-{}] => {} (Not found)".format(title,chkType,year,url_tmdb)
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : tmdb] {} [{}-{}] => {} ({})".format(title,chkType,year,url_tmdb,str(e))


	def search_programmetv_google(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
		try:
			url_ptv = ""
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			chkType, fd = self.checkType(shortdesc,fulldesc)
			if chkType.startswith("movie"):
				return False, "[SKIP : programmetv-google] {} [{}] => Skip movie title".format(title,chkType)
			year = None
			year = re.findall('19\d{2}|20\d{2}', fd)
			if len(year)>0:
				year = year[0]
			else:
				year = None
			url_ptv = "site:programme-tv.net+"+quote(title)
			if channel and title.find(channel.split()[0])<0:
				url_ptv += "+"+quote(channel)
			if year:
				url_ptv += "+{}".format(year)
			url_ptv = "https://www.google.com/search?q={}&tbm=isch&tbs=ift:jpg%2Cisz:m".format(url_ptv)
			ff = requests.get(url_ptv, stream=True, headers=headers).text
			if not PY3:
				ff = ff.encode('utf-8')
			posterlst = re.findall('\],\["https://(.*?)",\d+,\d+]', ff)
			if posterlst and posterlst[0]:
				url_poster = "https://{}".format(posterlst[0])
				url_poster = re.sub(r"\\u003d", "=", url_poster)
				url_poster_size = re.findall('/(\d+)x(\d+)/',url_poster)
				if url_poster_size and url_poster_size[0]:
					h_ori = float(url_poster_size[0][1])
					h_tar = float(re.findall('(\d+)',isz)[1])
					ratio = h_ori/h_tar
					w_ori = float(url_poster_size[0][0])
					w_tar = w_ori/ratio
					w_tar = int(w_tar)
					h_tar = int(h_tar)
					url_poster = re.sub('/\d+x\d+/',"/"+str(w_tar)+"x"+str(h_tar)+"/",url_poster)
				url_poster = re.sub('crop-from/top/','',url_poster)
				self.savePoster(dwn_poster, url_poster)
				if self.verifyPoster(dwn_poster) and url_poster_size:
					return True, "[SUCCESS : programmetv-google] {} [{}] => {} => {} (initial size: {})".format(title,chkType,url_ptv,url_poster,url_poster_size)
				else:
					if os.path.exists(dwn_poster):
						os.remove(dwn_poster)
					return False, "[SKIP : programmetv-google] {} [{}] => {} => {} (initial size: {}) (jpeg error)".format(title,chkType,url_ptv,url_poster,url_poster_size)
			else:
				return False, "[SKIP : programmetv-google] {} [{}] => {} (Not found)".format(title,chkType,url_ptv)
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : programmetv-google] {} [{}] => {} ({})".format(title,chkType,url_ptv,str(e))
			

	def search_molotov_google(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
		try:
			url_mgoo = ''
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			chkType, fd = self.checkType(shortdesc,fulldesc)
				
			ptitle = self.UNAC(title)
			if channel:
				pchannel = self.UNAC(channel).replace(" ","")
			else:
				pchannel = ""
			poster = None
			pltc=None
			imsg = ""
			url_mgoo = "site:molotov.tv+"+quote(title)
			if channel and title.find(channel.split()[0])<0:
				url_mgoo += "+"+quote(channel)
			url_mgoo = "https://www.google.com/search?q={}&tbm=isch".format(url_mgoo)
			ff = requests.get(url_mgoo, stream=True, headers=headers).text
			if not PY3:
				ff = ff.encode('utf-8')
			plst = re.findall('https://www.molotov.tv/(.*?)"(?:.*?)?"(.*?)"', ff)
			len_plst = len(plst)
			molotov_id=0
			molotov_table=[0,0,None,None,0]
			molotov_final=False
			partialtitle=0
			partialchannel=100
			for pl in plst:
				get_path = "https://www.molotov.tv/"+pl[0]
				get_name = self.UNAC(pl[1])
				get_title = re.findall('(.*?)[ ]+en[ ]+streaming',get_name)
				if get_title:
					get_title = get_title[0]
				else:
					get_title = None
				get_channel = re.findall('(?:streaming|replay)?[ ]+sur[ ]+(.*?)[ ]+molotov.tv',get_name)
				if get_channel:
					get_channel = self.UNAC(get_channel[0]).replace(" ","")
				else:
					get_channel = re.findall('regarder[ ]+(.*?)[ ]+en',get_name)
					if get_channel:
						get_channel = self.UNAC(get_channel[0]).replace(" ","")
					else:
						get_channel = None
				if get_channel and pchannel and get_channel==pchannel:
					partialchannel=100
				else:
					partialchannel = self.PMATCH(pchannel,get_channel)
				partialtitle=0
				if get_title and ptitle and get_title==ptitle:
					partialtitle=100
				else:
					partialtitle = self.PMATCH(ptitle,get_title)
				if partialtitle > molotov_table[0]:
					molotov_table = [partialtitle, partialchannel, get_name, get_path,molotov_id]
				if partialtitle == 100 and partialchannel == 100:
					molotov_final=True
					break
				molotov_id+=1
			if molotov_table[0]:
				ffm = requests.get(molotov_table[3], stream=True, headers=headers).text
				if not PY3:
					ffm = ffm.encode('utf-8')
				pltt = re.findall('"https://fusion.molotov.tv/(.*?)/jpg" alt="(.*?)"', ffm)
				if len(pltt)>0:
					pltc = self.UNAC(pltt[0][1])
					plst = "https://fusion.molotov.tv/"+pltt[0][0]+"/jpg"
					imsg="Found title ({}%) & channel ({}%) : '{}' + '{}' [{}/{}]".format(molotov_table[0],molotov_table[1],molotov_table[2],pltc,molotov_table[4],len_plst)
			else:
				plst = re.findall('\],\["https://(.*?)",\d+,\d+].*?"https://.*?","(.*?)"', ff)
				len_plst = len(plst)
				if len_plst>0:
					for  pl in plst:
						if pl[1].startswith("Regarder"):
							pltc = self.UNAC(pl[1])
							partialtitle = self.PMATCH(ptitle,pltc)
							get_channel = re.findall('regarder[ ]+(.*?)[ ]+en',pltc)
							if get_channel:
								get_channel = self.UNAC(get_channel[0]).replace(" ","")
							else:
								get_channel = None
							partialchannel = self.PMATCH(pchannel,get_channel)
							if partialchannel>0 and partialtitle==0:
								partialtitle=1
							plst = "https://"+pl[0]
							molotov_table = [partialtitle, partialchannel, pltc, plst,-1]
							imsg="Fallback title ({}%) & channel ({}%) : '{}' [{}/{}]".format(molotov_table[0],molotov_table[1],pltc,-1,len_plst)
							break
			if molotov_table[0]==100 and molotov_table[1]==100:
				poster=plst
			elif chkType.startswith("movie"):
				imsg = "Skip movie type '{}' [{}]".format(pltc,len_plst)
			elif molotov_table[0]==100:
				poster=plst
			elif molotov_table[0]>50 and molotov_table[1]:
				poster=plst
			elif chkType=='':
				imsg = "Skip unknown type '{}' [{}]".format(pltc,len_plst)
			elif molotov_table[0] and molotov_table[1]:
				poster=plst
			elif molotov_table[0]>25:
				poster=plst
			else:
				imsg = "Not found '{}' [{}]".format(pltc,len_plst)
			if poster:
				url_poster = re.sub('/\d+x\d+/',"/"+re.sub(',','x',isz)+"/",poster)
				self.savePoster(dwn_poster, url_poster)
				if self.verifyPoster(dwn_poster):
					return True, "[SUCCESS : molotov-google] {} ({}) [{}] => {} => {} => {}".format(title,channel,chkType,imsg,url_mgoo,url_poster)
				else:
					if os.path.exists(dwn_poster):
						os.remove(dwn_poster)
					return False, "[SKIP : molotov-google] {} ({}) [{}] => {} => {} => {} (jpeg error)".format(title,channel,chkType,imsg,url_mgoo,url_poster)
			else:
				return False, "[SKIP : molotov-google] {} ({}) [{}] => {} => {}".format(title,channel,chkType,imsg,url_mgoo)
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : molotov-google] {} [{}] => {} ({})".format(title,chkType,url_mgoo,str(e))

	def search_google(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
		try:
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			chkType, fd = self.checkType(shortdesc,fulldesc)
			poster = None
			url_poster = ""
			year = None
			srch = None
			year = re.findall('19\d{2}|20\d{2}', fd)
			if len(year)>0:
				year = year[0]
			else:
				year = None
			if chkType.startswith("movie"):
				srch=chkType[6:]
			elif chkType.startswith("tv"):
				srch=chkType[3:]
			url_google = quote(title)
			if channel and title.find(channel)<0:
				url_google += "+{}".format(quote(channel))
			if srch:
				url_google += "+{}".format(srch)
			if year:
				url_google += "+{}".format(year)
			url_google = "https://www.google.com/search?q={}&tbm=isch&tbs=ift:jpg%2Cisz:m".format(url_google)
			ff = requests.get(url_google, stream=True, headers=headers).text
			posterlst = re.findall('\],\["https://(.*?)",\d+,\d+]', ff)
			if len(posterlst)==0:
				url_google = quote(title)
				url_google = "https://www.google.com/search?q={}&tbm=isch&tbs=ift:jpg%2Cisz:m".format(url_google)
				ff = requests.get(url_google, stream=True, headers=headers).text
				posterlst = re.findall('\],\["https://(.*?)",\d+,\d+]', ff)
			for pl in posterlst:
				url_poster = "https://{}".format(pl)
				url_poster = re.sub(r"\\u003d", "=", url_poster)
				self.savePoster(dwn_poster, url_poster)
				if self.verifyPoster(dwn_poster):
					poster = pl
					break
			if poster:
				return True, "[SUCCESS : google] {} [{}-{}] => {} => {}".format(title,chkType,year,url_google,url_poster)
			else:
				if os.path.exists(dwn_poster):
					os.remove(dwn_poster)
				return False, "[SKIP : google] {} [{}-{}] => {} => {} (Not found)".format(title,chkType,year,url_google,url_poster)
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : google] {} [{}-{}] => {} => {} ({})".format(title,chkType,year,url_google,url_poster,str(e))

	def search_tvdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
		try:
			series_nb = -1
			chkType, fd = self.checkType(shortdesc,fulldesc)
			ptitle = self.UNAC(title)
			
			year = re.findall('19\d{2}|20\d{2}', fd)
			if len(year)>0:
				year = year[0]
			else:
				year = ""
			url_tvdbg = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(quote(title))
			url_read = requests.get(url_tvdbg).text
			series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read) 
			series_name = re.findall('<SeriesName>(.*?)</SeriesName>', url_read)
			series_year = re.findall('<FirstAired>(19\d{2}|20\d{2})-\d{2}-\d{2}</FirstAired>', url_read)
			i = 0
			for iseries_year in series_year:
				if year=="":
					series_nb = 0
					break
				elif year==iseries_year:
					series_nb = i
					break
				i += 1
			poster = ""
			if series_nb>=0 and series_id and series_id[series_nb]:
				if series_name and series_name[series_nb]:
					series_name = self.UNAC(series_name[series_nb])
				else:
					series_name =''
				if self.PMATCH(ptitle,series_name):
					url_tvdb = "https://thetvdb.com/api/{}/series/{}".format(tvdb_api, series_id[series_nb])
					if lng:
						url_tvdb += "/{}".format(lng[:-3])
					else:
						url_tvdb += "/en"
					url_read = requests.get(url_tvdb).text
					poster = re.findall('<poster>(.*?)</poster>', url_read)
			if poster and poster[0]:
				url_poster = "https://artworks.thetvdb.com/banners/{}".format(poster[0])
				self.savePoster(dwn_poster, url_poster)
				return True, "[SUCCESS : tvdb] {} [{}-{}] => {} => {} => {}".format(title,chkType,year,url_tvdbg,url_tvdb,url_poster)
			else:
				return False, "[SKIP : tvdb] {} [{}-{}] => {} (Not found)".format(title,chkType,year,url_tvdbg)
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : tvdb] {} => {} ({})".format(title,url_tvdbg,str(e))

	def search_imdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
		try:
			url_poster = None
			chkType, fd = self.checkType(shortdesc,fulldesc)
			ptitle = self.UNAC(title)
			aka = re.findall('\((.*?)\)',fd)
			if len(aka)>1 and not aka[1].isdigit():
				aka = aka[1]
			elif len(aka)>0 and not aka[0].isdigit():
				aka = aka[0]
			else:
				aka = None
			if aka:
				paka = self.UNAC(aka)
			else:
				paka = ""
			year = re.findall('19\d{2}|20\d{2}', fd)
			if len(year)>0:
				year = year[0]
			else:
				year = ""
			imsg = ""
			url_mimdb = ""
			url_imdb = ""
			if aka and aka!=title:
				url_mimdb = "https://m.imdb.com/find?q={}%20({})".format(quote(title),quote(aka))
			else:
				url_mimdb = "https://m.imdb.com/find?q={}".format(quote(title))
			url_read = requests.get(url_mimdb).text
			rc=re.compile('<img src="(.*?)".*?<span class="h3">\n(.*?)\n</span>.*?\((\d+)\)(\s\(.*?\))?(.*?)</a>',re.DOTALL)
			url_imdb = rc.findall(url_read)
			if len(url_imdb)==0 and aka:
				url_mimdb = "https://m.imdb.com/find?q={}".format(quote(title))
				url_read = requests.get(url_mimdb).text
				rc=re.compile('<img src="(.*?)".*?<span class="h3">\n(.*?)\n</span>.*?\((\d+)\)(\s\(.*?\))?(.*?)</a>',re.DOTALL)
				url_imdb = rc.findall(url_read)
			len_imdb = len(url_imdb)
			idx_imdb = 0
			pfound = False
			for imdb in url_imdb:
				imdb = list(imdb)
				imdb[1] = self.UNAC(imdb[1])
				tmp=re.findall('aka <i>"(.*?)"</i>',imdb[4])
				if tmp:
					imdb[4]=tmp[0]
				else:
					imdb[4]=""
				imdb[4] = self.UNAC(imdb[4])
				imdb_poster=re.search("(.*?)._V1_.*?.jpg",imdb[0])
				if imdb_poster:
					if imdb[3]=="":
						if year and year!="":
							if year==imdb[2]:
								url_poster = "{}._V1_UY278,1,185,278_AL_.jpg".format(imdb_poster.group(1))
								imsg = "Found title : '{}', aka : '{}', year : '{}'".format(imdb[1],imdb[4],imdb[2])
								if self.PMATCH(ptitle,imdb[1]) or self.PMATCH(ptitle,imdb[4]) or (paka!="" and self.PMATCH(paka,imdb[1])) or (paka!="" and self.PMATCH(paka,imdb[4])):
									pfound = True
									break
							elif not url_poster and (int(year)-1==int(imdb[2]) or int(year)+1==int(imdb[2])):
								url_poster = "{}._V1_UY278,1,185,278_AL_.jpg".format(imdb_poster.group(1))
								imsg = "Found title : '{}', aka : '{}', year : '+/-{}'".format(imdb[1],imdb[4],imdb[2])
								if ptitle==imdb[1] or ptitle==imdb[4] or (paka!="" and paka==imdb[1]) or (paka!="" and paka==imdb[4]):
									pfound = True
									break
						else:
							url_poster = "{}._V1_UY278,1,185,278_AL_.jpg".format(imdb_poster.group(1))
							imsg = "Found title : '{}', aka : '{}', year : ''".format(imdb[1],imdb[4])
							if ptitle==imdb[1] or ptitle==imdb[4] or (paka!="" and paka==imdb[1]) or (paka!="" and paka==imdb[4]):
								pfound = True
								break
				idx_imdb += 1
			if url_poster and pfound:
				self.savePoster(dwn_poster, url_poster)
				return True, "[SUCCESS : imdb] {} [{}-{}] => {} [{}/{}] => {} => {}".format(title,chkType,year,imsg,idx_imdb,len_imdb,url_mimdb,url_poster)
			else:
				return False, "[SKIP : imdb] {} [{}-{}] => {} (No Entry found [{}])".format(title,chkType,year,url_mimdb,len_imdb)
		except Exception as e:
			if os.path.exists(dwn_poster):
				os.remove(dwn_poster)
			return False, "[ERROR : imdb] {} [{}-{}] => {} ({})".format(title,chkType,year,url_mimdb,str(e))

	def savePoster(self, dwn_poster, url_poster):
		with open(dwn_poster,'wb') as f:
			f.write(requests.get(url_poster, stream=True, allow_redirects=True, verify=False).content)
			f.close()

	def verifyPoster(self, dwn_poster):
		try:
			img = Image.open(dwn_poster)
			img.verify()
			if img.format=="JPEG":
				pass
			else:
				try:
					os.remove(dwn_poster)
				except:
					pass
				return None
		except Exception as e:
			try:
				os.remove(dwn_poster)
			except:
				pass
			return None
		return True

	def checkType(self, shortdesc,fulldesc):
		if shortdesc and shortdesc!='':
			fd=shortdesc.splitlines()[0]
		elif fulldesc and fulldesc!='':
			fd=fulldesc.splitlines()[0]
		else:
			fd = ""
		srch = ""
		fds = fd[:60]
		for i in self.checkMovie:
			if i in fds.lower():
				srch = "movie:"+i
				break
		for i in self.checkTV:
			if i in fds.lower():
				srch = "tv:"+i
				break
		return srch, fd

	def UNAC(self,string):
		if not PY3:
			if type(string) != unicode:
				string = unicode(string, encoding='utf-8')
		string = re.sub(u"u0026", "&", string)
		string = re.sub(r"[-,!/\.\":]",' ',string)
		string = re.sub(u"[ÀÁÂÃÄàáâãäåª]", 'a', string)
		string = re.sub(u"[ÈÉÊËèéêë]", 'e', string)
		string = re.sub(u"[ÍÌÎÏìíîï]", 'i', string)
		string = re.sub(u"[ÒÓÔÕÖòóôõöº]", 'o', string)
		string = re.sub(u"[ÙÚÛÜùúûü]", 'u', string)
		string = re.sub(u"[Ññ]", 'n', string)
		string = re.sub(u"[Çç]", 'c', string)
		string = re.sub(u"[Ÿýÿ]", 'y', string)
		string = re.sub(r"[^a-zA-Zα-ωΑ-ΩίϊΐόάέύϋΰήώΊΪΌΆΈΎΫΉΏ0-9 ']","", string)
		string = string.lower()
		string = re.sub(u"u003d", "", string)
		string = re.sub(r'\s{1,}', ' ', string)
		string = string.strip()
		return string

	def PMATCH(self,textA,textB):
		if not textB or textB=="" or not textA or textA=="":
			return 0
		if not textB.startswith(textA):
			lId = len(textA.replace(" ",""))
			textA=textA.split()
			cId = 0
			for id in textA:
				if id in textB:
					cId +=len(id)
			cId = 100*cId/lId
			return cId
		else:
			return 100

threadDB = PosterDB()
threadDB.start()

class PosterAutoDB(PosterDB):
	def __init__(self):
		super(PosterAutoDB, self).__init__()
		self.logdbg = None  # ΜΟΝΟ ΜΙΑ ΦΟΡΑ
		self.checkMovie = ["film", "movie", "фильм", "кино", "ταινία", "película", "cinéma", "cine", "cinema", "filma", "φιλμ", "σινεμά", "adventure", "περιπέτεια", "κινηματογράφος", "comedy", "κωμωδία" ]
		self.checkTV = [ "serial", "series", "serie", "serien", "série", "séries", "serious", "σειρά",
			"folge", "episodio", "episode", "épisode", "l'épisode", "επεισόδιο", "σεζόν", "ep.", "animation",
			"staffel", "soap", "doku", "tv", "talk", "show", "news", "factual", "entertainment", "telenovela", 
			"dokumentation", "dokutainment", "documentary", "ντοκιμαντέρ", "informercial", "information", "sitcom", "reality", 
			"program", "magazine", "ειδήσεις", "mittagsmagazin", "т/с", "м/с", "сезон", "с-н", "эпизод", "сериал", "серия",
			"εκπομπή", "actualité", "discussion", "interview", "débat", "émission", "divertissement", "jeu", "τηλεπαιχνίδι", "magasine",
			"information", "météo", "καιρός", "journal", "sport", "αθλητικά", "culture", "infos", "feuilleton", "téléréalité",
			"société", "clips", "concert", "santé", "éducation", "variété" ]

	def run(self):
		self.logAutoDB("[AutoDB] *** Initialized")
		while True:
			time.sleep(7200)  # 7200 - Start every 2 hours
			self.logAutoDB("[AutoDB] *** Running ***")
			# AUTO ADD NEW FILES - 1440 (24 hours ahead)
			for service in apdb.values():
				try:
					events = epgcache.lookupEvent(['IBDCTESX', (service, 0, -1, 1440)])
					newfd = 0
					newcn = None
					for evt in events:
						canal = [None, None, None, None, None, None]
						canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
						if evt[1] == None or evt[4] == None or evt[5] == None or evt[6] == None:
							self.logAutoDB("[AutoDB] *** missing epg for {}".format(canal[0]))
						else:
							canal[1] = evt[1]
							canal[2] = evt[4]
							canal[3] = evt[5]
							canal[4] = evt[6]
							canal[5] = convtext(canal[2])
							# self.logAutoDB("[AutoDB] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], canal[5]))
							dwn_poster = path_folder + canal[5] + ".jpg"
							if os.path.exists(dwn_poster):
								os.utime(dwn_poster, (time.time(), time.time()))
							if lng == "fr_FR":
								if not os.path.exists(dwn_poster):
									val, log = self.search_molotov_google(dwn_poster, canal[5], canal[4], canal[3], canal[0])
									if val and log.find("SUCCESS"):
										newfd = newfd + 1
								if not os.path.exists(dwn_poster):
									val, log = self.search_programmetv_google(dwn_poster, canal[5], canal[4], canal[3], canal[0])
									if val and log.find("SUCCESS"):
										newfd = newfd + 1
							if not os.path.exists(dwn_poster):
								val, log = self.search_imdb(dwn_poster, canal[2], canal[4], canal[3], canal[0])
								if val and log.find("SUCCESS"):
									newfd = newfd + 1
							if not os.path.exists(dwn_poster):
								val, log = self.search_tmdb(dwn_poster, canal[2], canal[4], canal[3], canal[0])
								if val and log.find("SUCCESS"):
									newfd = newfd + 1
							if not os.path.exists(dwn_poster):
								val, log = self.search_tvdb(dwn_poster, canal[2], canal[4], canal[3], canal[0])
								if val and log.find("SUCCESS"):
									newfd = newfd + 1
							if not os.path.exists(dwn_poster):
								val, log = self.search_google(dwn_poster, canal[2], canal[4], canal[3], canal[0])
								if val and log.find("SUCCESS"):
									newfd = newfd + 1
						newcn = canal[0]
					self.logAutoDB("[AutoDB] {} new file(s) added ({})".format(newfd, newcn))
				except Exception as e:
					self.logAutoDB("[AutoDB] *** service error : {} ({})".format(service, e))
			# AUTO REMOVE OLD FILES
			now_tm = time.time()
			emptyfd = 0
			oldfd = 0
			for f in os.listdir(path_folder):
				diff_tm = now_tm - os.path.getmtime(path_folder + f)
				if diff_tm > 120 and os.path.getsize(path_folder + f) == 0:  # Detect empty files > 2 minutes
					os.remove(path_folder + f)
					emptyfd = emptyfd + 1
				if diff_tm > 259200:  # Detect old files > 3 days old
					os.remove(path_folder + f)
					oldfd = oldfd + 1
			self.logAutoDB("[AutoDB] {} old file(s) removed".format(oldfd))
			self.logAutoDB("[AutoDB] {} empty file(s) removed".format(emptyfd))
			self.logAutoDB("[AutoDB] *** Stopping ***")

	def logAutoDB(self, logmsg):
		if self.logdbg:
			w = open(path_folder + "PosterAutoDB.log", "a+")
			w.write("%s\n" % logmsg)
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