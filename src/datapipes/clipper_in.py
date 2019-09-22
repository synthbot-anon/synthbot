import os
import re
from typing import *

import datapipes
from datapipes.fileutils import *


AUDIO_EXTENSIONS = set(['.flac', '.wav'])

CHARACTERS = {
	'A. K. Yearling': 'AK Yearling',
	'Adagio Dazzle': 'Adagio Dazzle',
	'Ahuizotl': 'Ahuizotl',
	'All Aboard': 'All Aboard',
	'Apple Bloom': 'Apple Bloom',
	'Apple Cobbler': 'Apple Cobbler',
	'Apple Rose': 'Apple Rose',
	'Applejack': 'Applejack',
	"Aria Blaze": "Aria Blaze",
	'Auntie Applesauce': 'Auntie Applesauce',
	'Autumn Blaze': 'Autumn Blaze',
	'Babs Seed': 'Babs Seed',
	'Big Bucks': 'Big Bucks',
	'Big Daddy Mccolt': 'Big Daddy Mccolt',
	'Big Mac': 'Big Macintosh',
	'Big Macintosh': 'Big Macintosh',
	'Blaze': 'Blaze',
	'Bow Hothoof': 'Bow Hothoof',
	'Boyle': 'Boyle',
	'Braeburn': 'Braeburn',
	'Bright Mac': 'Bright Mac',
	'Bulk Biceps': 'Bulk Biceps',
	'Burnt Oak': 'Burnt Oak',
	'Caballeron': 'Caballeron',
	'Cadance': 'Cadance',
	'Cadence': 'Cadance',
	'Capper': 'Capper',
	'Captain Celaeno': 'Captain Celaeno',
	'Carnival Barker': 'Carnival Barker',
	'Celestia': 'Celestia',
	'Cheerilee': 'Cheerilee',
	'Cheerlee': 'Cheerilee',
	'Cheese Sandwich': 'Cheese Sandwich',
	'Cherry Berry': 'Cherry Berry',
	'Cherry Jubilee': 'Cherry Jubilee',
	'Chiffon Swirl': 'Chiffon Swirl',
	'Chrysalis': 'Chrysalis',
	"Cinch": "Cinch",
	'Clear Skies': 'Clear Skies',
	'Cloudy Quartz': 'Cloudy Quartz',
	'Coco Pommel': 'Coco Pommel',
	'Code Red': 'Code Red',
	'Coriander Cumin': 'Coriander Cumin',
	'Countess Coloratura': 'Countess Coloratura',
	'Cozy Glow': 'Cozy Glow',
	'Cranberry Muffin': 'Cranberry Muffin',
	'Cranky': 'Cranky',
	'Daisy': 'Daisy',
	'Daring Do': 'Daring Do',
	'Daybreaker': 'Daybreaker',
	'Derpy': 'Derpy',
	'Diamond Tiara': 'Diamond Tiara',
	'Diamond Tiarra': 'Diamond Tiara',
	'Discord': 'Discord',
	'Donut Joe': 'Donut Joe',
	'Double Diamond': 'Double Diamond',
	'Dr. Caballeron': 'Dr Caballeron',
	'Dr. Hooves': 'Dr Hooves',
	'Dragon Lord Torch': 'Dragon Lord Torch',
	'Ember': 'Ember',
	'Fancy Pants': 'Fancy Pants',
	'Featherweight': 'Featherweight',
	'Female Pony 2': 'Female Pony 2',
	"Flash Sentry": "Flash Sentry",
	'Film': 'Film',
	'Filthy Rich': 'Filthy Rich',
	'Firelight': 'Firelight',
	'Flam': 'Flam',
	'Flash Magnus': 'Flash Magnus',
	'Fleetfoot': 'Fleetfoot',
	'Flim': 'Flim',
	'Flurry': 'Flurry',
	'Fluttershy': 'Fluttershy',
	'Gabby': 'Gabby',
	'Gallus': 'Gallus',
	'Gilda': 'Gilda',
	'Gladmane': 'Gladmane',
	"Gloriosa Daisy": "Gloriosa Daisy",
	'Goldgrape': 'Goldgrape',
	'Goldie Delicious': 'Goldie Delicious',
	'Grampa Gruff': 'Grampa Gruff',
	'Grand Pear': 'Grand Pear',
	'Granny Smith': 'Granny Smith',
	'Grany Smith': 'Granny Smith',
	'Grubber': 'Grubber',
	'Gustave Le Grand': 'Gustave Le Grand',
	'High Winds': 'High Winds',
	'Hoity Toity': 'Hoity Toity',
	'Hoo\'far': 'Hoofar',
	'Igneous': 'Igneous',
	'Iron Will': 'Iron Will',
	'Jack Pot': 'Jack Pot',
	'Lemon Hearts': 'Lemon Hearts',
	'Lightning Dust': 'Lightning Dust',
	'Lily Valley': 'Lily Valley',
	'Limestone': 'Limestone',
	'Lix Spittle': 'Lix Spittle',
	'Louise': 'Louise',
	'Luggage Cart': 'Luggage Cart',
	'Luna': 'Luna',
	'Lyra Heartstrings': 'Lyra Heartstrings',
	'Lyra': 'Lyra Heartstrings',
	'Ma Hooffield': 'Ma Hooffield',
	'Mane-iac': 'Mane-iac',
	'Marble': 'Marble',
	'Matilda': 'Matilda',
	'Maud': 'Maud',
	'Mayor Mare': 'Mayor Mare',
	'Meadowbrook': 'Meadowbrook',
	'Mean Applejack': 'Mean Applejack',
	'Mean Fluttershy': 'Mean Fluttershy',
	'Mean Pinkie Pie': 'Mean Pinkie Pie',
	'Mean Rainbow Dash': 'Mean Rainbow Dash',
	'Mean Rarity': 'Mean Rarity',
	'Mean Twilight Sparkle': 'Mean Twilight Sparkle',
	"Micro Chips": "Micro Chips",
	"Midnight Sparkle": "Midnight Sparkle",
	'Minuette': 'Minuette',
	'Miss Harshwhinny': 'Miss Harshwhinny',
	'Mistmane': 'Mistmane',
	'Misty Fly': 'Misty Fly',
	'Moon Dancer': 'Moon Dancer',
	'Mori': 'Mori',
	'Mr Cake': 'Mr Cake',
	'Mr. Cake': 'Mr Cake',
	'Mr. Shy': 'Mr Shy',
	'Mrs Cake': 'Mrs Cake',
	'Mrs. Cake': 'Mrs Cake',
	'Mrs. Shy': 'Mrs Shy',
	'Mudbriar': 'Mudbriar',
	'Mulia Mild': 'Mulia Mild',
	'Mullet': 'Mullet',
	'Multiple': 'Multiple',
	'Neighsay': 'Neighsay',
	'Night Glider': 'Night Glider',
	'Night Light': 'Night Light',
	'Nightmare Moon': 'Nightmare Moon',
	'Ocean Flow': 'Ocean Flow',
	'Ocellus': 'Ocellus',
	'Octavia': 'Octavia',
	'On Stage': 'On Stage',
	'Party Favor': 'Party Favor',
	'Pear Butter': 'Pear Butter',
	'Pharynx': 'Pharynx',
	'Photo Finish': 'Photo Finish',
	'Photographer': 'Photographer',
	'Pig Creature 1': 'Pig Creature 1',
	'Pig Creature 2': 'Pig Creature 2',
	'Pinkie': 'Pinkie Pie',
	'Pipsqueak': 'Pipsqueak',
	'Pony Of Shadows': 'Pony Of Shadows',
	'Prince Rutherford': 'Prince Rutherford',
	'Princess Cadance': 'Cadance',
	'Princess Skystar': 'Skystar',
	'Pursey Pink': 'Pursey Pink',
	'Pushkin': 'Pushkin',
	'Queen Novo': 'Queen Novo',
	'Quibble Pants': 'Quibble Pants',
	'Rachel Platten': 'Rachel Platten',
	'Rain Shine': 'Rain Shine',
	'Rainbow': 'Rainbow Dash',
	'Rarity': 'Rarity',
	'Raspberry Beret': 'Raspberry Beret',
	'Rockhoof': 'Rockhoof',
	'Rolling Thunder': 'Rolling Thunder',
	'Rose': 'Rose',
	'Rumble': 'Rumble',
	'S04e26 Unnamed Earth Mare #1': 'S04e26 Unnamed Earth Mare #1',
	'Saffron Masala': 'Saffron Masala',
	"Sandalwood": "Sandalwood",
	'Sandbar': 'Sandbar',
	'Sapphire Shores': 'Sapphire Shores',
	'Sassy Saddles': 'Sassy Saddles',
	'Scootaloo': 'Scootaloo',
	'Seaspray': 'Seaspray',
	'Shining Armor': 'Shining Armor',
	'Short Fuse': 'Short Fuse',
	'Silver Spoon': 'Silver Spoon',
	'Silverstream': 'Silverstream',
	'Sky Beak': 'Sky Beak',
	'Sky Stinger': 'Sky Stinger',
	'Sludge': 'Sludge',
	'Smolder': 'Smolder',
	'Snails': 'Snails',
	'Snips': 'Snips',
	'Soarin': 'Soarin',
	'Sombra': 'Sombra',
	'Somnambula': 'Somnambula',
	"Sonata Dusk": "Sonata Dusk",
	'Songbird Serenade': 'Songbird Serenade',
	'Spike': 'Spike',
	'Spitfire': 'Spitfire',
	'Spoiled Rich': 'Spoiled Rich',
	'Star Swirl': 'Star Swirl',
	'Starlight': 'Starlight',
	'Stellar Flare': 'Stellar Flare',
	'Steve': 'Steve',
	'Storm Creature': 'Storm Creature',
	'Stormy Flare': 'Stormy Flare',
	'Stygian': 'Stygian',
	'Sugar Belle': 'Sugar Belle',
	'Sunburst': 'Sunburst',
	"Sunset Shimmer": "Sunset Shimmer",
	'Surprise': 'Surprise',
	'Svengallop': 'Svengallop',
	'Sweetie Belle': 'Sweetie Belle',
	'Sweetie Drops': 'Sweetie Drops',
	'Tempest Shadow': 'Tempest Shadow',
	'Terramar': 'Terramar',
	'The Storm King': 'The Storm King',
	'Thorax': 'Thorax',
	'Thunderlane': 'Thunderlane',
	'Tight End': 'Tight End',
	"Timber Spruce": "Timber Spruce",
	'Tirek': 'Tirek',
	'Toothy Klugetowner': 'Toothy Klugetowner',
	'Tourist Pony': 'Tourist Pony',
	'Tree Hugger': 'Tree Hugger',
	'Tree Of Harmony': 'Tree Of Harmony',
	'Trixie': 'Trixie',
	'Trouble Shoes': 'Trouble Shoes',
	'Twilight Velvet': 'Twilight Velvet',
	'Twilight': 'Twilight Sparkle',
	'Twinkleshine': 'Twinkleshine',
	'Twist': 'Twist',
	'Vapor Trail': 'Vapor Trail',
	'Vendor 2': 'Vendor 2',
	'Vera': 'Vera',
	'Verko': 'Verko',
	"Vignette": "Vignette",
	'Vinny': 'Vinny',
	'Whinnyfield': 'Whinnyfield',
	'Wind Rider': 'Wind Rider',
	'Windy Whistles': 'Windy Whistles',
	'Yona': 'Yona',
	'Zecora': 'Zecora',
	'Zephyr': 'Zephyr',
	'Zesty Gourmand': 'Zesty Gourmand',
}

