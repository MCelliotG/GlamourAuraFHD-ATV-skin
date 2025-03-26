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
import unicodedata
import time
import socket
import requests
import threading
from PIL import Image
import math

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
tvmaze_api = "-5Xwuu84at4GqV7byoNMO5DFqBtPpm8i"
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

# Define main path
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

ROMAN_TO_INT = {
	"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5", "VI": "6", "VII": "7", "VIII": "8",
	"IX": "9", "X": "10", "XI": "11", "XII": "12", "XIII": "13", "XIV": "14", "XV": "15",
	"XVI": "16", "XVII": "17", "XVIII": "18", "XIX": "19", "XX": "20",
	"XXI": "21", "XXII": "22", "XXIII": "23", "XXIV": "24", "XXV": "25",
	"XXVI": "26", "XXVII": "27", "XXVIII": "28", "XXIX": "29", "XXX": "30",
	"XL": "40", "L": "50", "LX": "60", "LXX": "70", "LXXX": "80", "XC": "90", "C": "100"
}

def replace_roman(match):
	roman = match.group(0)
	return ROMAN_TO_INT.get(roman, roman)

REGEX = re.compile(
	r'\s*\*\d{4}\Z|'  # removes ( *1234)
	r'\[K\d+\]\s*|'  # removes [Κ12], [Κ16] etc.
	r'([\(\[]).*?([\)\]])|'  # removes content within brackets
	r'(\.\s{1,}\").+|'  # removes (. "xxx)
	r'(\?\s{1,}\").+|'  # removes (? "xxx)
	r'(\.{2,}\Z)|'  # removes ".." at the string ends
	r'(\s*-\s*)?\b(\d+ος\sΚύκλος|\d+η\sΚύκλος|Κύκλος\s\d+|Κύκλος\s[IVXLCDM]+|[IVXLCDM]+\'?\sΚύκλος|[Α-ΩA-Z]+\'?\sΚύκλος)\b'  # removes "- 4ος Κύκλος", "Κύκλος IV", "Δ' Κύκλος"
	r'|(\s*-\s*)?\b(\d+[ης]?\sΣεζόν|Σεζόν\s\d+|Σεζόν\s(?:[IVXLCDM]+)|(?:[IVXLCDM]+)\sΣεζόν)\b'  # removes "- 1η Σεζόν", "Σεζόν 7"
	r'|\b[SEKΤτΕεΚκ]\d+\s?[ΕεEe]?\d*\b'  # removes "K5 E7", "S4 E6", "E47" παντού
	r'|(: odc.\d+)|'
	r'(\d+: odc.\d+)|'
	r'(\d+ odc.\d+)|(:)|'
	r'(?<=\S)\s*-\s*(?=\S)|' # replaces - with space
	r'(,)|' # removes commas
	r'!|'
	r'/.*|' # removes anything after "/"
	r'\|\s[0-9]+\+|'
	r'[0-9]+\+|'
	r'\"|:|' # removes quotes and colons
	r'Πpremьера\.\s|' # removes russian words
	r'\s*$', # remove trailing spaces if there are any
	re.DOTALL
)

def convtext(text, fulldesc=""):
	text = text.replace('\xc2\x86', '').replace('\xc2\x87', '')
	text = REGEX.sub(' ', text)  # add space
	text = re.sub(r'\s{2,}', ' ', text).strip() # clean double spaces
	text = re.sub(r'\b(I{1,3}|IV|V|VI{0,3}|IX|X{1,3}|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|XXX|XL|L|LX|LXX|LXXX|XC|C)\b(?!$)', replace_roman, text)
	text = re.sub(r'\b(I{1,3}|IV|V|VI{0,3}|IX|X{1,3}|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|XXX|XL|L|LX|LXX|LXXX|XC|C)\b$', '', text).strip() # replace roman at the end
	text = re.sub(r'\b(Dr|Mr|Ms|Prof|J)\.\s+', r'\1 ', text, flags=re.IGNORECASE) #remove space from Mr Ms Dr etc
	text = re.sub(r'(\b\w+)\.\s(\d{4})', r'\1 \2', text) # remove redundant .
	text = re.sub(r'[«»]', '', text) #removes «»
	return text.lower()

def convert_to_greeklish(text):
	if not text:
		return text

	greek_to_greeklish = {
		'α': 'a', 'ά': 'a', 'β': 'v', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'έ': 'e',
		'ζ': 'z', 'η': 'i', 'ή': 'i', 'θ': 'th', 'ι': 'i', 'ί': 'i', 'ϊ': 'i',
		'ΐ': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o',
		'ό': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y',
		'ύ': 'y', 'ϋ': 'y', 'ΰ': 'y', 'φ': 'f', 'χ': 'h', 'ψ': 'ps', 'ω': 'o',
		'ώ': 'o', 'Α': 'A', 'Ά': 'A', 'Β': 'V', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E',
		'Έ': 'E', 'Ζ': 'Z', 'Η': 'I', 'Ή': 'I', 'Θ': 'Th', 'Ι': 'I', 'Ί': 'I',
		'Ϊ': 'I', 'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O',
		'Ό': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Ύ': 'Y',
		'Ϋ': 'Y', 'Φ': 'F', 'Χ': 'H', 'Ψ': 'Ps', 'Ω': 'O', 'Ώ': 'O'
	}
	diphthongs = {
		'ου': 'ou', 'ού': 'ou',
		'αυ': 'au', 'αύ': 'au',
		'ευ': 'eu', 'εύ': 'eu',
		'οϋ': 'oy', 'οΰ': 'oy',
		'εϋ': 'ey', 'εΰ': 'ey',
		'αϋ': 'ay', 'αΰ': 'ay'
	}
	greeklish_text = []
	i = 0
	while i < len(text):
		if i + 1 < len(text):
			diphthong = text[i] + text[i + 1]
			if diphthong in diphthongs:
				greeklish_text.append(diphthongs[diphthong])
				i += 2
				continue
		greeklish_text.append(greek_to_greeklish.get(text[i], text[i]))
		i += 1

	return ''.join(greeklish_text)

pdb = queue.LifoQueue()

