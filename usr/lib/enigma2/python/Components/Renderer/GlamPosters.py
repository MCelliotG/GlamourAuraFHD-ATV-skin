# -*- coding: utf-8 -*-
# GlamPosters renderer (Python 3) for Glamour skins or standalone
# Original work by digiteng...
# © Provided that digiteng rights are protected, all or part of the code can be used, modified...
# Previous enhancements by sunriser and beber...
# 03.2025 Complete recoding and rewriting, single renderer all-in-one by MCelliotG, added OMDB and Fanart searching, dropped python2 support...
# If you use this renderer as is with the latest changes and rename it for your skins, or modify it please respect the credits...
# This code is available on Github (MCelliotG)

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
	from functools import lru_cache
except ImportError:
	def lru_cache(*args, **kwargs):
		def decorator(func):
			return func
		return decorator
try:
	from urllib.parse import quote
except ImportError:
	from urllib import quote
try:
	import queue
	from _thread import start_new_thread
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
fanart_api = "a512bd0eb8f2edd0e553a3addd9ddee2"
omdb_api = "54f9e831"

# isz will be defined in the renderer or the needed attribute
isz_poster = "300,450"
isz_backdrop = "1280,720"

apdb = dict()

# Automaking bouquet for poster generation
autobouquet_file = '/etc/enigma2/userbouquet.favourites.tv'
autobouquet_count = 32

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
					service = ':'.join((line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8], line[9], line[10]))
					apdb[i] = service

# Καθορισμός του βασικού path
path_folder = "/tmp/"

if os.path.isdir("/media/hdd"):
	path_folder = "/media/hdd/"
elif os.path.isdir("/media/usb"):
	path_folder = "/media/usb/"
elif os.path.isdir("/media/mmc"):
	path_folder = "/media/mmc/"

# "poster" & "backdrop" folders are created when they don't exist
poster_folder = path_folder + "poster/"
backdrop_folder = path_folder + "backdrop/"

if not os.path.isdir(poster_folder):
	os.makedirs(poster_folder)

if not os.path.isdir(backdrop_folder):
	os.makedirs(backdrop_folder)

REGEX = re.compile(
	r'\s*\*\d{4}\Z|'  # removes ( *1234)
	r'\[K\d+\]\s*|'  # removes [Κ12], [Κ16] etc.
	r'([\(\[]).*?([\)\]])|'  # removes content within brackets
	r'(\.\s{1,}\").+|'  # removes (. "xxx)
	r'(\?\s{1,}\").+|'  # removes (? "xxx)
	r'(\.{2,}\Z)|'  # removes ".." at the string ends
	r'\b(?=[MDCLXVIΙ])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})([IΙ]X|[IΙ]V|V?[IΙ]{0,3})\b\.?|'  # removes roman characters
	r'(: odc.\d+)|'
	r'(\d+: odc.\d+)|'
	r'(\d+ odc.\d+)|(:)|'
	r'( -[^-]+$)|'  # removes only hyphens that are not in the beginning of a title
	r'(,)|'  # removes commas
	r'!|'
	r'/.*|'  # removes anything after "/"
	r'\|\s[0-9]+\+|'
	r'[0-9]+\+|'
	r'(\"|\"\.|\"\,|\.)\s.+|'  # removes quotes with redundant text
	r'\"|:|'  # removes quotes and colons
	r'Πремьера\.\s|'  # removes russian words
	r'(х|Χ|μ|М|т|Т|д|Д)/ф\s|'
	r'(х|Χ|μ|М|τ|Т|д|Д)/с\s|'
	r'\s(с|С)(езон|ерия|-н|-я)\s.+|'
	r'\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
	r'\.\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
	r'\s(ч|ч\.|с\.|с)\s\d{1,3}.+|'
	r'\d{1,3}(-я|-й|\sс-н).+|'
	r'(\s([ΚκKkTtSse])\d+\s([ΕεEe])\d+\s?\Z)|'  # removes "K2 E5", "S3 E5", "T5 E6", etc. at the end
	r'(\s([EeΕεΚκKkTtSse])\d+\s?\Z)|'  # removes "K2", "S3", etc. at the end
	r'([ΚκKkTtSse])\d+\s([ΕεEe])\d+\s?\Z|'  # removes "E46", "T3 E6" etc. at the end
	r'(\sΚύκλος\s\d+\s?\Z)|'  # removes "Κύκλος X" at the end
	r'(\sΕπεισόδιο\s\d+\s?\Z)|'  # removes "Επεισόδιο Y" at the end
	r'(\sΚύκλος\s\d+\sΕπεισόδιο\s\d+\s?\Z)|'  # removes "Κύκλος X Επεισόδιο Y" at the end
	r'(\sΚ\.\s0?\d+\s?\Z)|'  # removes "Κ.06", "Κ. 6" at the end
	r'(\sΕπ\.\s?0?\d+\s?\Z)|'  # removes "Επ.06", "Επ. 6" at the end
	r'(\s[ΚκKk]\.\s?0?\d+\s?\Z)|'  # removes "Κ." or "κ." at the end
	r'(\s[ΚκKk]\.\s?\d+)'  # remove "Κ." followed by digits
	r'(\sΕπ\.\s?\d+)'  # remove "Επ." followed by digits (this will handle the case like "Επ.55")
	r'\s*',  # remove trailing spaces if there are any
	re.DOTALL
)

def convtext(text, fulldesc=""):
	text = text.replace('\xc2\x86', '')
	text = text.replace('\xc2\x87', '')

	# Keep Dr, Mr, Ms, Prof without deleting what follows (ie dr house)
	text = re.sub(r'\b(Dr|Mr|Ms|Prof)\.\s+', r'\1 ', text, flags=re.IGNORECASE)  

	# Find year of year ranges (π.χ. 2004 or 2004-2013) in fulldesc
	year_match = re.search(r'\b(19\d{2}|20\d{2})(?:-\d{4})?\b', fulldesc)

	# if found it's added within parentheses
	if year_match:
		text += f" ({year_match.group(0)})"

	# cleaning titles with REGEX
	text = REGEX.sub('', text)
	text = re.sub(r"[-,!/\":]", ' ', text)  # replace special characters with space
	text = re.sub(r'\s{1,}', ' ', text)  # replace multiple spaces with a single one
	text = text.strip()
	text = text.lower()
	return str(text)