TAGS = [
	'Amused',
	'Angry',
	'Annoyed',
	'Anxious',
	'Bored',
	'Canterlot Voice',
	'Confused',
	'Crazy',
	'Curious',
	'Disgust',
	'Dizzy',
	'Excited',
	'Exhausted',
	'Fear',
	'Happy',
	'Laughing',
	'Love',
	'Muffled',
	'Nervous',
	'Neutral',
	'Sad',
	'Sarcastic',
	'Serious',
	'Shouting',
	'Singing',
	'Smug',
	'Surprised',
	'Tired',
	'Whining',
	'Whispering'
]
_tag_regex = '|'.join(TAGS)

NOISE = {
	'': '',
	'Clean': '',
	'Noisy': 'Noisy',
	'Very Noisy': 'Very Noisy'
}

class ClipperLabelSet(LocalFiles):
	def __init__(self, path: str):
		LocalFiles.__init__(self, get_directory(path))

	def _accept_path(self, path: str):
		return get_name(path) in ('labels.txt', 'fim_movie.txt')

	def _wrap_path(self, path: str):
		return ClipperLabels(path)

	def collect(self):
		result = {}
		for file in self.get_files():
			result.update(file.labels)

		return result

def remove_non_ascii(text):
	return re.sub(r'[^\x00-\x7f]', '', text)