def image_postprocessing(img_path, image_type):
	try:
		if not os.path.exists(img_path):
			log_to_file(f"CVI: [ERROR] Image does not exist: {img_path}")
			return False

		# Open image and log initial info
		with Image.open(img_path) as img:
			log_to_file(f"CVI: [PROCESSING] Image: {img_path}")
			log_to_file(f"CVI: Original size: {img.size} | Format: {img.format} | Mode: {img.mode}")

			# Verify JPEG format
			if img.format != "JPEG":
				log_to_file(f"CVI: [ERROR] Invalid format: {img.format} (Expected JPEG)")
				return False

			original_size = img.size
			original_mode = img.mode

			# Define target dimensions
			if image_type == "poster":
				target_w, target_h = 300, 450
			else:
				target_w, target_h = 1280, 720

			target_ratio = target_w / target_h
			current_ratio = img.width / img.height

			log_to_file(f"CVI: Target ratio: {target_ratio:.2f} | Current ratio: {current_ratio:.2f}")

			# Only process if ratio mismatch
			if not math.isclose(current_ratio, target_ratio, rel_tol=0.01):
				log_to_file("CVI: Aspect ratio differs - cropping...")
		
				if current_ratio > target_ratio:  # Too wide
					new_width = int(img.height * target_ratio)
					offset = (img.width - new_width) // 2
					img = img.crop((offset, 0, offset + new_width, img.height))
				else:  # Too tall
					new_height = int(img.width / target_ratio)
					offset = (img.height - new_height) // 2
					img = img.crop((0, offset, img.width, offset + new_height))

				log_to_file(f"CVI: After cropping: {img.size}")

				# Resize to target dimensions
				img = img.resize((target_w, target_h), Image.LANCZOS)
				log_to_file(f"CVI: After resizing: {img.size}")

				# Preserve original mode (especially for CMYK->RGB conversion)
				if img.mode != original_mode:
					img = img.convert(original_mode)

				# Save with quality=95 and EXIF removal
				img.save(img_path, "JPEG", quality=95, subsampling=0, exif=b'')
				log_to_file(f"CVI: [SUCCESS] Image processed and saved: {img_path}")
				return True
			else:
				log_to_file("CVI: Aspect ratio matches - no processing needed")
				return True

	except Exception as e:
		log_to_file(f"CVI: [ERROR] Processing failed: {str(e)}")
		if os.path.exists(img_path):
			try:
				os.remove(img_path)
				log_to_file(f"CVI: Removed corrupted file: {img_path}")
			except:
				pass
		return False

# Global flags
debug_enabled = True
operational_logs_enabled = True

def log_to_file(logmsg, log_type="operational"):
	log_path = "/tmp/GlamPosters.log"
	# Size check
	if operational_logs_enabled and os.path.exists(log_path) and os.path.getsize(log_path) >= 2 * 1024 * 1024:  # 2MB
		try:
			with open(log_path, "w") as f:
				f.write("")
			logmsg = "[LOG] Log file cleared (reached 2MB).\n" + logmsg
		except Exception as e:
			print(f"[ERROR] Failed to clear log file: {e}")
	if (log_type == "debug" and debug_enabled) or (log_type == "operational" and operational_logs_enabled):
		try:
			with open(log_path, "a+") as f:
				f.write(f"{logmsg}\n")
		except Exception as e:
			print(f"[ERROR] Failed to write log: {e}")