pdb = queue.LifoQueue()

class PostersDB(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.logdbg = None
		self.checkMovie = [
		# 🎬 Movies
		"cine", "cinema", "cinéma", "film", "filme", "kino", "movie", "película",
		"σινεμά", "ταινία", "κινηματογράφος", "φιλμ", "кино", "фильм",
		# 🎭 Genres
		"abenteuer", "acción", "action", "adventure", "aventura", "comedia", "comedy", "comédie", "drama", "drame",
		"fantasía", "fantasie", "fantastique", "fantasy", "misterio", "mystère", "mystery", "suspenso", "terror", "thriller", "western",
		"γουέστερν", "δράμα", "δράση", "θρίλερ", "κωμωδία", "μυστήριο", "περιπέτεια", "τρόμου",
		"боевик", "драма", "детектив", "комедия", "приключение", "триллер", "ужасы", "вестерн", "фэнтези"
		]
		self.checkTV = [
		# 📺 Series
		"feuilleton", "fernsehserie", "series", "sitcom", "soap opera", "série", "telenovela", "tv series", "tv show", "αισθηματική σειρά",
		"δραματική σειρά", "κομεντί", "κωμική σειρά", "σειρά", "τηλεοπτική σειρά", "σόου", "сериал", "теленовелла", "телесериал",
		# 📢 Episodes/Seasons
		"ep.", "episode", "episodio", "épisode", "folge", "s.", "saison", "season", "staffel", "t.", "temporada",
		"επεισόδιο", "επ.", "κ.", "κύκλος", "σεζόν", "м/с", "с-н", "сериал", "серия", "сезон", "т/с", "эпизод", "эпизод",
		# 🎨 Animation/Reality/Documentaries
		"animation", "animación", "anime", "cartoon", "caricatura", "dessin animé", "documentaire", "documental", "documentary", "dokumentation", "reality", "realidad",
		"reality-show", "téléréalité", "άνιμε", "κινουμένων σχεδίων", "καρτούν", "ντοκιμαντέρ", "ριάλιτι", "анимация", "аниме", "мультфильм", "документальный", "реалити",
		# 📰 News/Information
		"actualité", "aktuell", "current affairs", "información", "infotainment", "journal", "nachrichten",
		"news", "noticias", "ειδήσεις", "ενημέρωση", "ινφοτέιντμεντ", "новости", "информация",
		# 🎤 Talk Shows/Magazines
		"entrevista", "magazine", "magazin", "revista", "talk show", "talkshow",
		"μαγκαζίνο", "συζήτηση", "συνέντευξη", "τοκ σόου", "журнал", "ток-шоу",
		# 🎭 Entertainment
		"concurso", "divertissement", "entertainment", "entretenimiento", "game show", "jeu télévisé", "quizsendung", "unterhaltung",
		"variedad", "varieté", "varieties", "variété", "ποικιλία", "τηλεπαιχνίδι", "ψυχαγωγία", "варьете", "игровое шоу", "развлекательное шоу",
		# 🎼 Music
		"clips", "concert", "concierto", "klip", "konzert", "music", "musique", "música", "videoclips",
		"βιντεοκλίπ", "κλιπ", "μουσική", "συναυλία", "клипы", "концерт", "музыка",
		# 🏆 Sports
		"athletics", "athlétisme", "atletismo", "baloncesto", "basket", "basketball", "basketbol", "deportes", "football", "fútbol", "fußball",
		"leichtathletik", "sports","αθλητικά", "μπάσκετ", "ποδόσφαιρο", "στίβος", "баскетбол", "легкая атлетика", "спорт", "футбол",
		# 🌦️ Weather
		"clima", "météo", "weather", "wetter", "καιρός", "δελτίο καιρού", "погода",
		# 📚 Education/Health/Society
		"bildung", "culture", "cultura", "education", "educación", "gesellschaft", "gesundheit", "health", "kultur", "santé", "sociedad", "society",
		"εκπαίδευση", "επικαιρότητα", "κοινωνία", "πολιτισμός", "υγεία", "образование", "здоровье", "общество", "культура"
]

	def run(self):
		self.logDB("[QUEUE] : Initialized")
		while True:
			canal = pdb.get()
			self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], canal[5]))

			# Define storage folder by the usedImage attribute in the skin code
			usedImage = canal[6]  # receiving usedImage from the last queued object 
			subfolder = "poster/" if usedImage == "poster" else "backdrop/"
			dwn_image = path_folder + subfolder + canal[5] + ".jpg"

			# Making cleaned_title for better searching
			cleaned_title = convtext(canal[2], canal[3])

			# If the file exists update its timestamp
			if os.path.exists(dwn_image):
				os.utime(dwn_image, (time.time(), time.time()))

			# Search and store image functions (without google searches)
			search_functions = [
				self.search_tmdb, self.search_tvdb, self.search_omdb,
				self.search_fanart, self.search_imdb
			]

			# Search and store image functions (google searches)
			google_searches = [
				self.search_molotov_google,
				self.search_programmetv_google, self.search_google
			]
			found = False

			for search_function in search_functions:
				if not os.path.exists(dwn_image):
					try:
						val, log = search_function(dwn_image, cleaned_title, canal[4], canal[3], usedImage)
						self.logDB(log)
						if val:
							print(f"GlamPosters: [SUCCESS] Found image using {search_function.__name__}")
							found = True
							break
					except Exception as e:
						print(f"GlamPosters: [ERROR] {search_function.__name__} failed: {str(e)}")
						self.logDB(f"[ERROR] {search_function.__name__} failed: {str(e)}")

			if not found:
				print("GlamPosters: [INFO] No image found, trying Google Searches with channel name.")
				try:
					for google_search in google_searches:
						val, log = google_search(dwn_image, cleaned_title, canal[0], canal[4], canal[3], usedImage)
						if val:
							print(f"GlamPosters: [SUCCESS] Found image using {google_search.__name__}")
							found = True
							break
				except Exception as e:
					print(f"GlamPosters: [ERROR] {google_search.__name__} failed: {str(e)}")
					self.logDB(f"[ERROR] {google_search.__name__} failed: {str(e)}")

			pdb.task_done()

	def logDB(self, logmsg):
		if self.logdbg:
			w = open(path_folder + "PostersDB.log", "a+")
			w.write("%s\n"%logmsg)
			w.close()