def audio_name_from_label_line(line: str, known_paths):
	label = line.split('\t')[-1].strip()
	base = re.sub(r'[?]', '_', label)
	base = remove_non_ascii(base)
	
	if base not in known_paths:
		return base

	duplicate_count = 1
	modified = base
	while modified in known_paths:
		duplicate_count += 1
		modified = '{}-{}'.format(base, duplicate_count)

	return modified	

def _parse_label(line):
	start, end, label = line.split('\t')
	
	label_parts = label.split('_')
	# skip hh_mm_ss
	assert re.match(r'[0-9][0-9]', label_parts[0])
	assert re.match(r'[0-9][0-9]', label_parts[1])
	assert re.match(r'[0-9][0-9]', label_parts[2])

	# get character name
	character_key = label_parts[3]
	assert character_key in CHARACTERS, \
		'Missing character {} in clipper_in.CHARACTERS for {}'.format(character_key, line)
	character = CHARACTERS[character_key]

	# get tags
	tags = re.findall(_tag_regex, label_parts[4])
	assert label_parts[4] == ' '.join(tags), \
		'Something wrong with the tags in {}'.format(line.strip())

	# noise level
	noise_level = label_parts[5]
	assert noise_level in NOISE, \
		'Missing noise tag {} in clipper_in.NOISE for {}'.format(noise_level, line)

	# get transcript
	transcript = label_parts[6].strip()
	assert len(label_parts) == 7, \
		'Excess label parts in {}'.format(line.strip())
	
	return {
		'start': start,
		'end': end,
		'character': character,
		'tags': tags,
		'noise': noise_level,
		'transcript': transcript
	}