class PostersDB(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.logdbg = debug_enabled
		self.checkMovie = [
		# 🎬 Movies
		"cine", "cinema", "cinéma", "film", "filme", "kino", "movie", "película", "ξένη ταινία",
		"σινεμά", "ταινία", "ταινίες", "κινηματογραφική ταινία", "κινηματογράφος", "φιλμ", "кино", "фильм",
		# 🎭 Genres
		"abenteuer", "acción", "action", "adventure", "aventura", "comedia", "comedy", "comédie", "drama", "drame",
		"fantasía", "fantasie", "fantastique", "fantasy", "misterio", "mystère", "mystery", "suspenso", "terror", "thriller", "western",
		"γουέστερν", "δράμα", "δράση", "θρίλερ", "κωμωδία", "κομεντί", "μυστήριο", "περιπέτεια", "τρόμου",
		"боевик", "драма", "детектив", "комедия", "приключение", "триллер", "ужасы", "вестерн", "фэнтези"
		]
		self.checkTV = [
		# 📺 Series
		"tv", "feuilleton", "fernsehserie", "series", "sitcom", "soap opera", "série", "telenovela", "tv series", "tv show", "αισθηματική σειρά", "καθημερινή", "καθημερινό",
		"δραματική σειρά", "κωμική σειρά", "κωμωδία αυτοτελών επεισοδίων", "καθημερινή σειρά", "σειρά", "τηλεοπτική σειρά", "σόου", "сериал", "теленовелла", "телесериал",
		# 📢 Episodes/Seasons
		"ep.", "episode", "episodio", "épisode", "folge", "s.", "saison", "season", "staffel", "t.", "temporada", "αυτοτελή",
		"επεισόδιο", "επ.", "κ.", "κύκλος", "σεζόν", "σαιζόν", "м/с", "с-н", "сериал", "серия", "сезон", "т/с", "эпизод", "эпизод",
		# 🎨 Animation/Reality/Documentaries
		"animation", "animación", "anime", "cartoon", "caricatura", "dessin animé", "documentaire", "documental", "documentary", "dokumentation", "reality", "realidad",
		"reality-show", "téléréalité", "άνιμε", "κινούμενα σχέδια", "κινουμένων σχεδίων", "καρτούν", "ντοκιμαντέρ", "ριάλιτι", "анимация", "аниме", "мультфильм", "документальный", "реалити",
		# 📰 News/Information
		"actualité", "aktuell", "current affairs", "información", "infotainment", "journal", "nachrichten", "ζωντανή", "πρωινή", "τηλεπωλήσεις", "Θυρίδα τηλεπώλησης", "ενημερωτικό ένθετο",
		"news", "noticias", "ειδήσεις", "δελτίο", "κεντρικό δελτίο", "δελτίο ειδήσεων", "μεσημβρινό δελτίο ειδήσεων", "ενημέρωση", "ενημερωτική εκπομπή", "ινφοτέιντμεντ", "новости", "информация",
		# 🎤 Talk Shows/Magazines
		"entrevista", "magazine", "magazin", "revista", "talk show", "talkshow", "πρωινό", "ψυχαγωγικό μαγκαζίνο",
		"μαγκαζίνο", "συζήτηση", "συνέντευξη", "τοκ σόου", "журнал", "ток-шоу",
		# 🎭 Entertainment
		"concurso", "divertissement", "entertainment", "entretenimiento", "game show", "jeu télévisé", "quizsendung", "unterhaltung", "σάτιρα", "μαγειρική", "εκπομπή μαγειρικής",
		"variedad", "varieté", "varieties", "variété", "ποικιλία", "τηλεπαιχνίδι", "ψυχαγωγία", "ψυχαγωγική εκπομπή", "варьете", "игровое шоу", "развлекательное шоу",
		# 🎼 Music
		"clips", "concert", "concierto", "klip", "konzert", "music", "musique", "música", "videoclips",
		"βιντεοκλίπ", "κλιπ", "μουσική", "συναυλία", "клипы", "концерт", "музыка",
		# 🏆 Sports
		"athletics", "athlétisme", "atletismo", "baloncesto", "basket", "basketball", "basketbol", "deportes", "football", "fútbol", "fußball",
		"leichtathletik", "sports","αθλητικά", "ζωντανά", "ζωντανή", "ζωντανή μετάδοση", "απευθείας", "μπάσκετ", "ποδόσφαιρο", "στίβος", "баскетбол", "легкая атлетика", "спорт", "футбол",
		# 🌦️ Weather
		"clima", "météo", "weather", "wetter", "καιρός", "δελτίο καιρού", "погода",
		# 📚 Education/Health/Society
		"bildung", "culture", "cultura", "education", "educación", "gesellschaft", "gesundheit", "health", "kultur", "santé", "sociedad", "society",
		"εκπαίδευση", "επικαιρότητα", "κοινωνία", "πολιτισμός", "υγεία", "образование", "здоровье", "общество", "культура", "παιδικό πρόγραμμα", "νεανικό πρόγραμμα"
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
				self.search_tmdb, self.search_tvdb, self.search_fanart,
				self.search_imdb, self.search_filmy, self.search_tvmaze, self.search_impawards
			]

			# Search and store image functions (google searches)
			google_searches = [
				self.search_molotov_google, self.search_google
			]
			found = False

			for search_function in search_functions:
				if not os.path.exists(dwn_image):
					try:
						val, log = search_function(dwn_image, cleaned_title, canal[4], canal[3], usedImage, canal[0])
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
						val, log = google_search(dwn_image, cleaned_title, canal[4], canal[3], usedImage, canal[0])
						if val:
							print(f"GlamPosters: [SUCCESS] Found image using {google_search.__name__}")
							found = True
							break
				except Exception as e:
					print(f"GlamPosters: [ERROR] {google_search.__name__} failed: {str(e)}")
					self.logDB(f"[ERROR] {google_search.__name__} failed: {str(e)}")

			pdb.task_done()

	def logDB(self, logmsg, log_type="operational"):
		if (log_type == "debug" and self.logdbg) or (log_type == "operational" and operational_logs_enabled):
			log_to_file(logmsg, log_type)

# TMDB Search
	@lru_cache(maxsize=500)
	def search_tmdb(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			url_image = None
			# Extact year from fulldesc
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fulldesc)
			year = year_matches[0] if year_matches else None
			# Extract alternative titles (AKA) from fulldesc
			aka_matches = re.findall(r'\[(.*?)\]|\((.*?)\)', fulldesc)
			aka = None
			for match in aka_matches:
				# Επιλέγουμε τον πρώτο μη κενό τίτλο από τις αγκύλες ή παρενθέσεις
				if match[0]:
					aka = match[0]
					break
				elif match[1]:
					aka = match[1]
					break
			# Check if AKA is in a different language
			if aka and self.is_different_language(title, aka):
				log_to_file(f"[DEBUG : tmdb] Found alternative title: {aka}")
			else:
				aka = None  # Ignore AKA if it is in the same language
			# Define type (movie or series)
			chkType, fd = self.checkType(shortdesc, fulldesc)
			srch = "multi" if chkType == "" else "movie" if chkType.startswith("movie") else "tv"

			url_tmdb = f"https://api.themoviedb.org/3/search/{srch}?api_key={tmdb_api}&query={quote(title)}&include_adult=false"
			if year:
				url_tmdb += f"&year={year}"
			# Sync with GUI language
			if lng:
				try:
					language, region = lng.split('_')  # Χωρίζουμε το lng σε language και region
					url_tmdb += f"&language={language}"
					url_tmdb += f"&region={region}"
				except ValueError:
					language = lng
					url_tmdb += f"&language={language}"

			response = requests.get(url_tmdb, timeout=10)
			if response.status_code != 200:
				return False, f"[ERROR : tmdb] {title} [{chkType}-{year}] => {url_tmdb} (HTTP {response.status_code})"

			data = response.json()
			if data and data.get('results'):
				# Choose best title by vote_average and aka
				results = data['results']
				best_result = None
				best_score = 0

				for result in results:
					score = result.get('vote_average', 0)
					# Title based score
					if title.lower() == result.get("title", result.get("name", "")).lower():
						score += 10
					elif aka and aka.lower() == result.get("title", result.get("name", "")).lower():
						score += 5
					# Year based score
					if year and result.get("release_date", result.get("first_air_date", "")):
						result_year = result["release_date"][:4] if result.get("release_date") else result["first_air_date"][:4]
						if result_year == year:
							score += 5
					# Update best score
					if score > best_score:
						best_result = result
						best_score = score
				# Use first score if no other is found
				if not best_result:
					best_result = results[0]
				# Choose suitable image type
				if usedImage == "poster" and best_result.get('poster_path'):
					url_image = f"https://image.tmdb.org/t/p/w{isz_poster.split(',')[0]}{best_result['poster_path']}"
				elif usedImage == "backdrop" and best_result.get('backdrop_path'):
					url_image = f"https://image.tmdb.org/t/p/w{isz_backdrop.split(',')[0]}{best_result['backdrop_path']}"
				else:
					# If poster is not found, search for images from episodes (for series)
					if srch == "tv" and best_result.get("id"):
						episodes_url = f"https://api.themoviedb.org/3/tv/{best_result['id']}/images?api_key={tmdb_api}"
						episodes_response = requests.get(episodes_url, timeout=10)
						if episodes_response.status_code == 200:
							episodes_data = episodes_response.json()
							if episodes_data.get("stills"):
								url_image = f"https://image.tmdb.org/t/p/w{isz_poster.split(',')[0]}{episodes_data['stills'][0]['file_path']}"
				# Store image
				if url_image:
					self.saveImage(dwn_image, url_image, usedImage)
					return True, f"[SUCCESS : tmdb] {title} [{chkType}-{year}] => {url_tmdb} => {url_image}"
				else:
					return False, f"[SKIP : tmdb] {title} [{chkType}-{year}] => {url_tmdb} (No image found)"
			else:
				return False, f"[SKIP : tmdb] {title} [{chkType}-{year}] => {url_tmdb} (No results found)"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[ERROR : tmdb] {title} [{chkType}-{year}] => {url_tmdb} ({str(e)})"

# TVDB Search
	@lru_cache(maxsize=500)
	def search_tvdb(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			# Extract year from fulldesc
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fulldesc)
			year = year_matches[0] if year_matches else None

			# Extract alternative titles (AKA) from fulldesc
			aka_matches = re.findall(r'\((.*?)\)', fulldesc)
			aka = aka_matches[0] if aka_matches else None

			# Define the API endpoint with your API key
			url_tvdb = f"https://thetvdb.com/api/GetSeries.php?seriesname={quote(title)}"
			# Add language if available
			if lng:
				try:
					language, region = lng.split('_')  # Χωρίζουμε το lng σε language και region
					headers = {'Accept-Language': language}
				except ValueError: 
					language = lng
					headers = {'Accept-Language': language}
			else:
				headers = {'Accept-Language': 'en'}  # Default to English if no language is set

			response = requests.get(url_tvdb, headers=headers, timeout=5)
			if response.status_code != 200:
				return False, f"[ERROR : tvdb] {title} => {url_tvdb} (HTTP {response.status_code})"

			url_read = response.text

			# Extract data with variable regex
			try:
				series_id = re.findall(r'<seriesid>(.*?)</seriesid>', url_read)
				series_name = re.findall(r'<SeriesName>(.*?)</SeriesName>', url_read)
				series_year = re.findall(r'<FirstAired>(\d{4})-\d{2}-\d{2}</FirstAired>', url_read)
				series_aliases = re.findall(r'<Alias>(.*?)</Alias>', url_read)
			except Exception as e:
				return False, f"[ERROR : tvdb] Failed parsing response: {str(e)}"

			# Clean title with UNAC
			series_nb = -1
			ptitle = self.UNAC(title)
			paka = self.UNAC(aka) if aka else ""

			for i, (s_id, s_name, s_year, s_aliases) in enumerate(zip(series_id, series_name, series_year, series_aliases)):
				clean_s_name = self.UNAC(s_name)
				clean_s_aliases = [self.UNAC(alias) for alias in s_aliases.split('|')] if s_aliases else []

				# Score based on title match
				title_score = self.PMATCH(ptitle, clean_s_name)
				aka_score = max([self.PMATCH(paka, alias) for alias in clean_s_aliases]) if paka else 0
				total_score = max(title_score, aka_score)
		
				# Score based on year match
				if year and s_year == year:
					total_score += 50

				# Update best result if current result has a higher score
				if total_score > 50:  # Minimum score threshold
					series_nb = i
					break

			if series_nb >= 0:
				selected_id = series_id[series_nb]
				selected_name = series_name[series_nb]
				selected_year = series_year[series_nb]
				# URL creation (v4 API)
				url_tvdb_images = f"https://thetvdb.com/api/{tvdb_api}/series/{selected_id}/images/query?keyType={usedImage}"
				response_images = requests.get(url_tvdb_images, headers=headers, timeout=5)

				if response_images.status_code == 200:
					data = response_images.json()
					if data['data']:
						# Choose first available image
						url_image = data['data'][0]['fileName']
						url_image = f"https://artworks.thetvdb.com{url_image}"
						self.saveImage(dwn_image, url_image, usedImage)
						return True, f"[SUCCESS : tvdb] {title} => Found '{selected_name}' ({selected_year}), URL: {url_image}"
			return False, f"[SKIP : tvdb] {title} (No matching series found)"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[ERROR : tvdb] {title} ({str(e)})"

# Fanart Search
	@lru_cache(maxsize=500)
	def search_fanart(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			# Title conversion
			title = convtext(title)
			title = convert_to_greeklish(title)
			# Check if the content is a movie using checkMovie list
			chkType, fd = self.checkType(shortdesc, fulldesc)
			if not chkType.startswith("movie"):
				return False, f"[SKIP : fanart] {title} (Not a movie, skipping Fanart.tv)"
			# searching IMDb ID from OMDB
			url_omdb = f"https://www.omdbapi.com/?t={quote(title)}&apikey={omdb_api}"
			response = requests.get(url_omdb).json()
			imdb_id = response.get("imdbID")
			# If no IMDb ID from OMDB, try TMDb
			if not imdb_id:
				url_tmdb = f"https://api.themoviedb.org/3/search/movie?api_key={tmdb_api}&query={quote(title)}"
				response_tmdb = requests.get(url_tmdb, timeout=10)
				if response_tmdb.status_code == 200:
					data_tmdb = response_tmdb.json()
					if data_tmdb.get('results'):
						best_result = max(data_tmdb['results'], key=lambda x: x.get('vote_average', 0))
						imdb_id = best_result.get("imdb_id")
	
			if not imdb_id:
				return False, f"[SKIP : fanart] {title} (No IMDb ID found)"
			# searching Fanart.tv
			url_fanart = f"https://webservice.fanart.tv/v3/movies/{imdb_id}?api_key={fanart_api}"
			response = requests.get(url_fanart, timeout=5).json()
			# select correct image type by the usedImage skin attribute
			url_image = None
			if usedImage == "poster" and "movieposter" in response and response["movieposter"]:
				url_image = response["movieposter"][0]["url"]
			elif usedImage == "backdrop" and "moviebackground" in response and response["moviebackground"]:
				url_image = response["moviebackground"][0]["url"]
			# store image
			if url_image:
				self.saveImage(dwn_image, url_image, usedImage)
				return True, f"[SUCCESS : fanart] {title} => {url_image}"
			else:
				return False, f"[SKIP : fanart] {title} (No image found)"

		except Exception as e:
			return False, f"[ERROR : fanart] {title} ({str(e)})"

#IMDB Search
	@lru_cache(maxsize=500)
	def search_imdb(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			# Convert to greeklish 
			title = convtext(title)
			title = convert_to_greeklish(title)
			# Extract year from fulldesc
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fulldesc)
			year = year_matches[0] if year_matches else None
			# Extract alternative titles (AKA) from fulldesc
			aka_matches = re.findall(r'\((.*?)\)', fulldesc)
			aka = aka_matches[0] if aka_matches else None
			# Define type (movie or series)
			chkType, fd = self.checkType(shortdesc, fulldesc)
			# Create search URL
			url_mimdb = f"https://m.imdb.com/find?q={quote(title)}"
			if aka and aka != title:
				url_mimdb += f"%20({quote(aka)})"

			if lng:
				try:
					language, region = lng.split('_')  # Χωρίζουμε το lng σε language και region
					url_mimdb += f"&language={language}"
				except ValueError:
					language = lng
					url_mimdb += f"&language={language}"
	
			headers = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
			}
			# Make the request
			response = requests.get(url_mimdb, headers=headers, timeout=10)
			if response.status_code != 200:
				return False, f"[ERROR : imdb] {title} => {url_mimdb} (HTTP {response.status_code})"
			# Extract data from IMDb
			url_read = response.text
			rc = re.compile(r'<img src="(.*?)".*?<span class="h3">\n(.*?)\n</span>.*?\((\d+)\)(\s\(.*?\))?(.*?)</a>', re.DOTALL)
			url_imdb = rc.findall(url_read)
			# If no results found, retry with aka
			if not url_imdb and aka:
				url_mimdb = f"https://m.imdb.com/find?q={quote(title)}"
				response = requests.get(url_mimdb, headers=headers, timeout=10)
				url_read = response.text
				url_imdb = rc.findall(url_read)

			len_imdb = len(url_imdb)
			idx_imdb = 0
			pfound = False
			url_image = None
			# Check results
			for imdb in url_imdb:
				imdb = list(imdb)
				imdb[1] = self.UNAC(imdb[1])  # Καθαρισμός τίτλου
				imdb[4] = self.UNAC(re.findall(r'aka <i>"(.*?)"</i>', imdb[4])[0]) if re.findall(r'aka <i>"(.*?)"</i>', imdb[4]) else ""
				# image URL extraction
				imdb_image = re.search(r"(.*?)._V1_.*?.jpg", imdb[0])
				if imdb_image:
					# year matching
					if year and year == imdb[2]:
						url_image = f"{imdb_image.group(1)}._V1_UY278,1,185,278_AL_.jpg" if usedImage == "poster" else f"{imdb_image.group(1)}._V1_UX1920,1,1080,1920_AL_.jpg"
						pfound = True
					elif not url_image and (int(year) - 1 == int(imdb[2]) or int(year) + 1 == int(imdb[2])):
						url_image = f"{imdb_image.group(1)}._V1_UY278,1,185,278_AL_.jpg" if usedImage == "poster" else f"{imdb_image.group(1)}._V1_UX1920,1,1080,1920_AL_.jpg"
						pfound = True
					elif not year:
						url_image = f"{imdb_image.group(1)}._V1_UY278,1,185,278_AL_.jpg" if usedImage == "poster" else f"{imdb_image.group(1)}._V1_UX1920,1,1080,1920_AL_.jpg"
						pfound = True

					if pfound:
						break

				idx_imdb += 1
			# store image if found
			if url_image and pfound:
				self.saveImage(dwn_image, url_image, usedImage)
				return True, f"[SUCCESS : imdb] {title} [{chkType}-{year}] => Found '{imdb[1]}' ({imdb[2]}), URL: {url_image}"
			else:
				return False, f"[SKIP : imdb] {title} [{chkType}-{year}] => {url_mimdb} (No Entry found [{len_imdb}])"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[ERROR : imdb] {title} [{chkType}-{year}] => {url_mimdb} ({str(e)})"

#Filmy Search
	@lru_cache(maxsize=500)
	def search_filmy(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			# Check type
			chkType, fd = self.checkType(shortdesc, fulldesc)
			if chkType.startswith("tv"):
				return False, f"[SKIP : filmy.gr] {title} (TV show detected, skipping filmy.gr)"
			# Year extraction from fulldesc
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fulldesc)
			year = year_matches[0] if year_matches else None
			# Create URL
			search_query = quote(title)  # Κωδικοποίηση του τίτλου για το URL
			url_filmy = f"https://www.filmy.gr/?s={search_query}&post_type=amy_movie&amy_type=movie"
			# Add year if available
			if year:
				url_filmy += f"&year={year}"

			headers = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
			}

			response = requests.get(url_filmy, headers=headers, timeout=10)
			if response.status_code != 200:
				return False, f"[ERROR : filmy.gr] {title} => {url_filmy} (HTTP {response.status_code})"
			# Extract titles and images from HTML response
			result_pattern = re.compile(r'<img[^>]+src="([^">]+)"[^>]+alt="([^">]+)"')
			matches = result_pattern.findall(response.text)

			if not matches:
				return False, f"[SKIP : filmy.gr] {title} (No results found)"
			# Choose best image by year and score
			best_image = None
			best_score = 0

			for image_url, image_title in matches:
				# Calculate score with PMATCH
				score = self.PMATCH(title, image_title)
				# Add score for year if available
				if year and year in image_title:
					score += 50

				if score > best_score:
					best_score = score
					best_image = image_url

			if best_image:
				self.saveImage(dwn_image, best_image, usedImage)
				return True, f"[SUCCESS : filmy.gr] {title} => {best_image} (Score: {best_score})"
			else:
				return False, f"[SKIP : filmy.gr] {title} (No suitable image found)"

		except Exception as e:
			return False, f"[ERROR : filmy.gr] {title} ({str(e)})"