# TMDB Search
	@lru_cache(maxsize=500)
	def search_tmdb(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			year = ""
			url_tmdb = ""
			image_url = None

			# define type (movie or series)
			chkType, fd = self.checkType(shortdesc, fulldesc)
			srch = "multi" if chkType == "" else "movie" if chkType.startswith("movie") else "tv"

			# trying year extraction
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fd)
			if year_matches:
				year = year_matches[-1]  # using last year if many

			# create URL TMDB
			url_tmdb = f"https://api.themoviedb.org/3/search/{srch}?api_key={tmdb_api}&query={quote(title)}"
			if year:
				url_tmdb += f"&year={year}"
			if lng:
				url_tmdb += f"&language={lng[:-3]}"

			response = requests.get(url_tmdb, timeout=5).json()
			if response and response.get('results'):
				result = response['results'][0]  

				# select suitable image URL
				if usedImage == "poster" and result.get('poster_path'):
					image_url = f"https://image.tmdb.org/t/p/w{isz_poster.split(',')[0]}{result['poster_path']}"
				elif usedImage == "backdrop" and result.get('backdrop_path'):
					image_url = f"https://image.tmdb.org/t/p/w{isz_backdrop.split(',')[0]}{result['backdrop_path']}"

			if image_url:
				self.saveImage(dwn_image, image_url)
				return True, f"[SUCCESS : tmdb] {title} [{chkType}-{year}] => {url_tmdb} => {image_url}"
			else:
				return False, f"[SKIP : tmdb] {title} [{chkType}-{year}] => {url_tmdb} (Not found)"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[ERROR : tmdb] {title} [{chkType}-{year}] => {url_tmdb} ({str(e)})"

# TVDB Search
	@lru_cache(maxsize=500)
	def search_tvdb(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			series_nb = -1
			chkType, fd = self.checkType(shortdesc, fulldesc)
			ptitle = self.UNAC(title)

			# trying year extraction from fulldesc
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fd)
			year = year_matches[0] if year_matches else ""

			url_tvdb = f"https://thetvdb.com/api/GetSeries.php?seriesname={quote(title)}"
			url_read = requests.get(url_tvdb, timeout=5).text

			try:
				series_id = re.findall(r'<seriesid>(.*?)</seriesid>', url_read)
				series_name = re.findall(r'<SeriesName>(.*?)</SeriesName>', url_read)
				series_year = re.findall(r'<FirstAired>(19\d{2}|20\d{2})-\d{2}-\d{2}</FirstAired>', url_read)
			except Exception as e:
				return False, f"[ERROR : tvdb] Failed parsing response: {str(e)}"

			# chose correct order by year
			for i, iseries_year in enumerate(series_year):
				if not year or year == iseries_year:
					series_nb = i
					break

			if series_nb >= 0 and series_id:
				series_name_clean = self.UNAC(series_name[series_nb]) if series_name else ""
				if series_name_clean and self.PMATCH(ptitle, series_name_clean):
					url_tvdb = f"https://thetvdb.com/api/{tvdb_api}/series/{series_id[series_nb]}"
					url_tvdb += f"/{lng[:-3]}" if lng else "/en"

					url_read = requests.get(url_tvdb, timeout=5).text

					# select correct image type by the usedImage skin attribute
					if usedImage == "poster":
						image = re.findall(r'<poster>(.*?)</poster>', url_read)
					elif usedImage == "backdrop":
						image = re.findall(r'<fanart>(.*?)</fanart>', url_read) or []  # To TVDB χρησιμοποιεί "fanart" για backdrops

					if image and image[0]:
						url_image = f"https://artworks.thetvdb.com/banners/{image[0]}"
						self.saveImage(dwn_image, url_image)
						return True, f"[SUCCESS : tvdb] {title} [{chkType}-{year}] => {url_tvdb} => {url_image}"
			
			return False, f"[SKIP : tvdb] {title} [{chkType}-{year}] => {url_tvdb} (Not found)"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[ERROR : tvdb] {title} [{chkType}] => {url_tvdb} ({str(e)})"

# OMDB Search
	@lru_cache(maxsize=500)
	def search_omdb(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			# trying year extraction from fulldesc
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fulldesc)
			year = year_matches[0] if year_matches else ""

			# create URL quote
			url_omdb = f"https://www.omdbapi.com/?t={quote(title)}&apikey={omdb_api}"
			if year:
				url_omdb += f"&y={year}"

			response = requests.get(url_omdb, timeout=5).json()

			# select correct image type by the usedImage skin attribute
			image_url = None
			if usedImage == "poster" and response.get("Poster") and response["Poster"] != "N/A":
				image_url = response["Poster"]
			elif usedImage == "backdrop":
				return False, "[SKIP : omdb] No backdrops available on OMDb."

			# store image
			if image_url:
				self.savePoster(dwn_image, image_url)
				return True, f"[SUCCESS : omdb] {title} ({year}) => {image_url}"
			else:
				return False, f"[SKIP : omdb] {title} ({year}) (No valid poster found)"

		except Exception as e:
			return False, f"[ERROR : omdb] {title} ({year}) ({str(e)})"

