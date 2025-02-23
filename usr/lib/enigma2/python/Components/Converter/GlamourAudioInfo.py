#GlamourAudioInfo converter (Python 3)
#Modded and recoded by MCelliotG for use in Glamour skins or standalone, based on VAudioInfo converter
#If you use this Converter with its modifications as it is for other skins and rename it, please keep the lines above adding your credits below

from enigma import iPlayableService
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll
import re

try:
	from enigma import iAudioType_ENUMS as iAt
	AUDIO_FORMATS = {
		iAt.atDTSHD: ("DTS-HD",_("DTS-HD"), 1),
		iAt.atDTS: ("DTS", _("DTS"), 2),
		iAt.atAACHE: ("AACHE", _("HE-AAC"), 3),
		iAt.atAAC: ("AAC", _("AAC"), 4),
		iAt.atDDP: ("DDP", _("AC3+"), 5),
		iAt.atAC3: ("AC3", _("AC3"), 6),
		iAt.atMPEG: ("MPEG", _("MPEG"), 7),
		iAt.atMP3: ("MP3", _("MP3"), 8),
		iAt.atPCM: ("LPCM", _("LPCM"), 9),
		iAt.atPCM: ("PCM", _("PCM"), 10),
		iAt.atWMA: ("WMA", _("WMA"), 11),
		iAt.atFLAC: ("FLAC", _("FLAC"), 12),
		iAt.atTRUEHD: ("TRUEHD", _("TRUEHD"), 13),
		iAt.atOPUS: ("OPUS", _("OPUS"), 14),
		iAt.atAC4: ("AC4", _("AC4"), 15),
		iAt.atOGG: ("OGG", _("OGG"), 16),
		iAt.atATMOS: ("ATMOS", _("ATMOS"), 17),
		iAt.atUnknown: ("unknown", _("<unknown>"), -1)
	}
except:
	pass

class GlamourAudioInfo(Poll, Converter):
	GET_AUDIO_ICON = 0
	GET_AUDIO_CODEC = 1

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.type = type
		self.poll_interval = 1000
		self.poll_enabled = True
		self.lang_dict = {
			"ger": "Deutsch", "deu": "Deutsch", "german": "Deutsch",
			"gre": "Ελληνικά", "ell": "Ελληνικά", "greek": "Ελληνικά"
		}
		self.codecs = {
			"01_dolbydigitalplus": ("digital+", "digitalplus", "ac3+", "e-ac-3",),
			"02_dolbydigital": ("dolbyac3", "ac3", "ac-3", "dolbydigital",),
			"03_mp3": ("mp3",),
			"04_wma": ("wma",),
			"05_flac": ("flac",),
			"06_he-aac": ("he-aac",),
			"07_aac": ("aac", "mpeg-4 aac", "mpeg-4",),
			"08_lpcm": ("lpcm",),
			"09_dts-hd": ("dts-hd",),
			"10_dts": ("dts",),
			"11_pcm": ("pcm",),
			"12_mpeg": ("mpeg",),
			"13_dolbytruehd": ("truehd","dolbytruehd",),
			"14_opus": ("opus",),
			"15_dolbyac4": ("dolbyac4","ac4","ac-4",),
			"16_ogg": ("vorbis", "ogg",),
			"17_dolbyatmos": ("atmos", "doblyatmos",)
			}
		self.codec_info = {
			"dolbydigitalplus": ("51", "20", "71"),
			"dolbydigital": ("51", "20", "10", "71"),
			"wma": ("8", "9"),
		}
		self.type, self.interesting_events = {
				"AudioIcon": (self.GET_AUDIO_ICON, (iPlayableService.evUpdatedInfo,)),
				"AudioCodec": (self.GET_AUDIO_CODEC, (iPlayableService.evUpdatedInfo,)),
			}[type]

	def getAudio(self):
		service = self.source.service
		audio = service.audioTracks()
		if audio:
			self.current_track = audio.getCurrentTrack()
			self.number_of_tracks = audio.getNumberOfTracks()
			if self.number_of_tracks > 0 and self.current_track > -1:
				self.audio_info = audio.getTrackInfo(self.current_track)
				return True
		return False

	def getLanguage(self):
		languages = self.audio_info.getLanguage()
		return self.lang_dict.get(languages.lower(), languages).replace("und ", "")

	def getAudioCodec(self, info):
		description_str = _("unknown")
		if self.getAudio():
			try:
				type = AUDIO_FORMATS[self.audio_info.getType()][1];
				description_str = type
				channels = self.audio_info.getDescription();
				channels_str = re.search("([0-9\.]+)", channels)
				if channels_str:
					description_str = description_str + " " + channels_str.group(1)
			except:
				languages = self.getLanguage()
				description = self.audio_info.getDescription();
				description_str = description.split(" ")
				if len(description_str) and description_str[0] in languages:
					return languages
				if description.lower() in languages.lower():
					languages = ""
				description_str = description + " " + languages
		return description_str

	def getAudioIcon(self, info):
		description_str = self.get_short(self.getAudioCodec(info).translate(str.maketrans("", "", ' .')).lower())
		return description_str

	def get_short(self, audioName):
		for return_codec, codecs in sorted(iter(self.codecs.items())):
			for codec in codecs:
				if codec in audioName:
					codec = return_codec.split('_')[1]
					if codec in self.codec_info:
						for ex_codec in self.codec_info[codec]:
							if ex_codec in audioName:
								codec += ex_codec
								break
					return codec
		return audioName

	@cached
	def getText(self):
		service = self.source.service
		if service:
			info = service and service.info()
			if info:
				if self.type == self.GET_AUDIO_CODEC:
					return self.getAudioCodec(info)
				if self.type == self.GET_AUDIO_ICON:
					return self.getAudioIcon(info)
		return _( "Invalid type" )

	text = property(getText)


	def changed(self, what):
		if what[0] != self.CHANGED_SPECIFIC or what[1] in self.interesting_events:
			Converter.changed(self, what)