#IMPAwards Search
	@lru_cache(maxsize=500)
	def search_impawards(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			title = convert_to_greeklish(title)
			# Check type
			chkType, fd = self.checkType(shortdesc, fulldesc)
			if not chkType.startswith("movie"):
				return False, f"[SKIP : impawards] {title} (Not a movie, skipping IMPAwards)"
			# Extract year
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fulldesc)
			year = year_matches[0] if year_matches else None
			# Clean the title for URL
			def clean_title_for_url(title):
				title = re.sub(r'[^a-zA-Z0-9]', '_', title)
				title = re.sub(r'_+', '_', title)
				title = title.strip('_').lower()
				return title
			# Generate possible URLs based on title and year
			possible_urls = []
			if year:
				base_url = f"http://www.impawards.com/{year}/{clean_title_for_url(title)}"
				possible_urls.append(f"{base_url}.html")  # Check version alternatives
				possible_urls.append(f"{base_url}_ver1.html")
				possible_urls.append(f"{base_url}_ver2.html")
				possible_urls.append(f"{base_url}_ver3.html")
			else:
				# If no year, try the last 5 years
				current_year = datetime.datetime.now().year
				for y in range(current_year, current_year - 5, -1):
					base_url = f"http://www.impawards.com/{y}/{clean_title_for_url(title)}"
					possible_urls.append(f"{base_url}.html")  # Basic URL
					possible_urls.append(f"{base_url}_ver1.html")
					possible_urls.append(f"{base_url}_ver2.html")
					possible_urls.append(f"{base_url}_ver3.html")
			# Headers for the request
			headers = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
			}
			# Try each possible URL
			poster_url = None
			best_score = 0
			for url in possible_urls:
				response = requests.get(url, headers=headers, timeout=10)
				if response.status_code == 200:
					# Extract the poster URL using regex
					html_content = response.text
					poster_url_match = re.search(r'<img src="(.*?)".*?class="poster"', html_content, re.DOTALL)
					if poster_url_match:
						poster_url_candidate = poster_url_match.group(1)
						if not poster_url_candidate.startswith('http'):
							poster_url_candidate = f"http://www.impawards.com{poster_url_candidate}"
						# PMATCH
						score = self.PMATCH(title, poster_url_candidate)
						if score > best_score:
							best_score = score
							poster_url = poster_url_candidate
			# If no poster found, return
			if not poster_url:
				return False, f"[SKIP : impawards] {title} (No poster found)"
			# Save the image
			self.saveImage(dwn_image, poster_url, usedImage)
			return True, f"[SUCCESS : impawards] {title} => {poster_url} (Score: {best_score})"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[ERROR : impawards] {title} ({str(e)})"