# Fanart Search
	@lru_cache(maxsize=500)
	def search_fanart(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			# searching IMDb ID from OMDB
			url_omdb = f"https://www.omdbapi.com/?t={quote(title)}&apikey={omdb_api}"
			response = requests.get(url_omdb).json()
			imdb_id = response.get("imdbID")
			if not imdb_id:
				return False, f"[SKIP : fanart] {title} (No IMDb ID found)"

			# searching Fanart.tv
			url_fanart = f"https://webservice.fanart.tv/v3/movies/{imdb_id}?api_key={fanart_api}"
			response = requests.get(url_fanart, timeout=5).json()

			# select correct image type by the usedImage skin attribute
			image_url = None
			if usedImage == "poster" and "movieposter" in response and response["movieposter"]:
				image_url = response["movieposter"][0]["url"]
			elif usedImage == "backdrop" and "moviebackground" in response and response["moviebackground"]:
				image_url = response["moviebackground"][0]["url"]

			# store image
			if image_url:
				self.savePoster(dwn_image, image_url)
				return True, f"[SUCCESS : fanart] {title} => {image_url}"
			else:
				return False, f"[SKIP : fanart] {title} (No image found)"

		except Exception as e:
			return False, f"[ERROR : fanart] {title} ({str(e)})"

#IMDB Search
	@lru_cache(maxsize=500)
	def search_imdb(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			url_image = None
			chkType, fd = self.checkType(shortdesc, fulldesc)
			ptitle = self.UNAC(title)

			# extracting alternative title (aka)
			aka = re.findall(r'\((.*?)\)', fd)
			aka = aka[1] if len(aka) > 1 and not aka[1].isdigit() else aka[0] if len(aka) > 0 and not aka[0].isdigit() else None
			paka = self.UNAC(aka) if aka else ""

			# extracting year
			year_matches = re.findall(r'19\d{2}|20\d{2}', fd)
			year = year_matches[0] if year_matches else ""

			imsg = ""
			url_mimdb = f"https://m.imdb.com/find?q={quote(title)}"
			if aka and aka != title:
				url_mimdb += f"%20({quote(aka)})"

			url_read = requests.get(url_mimdb, timeout=5).text

			# Regex for entering data from IMDb
			rc = re.compile(r'<img src="(.*?)".*?<span class="h3">\n(.*?)\n</span>.*?\((\d+)\)(\s\(.*?\))?(.*?)</a>', re.DOTALL)
			url_imdb = rc.findall(url_read)

			# if no results found retrying with aka
			if not url_imdb and aka:
				url_mimdb = f"https://m.imdb.com/find?q={quote(title)}"
				print(f"GlamPosters: [DEBUG] Retrying IMDb search without aka: {url_mimdb}")
				url_read = requests.get(url_mimdb, timeout=5).text
				url_imdb = rc.findall(url_read)

			len_imdb = len(url_imdb)
			idx_imdb = 0
			pfound = False

			# check results
			for imdb in url_imdb:
				imdb = list(imdb)
				imdb[1] = self.UNAC(imdb[1])  # Καθαρισμός τίτλου
				imdb[4] = self.UNAC(re.findall(r'aka <i>"(.*?)"</i>', imdb[4])[0]) if re.findall(r'aka <i>"(.*?)"</i>', imdb[4]) else ""

				# image URL extraction
				imdb_image = re.search(r"(.*?)._V1_.*?.jpg", imdb[0])
				if imdb_image:
					# year matching
					if year and year == imdb[2]:
						image_url = f"{imdb_image.group(1)}._V1_UY278,1,185,278_AL_.jpg" if usedImage == "poster" else f"{imdb_image.group(1)}._V1_UX1920,1,1080,1920_AL_.jpg"
						imsg = f"Found title: '{imdb[1]}', aka: '{imdb[4]}', year: '{imdb[2]}'"
						pfound = True
					elif not url_image and (int(year) - 1 == int(imdb[2]) or int(year) + 1 == int(imdb[2])):
						image_url = f"{imdb_image.group(1)}._V1_UY278,1,185,278_AL_.jpg" if usedImage == "poster" else f"{imdb_image.group(1)}._V1_UX1920,1,1080,1920_AL_.jpg"
						imsg = f"Found title: '{imdb[1]}', aka: '{imdb[4]}', year: '+/-{imdb[2]}'"
						pfound = True
					elif not year:
						image_url = f"{imdb_image.group(1)}._V1_UY278,1,185,278_AL_.jpg" if usedImage == "poster" else f"{imdb_image.group(1)}._V1_UX1920,1,1080,1920_AL_.jpg"
						imsg = f"Found title: '{imdb[1]}', aka: '{imdb[4]}', year: ''"
						pfound = True

					if pfound:
						break

				idx_imdb += 1

			# store image if found
			if image_url and pfound:
				self.saveImage(dwn_image, image_url)
				return True, f"[SUCCESS : imdb] {title} [{chkType}-{year}] => {imsg} [{idx_imdb}/{len_imdb}] => {url_mimdb} => {image_url}"
			else:
				return False, f"[SKIP : imdb] {title} [{chkType}-{year}] => {url_mimdb} (No Entry found [{len_imdb}])"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[ERROR : imdb] {title} [{chkType}-{year}] => {url_mimdb} ({str(e)})"

# Molotov Search
	@lru_cache(maxsize=500)
	def search_molotov_google(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel):
		try:
			headers = {
				"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
			}
			chkType, fd = self.checkType(shortdesc, fulldesc)

			ptitle = self.UNAC(title)
			pchannel = self.UNAC(channel).replace(" ", "") if channel else ""

			image = None
			pltc = None
			imsg = ""
			url_mgoo = f"site:molotov.tv+{quote(title)}"
			if channel and title.find(channel.split()[0]) < 0:
				url_mgoo += f"+{quote(channel)}"
			url_mgoo = f"https://www.google.com/search?q={url_mgoo}&tbm=isch"

			ff = requests.get(url_mgoo, stream=True, headers=headers, timeout=5).text
			plst = re.findall(r'https://www.molotov.tv/(.*?)"(?:.*?)?"(.*?)"', ff)
			len_plst = len(plst)

			molotov_table = [0, 0, None, None, 0]
			molotov_final = False
			partialtitle = 0
			partialchannel = 100

			# process search results
			for molotov_id, pl in enumerate(plst):
				get_path = f"https://www.molotov.tv/{pl[0]}"
				get_name = self.UNAC(pl[1])
				get_title_match = re.findall(r'(.*?)[ ]+en[ ]+streaming', get_name)
				get_title = get_title_match[0] if get_title_match else None

				get_channel_match = re.findall(r'(?:streaming|replay)?[ ]+sur[ ]+(.*?)[ ]+molotov.tv', get_name)
				if get_channel_match:
					get_channel = self.UNAC(get_channel_match[0]).replace(" ", "")
				else:
					get_channel_match = re.findall(r'regarder[ ]+(.*?)[ ]+en', get_name)
					get_channel = self.UNAC(get_channel_match[0]).replace(" ", "") if get_channel_match else None

				# calculate similarity
				partialtitle = 100 if get_title == ptitle else self.PMATCH(ptitle, get_title)
				partialchannel = 100 if get_channel == pchannel else self.PMATCH(pchannel, get_channel)

				# update of best result
				if partialtitle > molotov_table[0]:
					molotov_table = [partialtitle, partialchannel, get_name, get_path, molotov_id]

				if partialtitle == 100 and partialchannel == 100:
					molotov_final = True
					break

			# if relative content found, download image
			if molotov_table[0]:
				ffm = requests.get(molotov_table[3], stream=True, headers=headers, timeout=5).text
				pltt = re.findall(r'"https://fusion.molotov.tv/(.*?)/jpg" alt="(.*?)"', ffm)

				if pltt:
					pltc = self.UNAC(pltt[0][1])
					plst = f"https://fusion.molotov.tv/{pltt[0][0]}/jpg"
					imsg = f"Found title ({molotov_table[0]}%) & channel ({molotov_table[1]}%) : '{molotov_table[2]}' + '{pltc}' [{molotov_table[4]}/{len_plst}]"

			# alternative image search
			else:
				plst = re.findall(r'\],\["https://(.*?)",\d+,\d+].*?"https://.*?","(.*?)"', ff)
				len_plst = len(plst)
				if plst:
					for pl in plst:
						if pl[1].startswith("Regarder"):
							pltc = self.UNAC(pl[1])
							partialtitle = self.PMATCH(ptitle, pltc)
							get_channel_match = re.findall(r'regarder[ ]+(.*?)[ ]+en', pltc)
							get_channel = self.UNAC(get_channel_match[0]).replace(" ", "") if get_channel_match else None
							partialchannel = self.PMATCH(pchannel, get_channel)
							if partialchannel > 0 and partialtitle == 0:
								partialtitle = 1
							plst = f"https://{pl[0]}"
							molotov_table = [partialtitle, partialchannel, pltc, plst, -1]
							imsg = f"Fallback title ({molotov_table[0]}%) & channel ({molotov_table[1]}%) : '{pltc}' [{-1}/{len_plst}]"
							break

			# suitable image selection
			if molotov_table[0] == 100 and molotov_table[1] == 100:
				image = plst
			elif chkType.startswith("movie"):
				imsg = f"Skip movie type '{pltc}' [{len_plst}]"
			elif molotov_table[0] == 100:
				image = plst
			elif molotov_table[0] > 50 and molotov_table[1]:
				image = plst
			elif chkType == '':
				imsg = f"Skip unknown type '{pltc}' [{len_plst}]"
			elif molotov_table[0] and molotov_table[1]:
				image = plst
			elif molotov_table[0] > 25:
				image = plst
			else:
				imsg = f"Not found '{pltc}' [{len_plst}]"

			# store valid image, if found
			if image:
				url_image = re.sub(r'/\d+x\d+/', f"/{re.sub(',', 'x', isz)}/", image)
				self.saveImage(dwn_image, url_image)
				if self.verifyImage(dwn_image):
					return True, f"[SUCCESS : molotov-google] {title} ({channel}) [{chkType}] => {imsg} => {url_mgoo} => {url_image}"
				else:
					if os.path.exists(dwn_image):
						os.remove(dwn_image)
					return False, f"[SKIP : molotov-google] {title} ({channel}) [{chkType}] => {imsg} => {url_mgoo} => {url_image} (jpeg error)"
			else:
				return False, f"[SKIP : molotov-google] {title} ({channel}) [{chkType}] => {imsg} => {url_mgoo}"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[ERROR : molotov-google] {title} [{chkType}] => {url_mgoo} ({str(e)})"

#ProgrammeTV Search
	@lru_cache(maxsize=500)
	def search_programmetv_google(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel):
		try:
			headers = {
				"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
			}
			chkType, fd = self.checkType(shortdesc, fulldesc)

			# ignore movies (prefer tv shows only)
			if chkType.startswith("movie"):
				return False, f"[SKIP : programmetv-google] {title} [{chkType}] => Skip movie title"

			# search year within full description
			year_match = re.findall(r'19\d{2}|20\d{2}', fd)
			year = year_match[0] if year_match else ""

			# create search quote
			url_ptv = f"site:programme-tv.net+{quote(title)}"
			if channel and title.find(channel.split()[0]) < 0:
				url_ptv += f"+{quote(channel)}"
			if year:
				url_ptv += f"+{year}"

			# add image type (poster or backdrop)
			url_ptv += "+poster" if usedImage == "poster" else "+backdrop"

			# final search URL in Google Images
			url_ptv = f"https://www.google.com/search?q={url_ptv}&tbm=isch&tbs=ift:jpg%2Cisz:m"
			ff = requests.get(url_ptv, stream=True, headers=headers, timeout=5).text

			# extract image URL
			imagelst = re.findall(r'\],\["https://(.*?)",\d+,\d+]', ff)
			if imagelst:
				url_image = f"https://{imagelst[0]}"
				url_image = re.sub(r"\\u003d", "=", url_image)

				# analyze image dimensions
				url_image_size = re.findall(r'/(\d+)x(\d+)/', url_image)
				if url_image_size:
					h_ori = float(url_image_size[0][1])
					h_tar = float(re.findall(r'(\d+)', isz)[1])
					ratio = h_ori / h_tar
					w_ori = float(url_image_size[0][0])
					w_tar = int(w_ori / ratio)
					h_tar = int(h_tar)
					url_image = re.sub(r'/\d+x\d+/', f"/{w_tar}x{h_tar}/", url_image)

				url_image = re.sub(r'crop-from/top/', '', url_image)

				# store image
				self.saveImage(dwn_image, url_image)

				# verify image
				if self.verifyImage(dwn_image):
					return True, f"[SUCCESS : programmetv-google] {title} [{chkType}] => {url_ptv} => {url_image} (initial size: {url_image_size})"
				else:
					if os.path.exists(dwn_image):
						os.remove(dwn_image)
					return False, f"[SKIP : programmetv-google] {title} [{chkType}] => {url_ptv} => {url_image} (initial size: {url_image_size}) (jpeg error)"

			return False, f"[SKIP : programmetv-google] {title} [{chkType}] => {url_ptv} (Not found)"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[ERROR : programmetv-google] {title} [{chkType}] => {url_ptv} ({str(e)})"

#Google Search
	@lru_cache(maxsize=500)
	def search_google(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel):
		try:
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			chkType, fd = self.checkType(shortdesc, fulldesc)
			image = None
			url_image = ""
			year = None
			srch = None
			canal_name = None

			# retrieve service name (canal[0]) from EPG
			service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
			if service:
				canal_name = ServiceReference(service).getServiceName()
				canal_name = self.UNAC(canal_name)  # remove special characters

			# find year in description
			year = re.findall(r'19\d{2}|20\d{2}', fd)
			if len(year) > 0:
				year = year[0]
			else:
				year = None

			# define search by type
			if chkType.startswith("movie"):
				srch = chkType[6:]
			elif chkType.startswith("tv"):
				srch = chkType[3:]

			# **first search attempt (without channel service name)**
			url_google = quote(title)
			if srch:
				url_google += "+{}".format(srch)
			if year:
				url_google += "+{}".format(year)
			if usedImage == "poster":
				url_google += "+poster"
			elif usedImage == "backdrop":
				url_google += "+backdrop"

			url_google = "https://www.google.com/search?q={}&tbm=isch&tbs=ift:jpg%2Cisz:m".format(url_google)
			ff = requests.get(url_google, stream=True, headers=headers, timeout=5).text

			# retrieve image
			imagelst = re.findall(r'\],\["https://(.*?)",\d+,\d+]', ff)
			if len(imagelst) == 0 and canal_name:  # **Αν αποτύχει, δοκιμάζουμε με το κανάλι**
				print(f"GlamPosters: [DEBUG] No image found. Retrying with channel name: {canal_name}")
				url_google = quote(title) + "+" + quote(canal_name)
				if usedImage == "poster":
					url_google += "+poster"
				elif usedImage == "backdrop":
					url_google += "+backdrop"
				url_google = "https://www.google.com/search?q={}&tbm=isch&tbs=ift:jpg%2Cisz:m".format(url_google)
				ff = requests.get(url_google, stream=True, headers=headers, timeout=5).text
				imagelst = re.findall(r'\],\["https://(.*?)",\d+,\d+]', ff)

			# select first available image
			for pl in imagelst:
				url_image = "https://{}".format(pl)
				url_image = re.sub(r"\\u003d", "=", url_image)

				# **filter for avoiding channel logos instead of posters or backdrops**
				if "logo" in url_image.lower() or "channel" in url_image.lower():
					print(f"GlamPosters: [DEBUG] Skipping potential channel logo: {url_image}")
					continue

				self.saveImage(dwn_image, url_image)
				if self.verifyImage(dwn_image):
					image = pl
					break

			if image:
				return True, "[SUCCESS : google] {} [{}-{}] => {} => {}".format(title, chkType, year, url_google, url_image)
			else:
				if os.path.exists(dwn_image):
					os.remove(dwn_image)
				return False, "[SKIP : google] {} [{}-{}] => {} => {} (Not found)".format(title, chkType, year, url_google, url_image)
		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, "[ERROR : google] {} [{}-{}] => {} => {} ({})".format(title, chkType, year, url_google, url_image, str(e))


	def saveImage(self, dwn_image, url_image):
		with open(dwn_image, 'wb') as f:
			f.write(requests.get(url_image, stream=True, allow_redirects=True, verify=False).content)
			f.close()

	def verifyImage(self, dwn_image):
		try:
			img = Image.open(dwn_image)
			img.verify()
			if img.format == "JPEG":
				return True
			else:
				try:
					os.remove(dwn_image)
				except:
					pass
				return None
		except Exception as e:
			try:
				os.remove(dwn_image)
			except:
				pass
			return None

	def checkType(self, shortdesc, fulldesc):
		if shortdesc and shortdesc != '':
			fd = shortdesc.splitlines()[0]
		elif fulldesc and fulldesc != '':
			fd = fulldesc.splitlines()[0]
		else:
			fd = ""

		srch = ""
		fds = fd[:60]

		for i in self.checkMovie:
			if i in fds.lower():
				srch = "movie:" + i
				break
		for i in self.checkTV:
			if i in fds.lower():
				srch = "tv:" + i
				break

		return srch, fd


	def UNAC(self, string):
		# replace special characters
		string = re.sub(u"u0026", "&", string)
		string = re.sub(r"[-,!/\.\":]", " ", string)

		# replace diacritics with plain latin characters
		translit_map = {
			u"[ÀÁÂÃÄàáâãäåª]": 'a', u"[ÈÉÊËèéêë]": 'e', u"[ÍÌÎÏìíîï]": 'i',
			u"[ÒÓÔÕÖòóôõöº]": 'o', u"[ÙÚÛÜùúûü]": 'u', u"[Ññ]": 'n',
			u"[Çç]": 'c', u"[Ÿýÿ]": 'y'
		}
		for pattern, replacement in translit_map.items():
			string = re.sub(pattern, replacement, string)

		# keep only English and Greek characters and numbers
		string = re.sub(r"[^a-zA-Zα-ωΑ-ΩίϊΐόάέύϋΰήώΊΪΌΆΈΎΫΉΏ0-9 ']", "", string)
		string = string.lower()
		string = re.sub(u"u003d", "", string)
		string = re.sub(r'\s{1,}', ' ', string)  # replace multiple spaces
		string = string.strip()
		return string

	def PMATCH(self, textA, textB):
		if not textB or textB == "" or not textA or textA == "":
			return 0
		if textB.startswith(textA):
			return 100  # full match
		
		# calculate match percentage
		lId = len(textA.replace(" ", ""))
		textA = textA.split()
		cId = sum(len(id) for id in textA if id in textB)
		return 100 * cId // lId if lId > 0 else 0

# start thread for image processing
threadDB = PostersDB()
threadDB.start()

class PosterAutoDB(PostersDB):
	def __init__(self):
		super(PosterAutoDB, self).__init__()
		self.logdbg = None  # just once
		self.checkMovie = ["abenteuer", "acción", "action", "adventure", "aventura", "comedia", "comedy", "comédie", "drama", "drame", "cine", "cinema", "cinéma", "film", "filme", "kino", "movie",
		"película", "fantasía", "fantasie", "fantastique", "fantasy", "misterio", "mystère", "mystery", "suspenso", "terror", "thriller", "western", "γουέστερν", "δράμα", "δράση",
		"θρίλερ", "κωμωδία", "μυστήριο", "περιπέτεια", "τρόμου", "σινεμά", "ταινία", "κινηματογράφος", "φιλμ", "кино", "фильм",
		"боевик", "драма", "детектив", "комедия", "приключение", "триллер", "ужасы", "вестерн", "фэнтези"]
		self.checkTV = ["actualité", "aktuell", "current affairs", "información", "infotainment", "journal", "nachrichten", "animation", "animación", "anime", "cartoon", "caricatura",
		"dessin animé", "documentaire", "documental", "documentary", "dokumentation", "reality", "realidad", "athletics", "athlétisme", "atletismo", "baloncesto", "basket", "basketball",
		"basketbol", "deportes", "football", "fútbol", "fußball", "bildung", "culture", "cultura", "education", "educación", "gesellschaft", "gesundheit", "health", "kultur", "santé",
		"sociedad", "society", "clima", "météo", "weather", "wetter", "καιρός", "δελτίο καιρού", "погода", "clips", "concert", "concierto", "klip", "konzert", "music", "musique",
		"música", "videoclips", "concurso", "divertissement", "entertainment", "entretenimiento", "game show", "jeu télévisé", "quizsendung", "unterhaltung", "entrevista", "magazine",
		"magazin", "revista", "talk show", "talkshow", "ep.", "episode", "episodio", "épisode", "folge", "s.", "saison", "season", "staffel", "t.", "temporada", "feuilleton",
		"fernsehserie", "series", "sitcom", "soap opera", "série", "telenovela", "tv series", "tv show", "αισθηματική σειρά", "leichtathletik", "sports","αθλητικά", "μπάσκετ",
		"ποδόσφαιρο", "στίβος", "баскетбол", "легкая атлетика", "спорт", "футбол", "news", "noticias", "ειδήσεις", "ενημέρωση", "ινφοτέιντμεντ", "новости", "информация", "reality-show", 
		"téléréalité", "άνιμε", "κινουμένων σχεδίων", "καρτούν", "ντοκιμαντέρ", "ριάλιτι", "анимация", "аниме", "мультфильм", "документальный", "реалити", "variedad", "varieté",
		"varieties", "variété", "ποικιλία", "τηλεπαιχνίδι", "ψυχαγωγία", "варьете", "игровое шоу", "развлекательное шоу", "βιντεοκλίπ", "κλιπ", "μουσική", "συναυλία", "клипы",
		"концерт", "музыка", "δραματική σειρά", "κομεντί", "κωμική σειρά", "σειρά", "τηλεοπτική σειρά", "σόου", "сериал", "теленовелла", "телесериал", "εκπαίδευση", "επικαιρότητα",
		"κοινωνία", "πολιτισμός", "υγεία", "образование", "здоровье", "общество", "культура", "επεισόδιο", "επ.", "κ.", "κύκλος", "σεζόν", "м/с", "с-н", "сериал", "серия", "сезон",
		"т/с", "эпизод", "эпизод", "μαγκαζίνο", "συζήτηση", "συνέντευξη", "τοκ σόου", "журнал", "ток-шоу"]

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
						canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').replace(' HD','')
						if evt[1] is None or evt[4] is None or evt[5] is None or evt[6] is None:
							self.logAutoDB("[AutoDB] *** Missing EPG for {}".format(canal[0]))
						else:
							canal[1] = evt[1]  # Start time
							canal[2] = evt[4]  # Event title
							canal[3] = evt[5]  # Full description
							canal[4] = evt[6]  # Short description
							canal[5] = convtext(canal[2], canal[3])  # title with year if year exists

							# posters and backdrops selection
							for image_type in ["poster", "backdrop"]:
								usedImage = image_type
								subfolder = "poster/" if image_type == "poster" else "backdrop/"
								dwn_image = path_folder + subfolder + canal[5] + ".jpg"

								if os.path.exists(dwn_image):
									os.utime(dwn_image, (time.time(), time.time()))
									continue

								# ** search engine priorities **
								search_functions = [
									self.search_tmdb,
									self.search_tvdb,
									self.search_omdb,
									self.search_fanart,
									self.search_imdb,
									self.search_molotov_google,
									self.search_programmetv_google,
									self.search_google
								]

								# ** try all search engines in priority order **
								for search_function in search_functions:
									if not os.path.exists(dwn_image):
										val, log = search_function(dwn_image, canal[5], canal[4], canal[3], canal[0], usedImage)
										self.logAutoDB(log)
										if val and "SUCCESS" in log:
											newfd += 1
											break  # stops search if suitable image is found

					newcn = canal[0]
					self.logAutoDB("[AutoDB] {} new file(s) added ({})".format(newfd, newcn))
				except Exception as e:
					self.logAutoDB("[AutoDB] *** Service error: {} ({})".format(service, e))

			# **auto delete old and empty files**
			now_tm = time.time()
			emptyfd = 0
			oldfd = 0
			for f in os.listdir(path_folder):
				diff_tm = now_tm - os.path.getmtime(path_folder + f)
				if diff_tm > 120 and os.path.getsize(path_folder + f) == 0:  #scan empty files > 2 minutes
					os.remove(path_folder + f)
					emptyfd += 1
				if diff_tm > 259200:  # scan old files > 3 days
					os.remove(path_folder + f)
					oldfd += 1
			self.logAutoDB("[AutoDB] {} old file(s) removed".format(oldfd))
			self.logAutoDB("[AutoDB] {} empty file(s) removed".format(emptyfd))
			self.logAutoDB("[AutoDB] *** Stopping ***")

	def logAutoDB(self, logmsg):
		if self.logdbg:
			with open(path_folder + "PosterAutoDB.log", "a+") as w:
				w.write("%s\n" % logmsg)

threadAutoDB = PosterAutoDB()
threadAutoDB.start()

class GlamPosters(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.nxts = 0
		self.canal = [None, None, None, None, None, None]
		self.oldCanal = None
		self.usedImage = "poster"  # default poster
		self.intCheck()
		self.timer = eTimer()
		self.timer.callback.append(self.showPoster)
		self.logdbg = None

	def applySkin(self, desktop, parent):
		attribs = []
		for (attrib, value,) in self.skinAttributes:
			if attrib == "nexts":
				self.nxts = int(value)
			elif attrib == "usedImage": # image type defined in the skin
				self.usedImage = value
			attribs.append((attrib, value))
		self.isz = isz_poster if self.usedImage == "poster" else isz_backdrop
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
			return  # poster is hidden ONLY when image must be cleared

		servicetype = None
		try:
			service = None
			if isinstance(self.source, ServiceEvent):  # source="ServiceEvent"
				service = self.source.getCurrentService()
				servicetype = "ServiceEvent"
			elif isinstance(self.source, CurrentService):  # source="session.CurrentService"
				service = self.source.getCurrentServiceRef()
				servicetype = "CurrentService"
			elif isinstance(self.source, EventInfo):  # source="session.Event_Now" or source="session.Event_Next"
				service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
				servicetype = "EventInfo"
			elif isinstance(self.source, Event):  # source="Event"
				if self.nxts:
					service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
				else:
					self.canal[0] = None
					self.canal[1] = self.source.event.getBeginTime()
					self.canal[2] = self.source.event.getEventName()
					self.canal[3] = self.source.event.getExtendedDescription()
					self.canal[4] = self.source.event.getShortDescription()
					self.canal[5] = convtext(self.canal[2], self.canal[3])  # convert to title + year
				servicetype = "Event"

			if service:
				events = epgcache.lookupEvent(['IBDCTESX', (service.toString(), 0, -1, -1)])
				self.canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
				self.canal[1] = events[self.nxts][1]
				self.canal[2] = events[self.nxts][4]
				self.canal[3] = events[self.nxts][5]
				self.canal[4] = events[self.nxts][6]
				self.canal[5] = convtext(self.canal[2], self.canal[3])  # convert to title + year
				if not autobouquet_file:
					if self.canal[0] not in apdb:
						apdb[self.canal[0]] = service.toString()
		except Exception as e:
			self.logPoster("Error (service) : " + str(e))
			self.instance.hide()
			return

		if not servicetype:
			self.logPoster("Error service type undefined")
			self.instance.hide()
			return

		try:
			curCanal = "{}-{}".format(self.canal[1], self.canal[2])
			# **if the program is the same, do not hide poster**
			if curCanal == getattr(self, "last_program", None):
				return  
			self.last_program = curCanal  # store last program
			self.oldCanal = curCanal

			self.logPoster("Service : {} [{}] : {} : {}".format(servicetype, self.nxts, self.canal[0], self.oldCanal))

			# select correct image file by the usedImage skin attribute
			subfolder = "backdrop/" if self.usedImage == "backdrop" else "poster/"
			pstrNm = path_folder + subfolder + self.canal[5] + ".jpg"

			if os.path.exists(pstrNm):
				self.timer.start(100, True)
			else:
				# **hide previous backdrop if no new has been found**
				if self.usedImage == "backdrop":
					self.instance.hide()
				canal_with_type = self.canal[:] + [self.usedImage]  # add usedImage in the list
				pdb.put(canal_with_type)
				start_new_thread(self.waitPoster, ())

		except Exception as e:
			self.logPoster("Error (eFile) : " + str(e))
			self.instance.hide()
			return

	def showPoster(self):
		if self.canal[5]:
			subfolder = "backdrop/" if self.usedImage == "backdrop" else "poster/"
			pstrNm = path_folder + subfolder + self.canal[5] + ".jpg"

			if os.path.exists(pstrNm):
				# **Check if backdrop is horizontal**
				if self.usedImage == "backdrop" and not self.is_valid_backdrop(pstrNm):
					self.logPoster(f"[ERROR : showPoster] Invalid backdrop detected, skipping: {pstrNm}")
					return  

				# **Avoid flickering: Load only when image changes**
				if getattr(self, "current_poster", None) and self.current_poster == pstrNm:
					return

				self.current_poster = pstrNm  # Store current image
				self.logPoster(f"[LOAD : showPoster] {pstrNm}")

				# **Set the image**
				self.instance.setPixmap(loadJPG(pstrNm))
				self.instance.setScale(2)
				self.instance.show()
			else:
				if self.usedImage == "backdrop":
					self.instance.hide()

	def waitPoster(self):
		self.instance.hide()
		if self.canal[5]:
			subfolder = "backdrop/" if self.usedImage == "backdrop" else "poster/"
			pstrNm = path_folder + subfolder + self.canal[5] + ".jpg"
			loop = 300
			found = None
			self.logPoster("[LOOP : waitPoster] {}".format(pstrNm))

			while loop >= 0:
				if os.path.exists(pstrNm):
					if os.path.getsize(pstrNm) > 0:
						# **check if backdrop is horizontal**
						if self.usedImage == "backdrop" and not self.is_valid_backdrop(pstrNm):
							self.logPoster("[ERROR : waitPoster] Invalid backdrop detected, skipping: {}".format(pstrNm))
							return  # hide not suitable backdrop

						loop = 0
						found = True
				time.sleep(0.6)
				loop -= 1

			if found:
				self.timer.start(10, True)

	def is_valid_backdrop(self, img_path):
		try:
			with Image.open(img_path) as img:
				width, height = img.size
				if width > height:  # image must be horizontal
					return True
				else:
					self.logPoster("[INVALID : Backdrop] Wrong dimensions for backdrop: {} ({}x{})".format(img_path, width, height))
					return False
		except Exception as e:
			self.logPoster("[ERROR : is_valid_backdrop] Failed to check image: {} ({})".format(img_path, e))
			return False

	def logPoster(self, logmsg):
		if self.logdbg:
			with open(path_folder + "GlamPosters.log", "a+") as w:
				w.write("%s\n" % logmsg)