class ClipperLabels:
	def __init__(self, path: str):
		self.path = path
		self.labels = {}
		for line in open(path).readlines():
			try:
				audio_name = audio_name_from_label_line(line, self.labels)
				label = _parse_label(line)
				
				assert audio_name not in self.labels
				self.labels[audio_name] = label

			except AssertionError as e:
				if not datapipes.__dry_run__:
					raise e
				print(e)

class ClipperDataset(LocalFiles):
	def __init__(self, path: str):
		LocalFiles.__init__(self, path)

		if datapipes.__verbose__:
			print('reading transcipts and labels from labels.text files')

		self.labels = ClipperLabelSet(path).collect()

	def _accept_path(self, path: str):
		return os.path.splitext(path)[-1].lower() in AUDIO_EXTENSIONS

	def _wrap_path(self, path: str):
		audio_name = get_name(os.path.splitext(path)[0])
		audio_name = remove_non_ascii(audio_name)

		if audio_name not in self.labels and '{}.'.format(audio_name) in self.labels:
			audio_name = '{}.'.format(audio_name)

		assert audio_name in self.labels, \
			'Missing audio name {} in labels'.format(audio_name)

		return ClipperFile(path, self.labels[audio_name])

def episode_from_path(path: str):
	episode_directory = get_name(get_directory(path))
	return episode_directory

class ClipperFile:
	def __init__(self, audio_path: str, label: dict):
		base_filename = os.path.splitext(audio_path)[0]
		self.audio_path = audio_path
		self.label = label
		self.episode = episode_from_path(audio_path)
		self.reference = normalize_path('{}-{}-{}-{}'.format(
			self.label['character'],
			self.episode, 
			self.label['start'],
			self.label['end']))