# TVMaze Search
	@lru_cache(maxsize=500)
	def search_tvmaze(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel=None):
		try:
			# Check type if it is TV
			chkType, fd = self.checkType(shortdesc, fulldesc)
			if chkType.startswith("movie"):
				return False, f"[SKIP : tvmaze] {title} (Movie detected, skipping TVmaze)"
			# Extract year
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fulldesc)
			year = year_matches[0] if year_matches else None
			# Extract language and country
			language = None
			country = None
			if lng:
				try:
					language, country = lng.split('_', 1)  # Split μόνο στην πρώτη '_'
				except ValueError:
					language = lng
			# Create URL
			url = f"https://api.tvmaze.com/search/shows?q={quote(title)}&exact=true"
			# Add language and country if they exist
			if country:
				url += f"&country={country}"
			if language:
				url += f"&language={language}"
			headers = {"Authorization": f"Bearer {tvmaze_api}"}
			# Request procedure
			response = requests.get(url, headers=headers, timeout=10)
			if response.status_code != 200:
				return False, f"[ERROR : tvmaze] {title} => {url} (HTTP {response.status_code})"

			data = response.json()
			if data:
				best_result = None
				best_score = 0
		
				for result in data:
					show = result["show"]
					current_score = 0
					# Title based choice (PMATCH)
					current_score += self.PMATCH(title, show.get("name", ""))
					# Year based score if exists
					if year and show.get("premiered"):
						show_year = show["premiered"][:4]
						if show_year == year:
							current_score += 50
					# Choose best score
					if current_score > best_score:
						best_score = current_score
						best_result = show
				# Choose imaage
				if best_result and best_result.get("image"):
					url_image = best_result["image"]["original"]
					self.saveImage(dwn_image, url_image, usedImage)
					return True, f"[SUCCESS : tvmaze] {title} => {url_image} (Score: {best_score})"
		
				return False, f"[SKIP : tvmaze] {title} (No valid image found)"
	
			return False, f"[SKIP : tvmaze] {title} (No results)"

		except Exception as e:
			return False, f"[ERROR : tvmaze] {title} ({str(e)})"

# Molotov Search
	@lru_cache(maxsize=500)
	def search_molotov_google(self, dwn_image, title, shortdesc, fulldesc, usedImage, channel):
		try:
			# Check for French location (fr_FR)
			if lng != "fr_FR":
				return False, f"[SKIP : molotov-google] {title} (Only available for France, lng={lng})"
	
			headers = {
				"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
			}
			# Convert title
			ptitle = self.UNAC(title)
			pchannel = self.UNAC(channel).replace(" ", "") if channel else ""
			# Create URL
			url_mgoo = f"site:molotov.tv+{quote(title)}"
			if channel and title.find(channel.split()[0]) < 0:
				url_mgoo += f"+{quote(channel)}"
			url_mgoo = f"https://www.google.com/search?q={url_mgoo}&tbm=isch"
			# Request
			response = requests.get(url_mgoo, stream=True, headers=headers, timeout=5).text
			# Extract image
			plst = re.findall(r'https://www.molotov.tv/(.*?)"(?:.*?)?"(.*?)"', response)
			if not plst:
				return False, f"[SKIP : molotov-google] {title} (No results found)"
			# Choose best image
			best_image = None
			best_score = 0
			for molotov_id, pl in enumerate(plst):
				get_path = f"https://www.molotov.tv/{pl[0]}"
				get_name = self.UNAC(pl[1])
				# Score calculation
				partialtitle = 100 if get_name == ptitle else self.PMATCH(ptitle, get_name)
				partialchannel = 100 if pchannel == "" else self.PMATCH(pchannel, get_name)

				if partialtitle > best_score:
					best_score = partialtitle
					best_image = get_path
	
			if best_image:
				self.saveImage(dwn_image, best_image, usedImage)
				return True, f"[SUCCESS : molotov-google] {title} => {best_image}"
			else:
				return False, f"[SKIP : molotov-google] {title} (No suitable image found)"

		except Exception as e:
			return False, f"[ERROR : molotov-google] {title} ({str(e)})"

#Google Search
	@lru_cache(maxsize=500)
	def search_google(self, dwn_image, title, shortdesc, fulldesc, usedImage, canal_name):
		try:
			headers = {
				"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
			}
			# Type check
			chkType, fd = self.checkType(shortdesc, fulldesc)
			# Extract year from fulldesc
			year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', fulldesc)
			year = year_matches[0] if year_matches else None
			# Extract original title from fulldesc
			original_title = None
			original_title_matches = re.findall(r'\[(.*?)\]', fulldesc)
			if original_title_matches:
				candidate = original_title_matches[0]
				# Check original title for different language
				if self.is_different_language(title, candidate):
					original_title = candidate
					log_to_file(f"[DEBUG : google] Original title found: {original_title}")
			# Clean title
			title = re.sub(r'\([^)]*\)', '', title).strip()
			# Check for none channel
			if not canal_name:
				canal_name = ""
				log_to_file(f"[DEBUG : google] Canal name is None or empty")
			else:
				canal_name = self.UNAC(canal_name)
				log_to_file(f"[DEBUG : google] Cleaned canal name: {canal_name}")
			# Log usedImage
			log_to_file(f"[DEBUG : google] Used image type: {usedImage}")
			# Check correct usedImage
			if usedImage not in ["poster", "backdrop"]:
				log_to_file(f"[ERROR : google] Invalid usedImage value: {usedImage}")
				return False, f"[ERROR : google] Invalid usedImage value: {usedImage}"
			# Use original title if checktype is TV
			if chkType.startswith("tv") and original_title:
				search_query = quote(self.UNAC(original_title))  # Χρήση του original τίτλου
				log_to_file(f"[INFO : google] Using original title for search: {original_title}")
			else:
				# Use EPG title if original title does not exist
				search_query = quote(self.UNAC(title))  # Χρήση του τίτλου από το EPG
				if canal_name and chkType.startswith("tv"):  # Προσθήκη του canal_name μόνο για τύπου "tv"
					search_query += f" {quote(canal_name)}"
				log_to_file(f"[INFO : google] Using EPG title for search: {title}")
			# Add year
			if year:
				search_query += f" {year}"
				log_to_file(f"[INFO : google] Adding year to search: {year}")
			# Check for correct aspect ratio
			if usedImage == "poster":
				aspect_ratio = "t|s"  # tall or square
				log_to_file(f"[INFO : google] Searching for poster using aspect ratios: t or s")
			else:
				aspect_ratio = "w|xw"  # wide or extra wide
				log_to_file(f"[INFO : google] Searching for backdrop using aspect ratios: w or xw")
			# URL quote
			google_url = f"https://www.google.com/search?as_st=y&as_q={search_query}&as_epq=&as_oq=&as_eq=&imgar={aspect_ratio}&imgcolor=&imgtype=&cr=&as_sitesearch=&as_filetype=jpg&tbs=&udm=2"

			log_to_file(f"[INFO : google] Searching: {google_url}")
			response = requests.get(google_url, headers=headers, timeout=10).text
			# Extract image URL
			image_list = re.findall(r'\],\["https://(.*?)",\d+,\d+]', response)
			# Choose first valid image
			for img_url in image_list:
				img_url = f"https://{img_url}"
				# Avoid logo and newspapers
				if "logo" in img_url.lower() or "channel" in img_url.lower() or "newspaper" in img_url.lower():
					log_to_file(f"[DEBUG : google] Skipping potential logo or newspaper: {img_url}")
					continue
				# Save image
				self.saveImage(dwn_image, img_url, usedImage)
				if self.verifyImage(dwn_image):
					log_to_file(f"[SUCCESS : google] Found image: {img_url}")
					return True, f"[SUCCESS : google] {title} [{chkType}-{year}] => {google_url} => {img_url}"
			# If no results try with channel name
			if canal_name and chkType.startswith("tv"):
				search_query = quote(f"{self.UNAC(title)} {canal_name} {year if year else ''}".strip())
				google_url = f"https://www.google.com/search?as_st=y&as_q={search_query}&as_epq=&as_oq=&as_eq=&imgar={aspect_ratio}&imgcolor=&imgtype=&cr=&as_sitesearch=&as_filetype=jpg&tbs=&udm=2"

				log_to_file(f"[INFO : google] Retrying with channel name: {google_url}")
				response = requests.get(google_url, headers=headers, timeout=10).text
				image_list = re.findall(r'\],\["https://(.*?)",\d+,\d+]', response)

				for img_url in image_list:
					img_url = f"https://{img_url}"
					if "logo" in img_url.lower() or "channel" in img_url.lower():
						log_to_file(f"[DEBUG : google] Skipping potential logo: {img_url}")
						continue

					self.saveImage(dwn_image, img_url, usedImage)
					if self.verifyImage(dwn_image):
						log_to_file(f"[SUCCESS : google] Found image: {img_url}")
						return True, f"[SUCCESS : google] {title} [{chkType}-{year}] => {google_url} => {img_url}"
			# Return fail if not succeeded
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			return False, f"[SKIP : google] {title} [{chkType}-{year}] => No results found"

		except Exception as e:
			if os.path.exists(dwn_image):
				os.remove(dwn_image)
			error_msg = f"[ERROR : google] {title} [{chkType}-{year}] ({str(e)})"
			log_to_file(error_msg)
			return False, error_msg

	def is_different_language(self, title, candidate):
		if re.search(r'[a-zA-Z]', candidate):
			return True
		return False

	def create_valid_image(self, img_path, image_type):
		return image_postprocessing(img_path, image_type)

	def saveImage(self, dwn_image, url_image, image_type):
		if os.path.exists(dwn_image) and os.path.getsize(dwn_image) > 0:
			return True
		try:
			# Download image
			response = requests.get(url_image, stream=True, allow_redirects=True, verify=False)
			if response.status_code != 200:
				log_to_file(f"[ERROR] Failed to download image: {url_image} (HTTP {response.status_code})")
				return False

			with open(dwn_image, 'wb') as f:
				f.write(response.content)
				f.close()

			# Verify image before processing
			if not self.verifyImage(dwn_image):
				log_to_file(f"[ERROR] Invalid image file: {dwn_image}")
				os.remove(dwn_image)
				return False
			# Process image
			if not self.create_valid_image(dwn_image, image_type):
				log_to_file(f"[ERROR] Failed to process image: {dwn_image}")
				os.remove(dwn_image)  # Αφαιρούμε την εικόνα αν η επεξεργασία αποτύχει
				return False
			return True
		except Exception as e:
			log_to_file(f"[ERROR] Failed to save image: {dwn_image} ({e})")
			return False

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
		if string is None:
			return ""

		# Remove umlats etc
		string = unicodedata.normalize('NFKD', string)
		string = ''.join(c for c in string if not unicodedata.combining(c))
		# replace special characters and HD from channel names
		string = re.sub(r'\s+HD\b', '', string, flags=re.IGNORECASE)
		string = re.sub(u"u0026", "&", string)
		string = re.sub(r"[-,!/\.\":]", " ", string)
		# replace diacritics with plain latin characters
		translit_map = {
			u"[ÀÁÂÃÄàáâãäåª]": 'a', u"[ÈÉÊËèéêë]": 'e', u"[ÍÌÎÏìíîï]": 'i',
			u"[ÒÓÔÕÖòóôõöº]": 'o', u"[ÙÚÛÜùúûü]": 'u', u"[Ññ]": 'n',
			u"[Çç]": 'c', u"[Ÿýÿ]": 'y',
			# Add non latin chars (π.χ. ρώσικα)
			u"[Аа]": 'a', u"[Бб]": 'b', u"[Вв]": 'v', u"[Гг]": 'g', u"[Дд]": 'd',
			u"[Ее]": 'e', u"[Ёё]": 'yo', u"[Жж]": 'zh', u"[Зз]": 'z', u"[Ии]": 'i',
			u"[Йй]": 'y', u"[Кк]": 'k', u"[Лл]": 'l', u"[Мм]": 'm', u"[Нн]": 'n',
			u"[Оо]": 'o', u"[Пп]": 'p', u"[Рр]": 'r', u"[Сс]": 's', u"[Тт]": 't',
			u"[Уу]": 'u', u"[Фф]": 'f', u"[Хх]": 'kh', u"[Цц]": 'ts', u"[Чч]": 'ch',
			u"[Шш]": 'sh', u"[Щщ]": 'shch', u"[Ъъ]": '', u"[Ыы]": 'y', u"[Ьь]": '',
			u"[Ээ]": 'e', u"[Юю]": 'yu', u"[Яя]": 'ya',
		}
		for pattern, replacement in translit_map.items():
			string = re.sub(pattern, replacement, string)

		# keep only English, Greek, Cyrillic, and numbers
		string = re.sub(r"[^a-zA-Zα-ωΑ-Ωа-яА-Я0-9 ']", "", string)
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
		self.logdbg = debug_enabled

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

								# Search and store image functions (without google searches)
								search_functions = [
									self.search_tmdb, self.search_tvdb, self.search_fanart,
									self.search_imdb, self.search_filmy, self.search_tvmaze, self.search_impawards
								]

								# Search and store image functions (google searches)
								google_searches = [
									self.search_molotov_google, self.search_google
								]
								found = False

								for search_function in search_functions:
									if not os.path.exists(dwn_image):
										val, log = search_function(dwn_image, canal[5], canal[4], canal[3], usedImage)
										self.logAutoDB(log)
										if val:
											found = True
											newfd += 1
											break

								if not found:
									for google_search in google_searches:
										if not os.path.exists(dwn_image):
											val, log = google_search(dwn_image, canal[5], canal[0], canal[4], canal[3], usedImage)
											self.logAutoDB(log)
											if val:
												newfd += 1
												break

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
				if diff_tm > 120 and os.path.getsize(path_folder + f) == 0:  # scan empty files > 2 minutes
					os.remove(path_folder + f)
					emptyfd += 1
				if diff_tm > 259200:  # scan old files > 3 days
					os.remove(path_folder + f)
					oldfd += 1
			self.logAutoDB("[AutoDB] {} old file(s) removed".format(oldfd))
			self.logAutoDB("[AutoDB] {} empty file(s) removed".format(emptyfd))
			self.logAutoDB("[AutoDB] *** Stopping ***")

	def logAutoDB(self, logmsg, log_type="operational"):
		if (log_type == "debug" and self.logdbg) or (log_type == "operational" and operational_logs_enabled):
			log_to_file(logmsg, log_type)

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
					self.canal = [None, None, None, None, None, None]  # Initialize canal list with 6 elements
					self.canal[1] = self.source.event.getBeginTime()
					self.canal[2] = self.source.event.getEventName()
					self.canal[3] = self.source.event.getExtendedDescription()
					self.canal[4] = self.source.event.getShortDescription()
					self.canal[5] = convtext(self.canal[2], self.canal[3])  # convert to title + year
				servicetype = "Event"

			if service:
				events = epgcache.lookupEvent(['IBDCTESX', (service.toString(), 0, -1, -1)])
				if events and len(events) > self.nxts:  # Check if events list is not empty and has enough elements
					self.canal = [None, None, None, None, None, None]  # Initialize canal list with 6 elements
					self.canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').replace(' HD','')
					self.canal[1] = events[self.nxts][1]
					self.canal[2] = events[self.nxts][4]
					self.canal[3] = events[self.nxts][5]
					self.canal[4] = events[self.nxts][6]
					self.canal[5] = convtext(self.canal[2], self.canal[3])  # convert to title + year
					if not autobouquet_file:
						if self.canal[0] not in apdb:
							apdb[self.canal[0]] = service.toString()
				else:
					self.logPoster("Error: No events found for service")
					self.instance.hide()
					return
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
				self.instance.hide()
				canal_with_type = self.canal[:] + [self.usedImage]  # add usedImage in the list
		
				# Έλεγχος αν το canal_with_type υπάρχει ήδη στο queue
				if canal_with_type not in list(pdb.queue):
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
				# Avoid flickering: Load only when image changes
				if getattr(self, "current_poster", None) and self.current_poster == pstrNm:
					return

				self.current_poster = pstrNm  # Store current image
				if self.usedImage == "poster":
					self.logPoster(f"[LOAD : showPoster] {pstrNm}")
				else:
					self.logPoster(f"[LOAD : showBackdrop] {pstrNm}")

				# Set the image
				self.instance.setPixmap(loadJPG(pstrNm))
				self.instance.setScale(2)
				self.instance.show()
			else:
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
						loop = 0
						found = True
				time.sleep(0.6)
				loop -= 1

			if found:
				self.timer.start(10, True)

	def logPoster(self, logmsg):
		log_to_file(logmsg)
