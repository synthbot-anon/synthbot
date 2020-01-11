import json
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
    'Aunt Holiday': 'Aunt Holiday',
    'Auntie Applesauce': 'Auntie Applesauce',
    'Auntie Lofty': 'Auntie Lofty',
    'Autumn Blaze': 'Autumn Blaze',
    'Babs Seed': 'Babs Seed',
    'Big Bucks': 'Big Bucks',
    'Big Daddy Mccolt': 'Big Daddy Mccolt',
    'Big Mac': 'Big Macintosh',
    'Big Macintosh': 'Big Macintosh',
    'Biscuit': 'Biscuit',
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
    'Canter Zoom': 'Canter Zoom',
    'Capper': 'Capper',
    'Captain Celaeno': 'Captain Celaeno',
    'Carnival Barker': 'Carnival Barker',
    'Celestia': 'Celestia',
    'Cheerilee': 'Cheerilee',
    'Cheerlee': 'Cheerilee',
    'Cheese Sandwich': 'Cheese Sandwich',
    'Cherry Berry': 'Cherry Berry',
    'Cherry Jubilee': 'Cherry Jubilee',
    'Chestnut Magnifico': 'Chestnut Magnifico',
    'Chiffon Swirl': 'Chiffon Swirl',
    'Chrysalis': 'Chrysalis',
    "Cinch": "Cinch",
    'Clear Skies': 'Clear Skies',
    'Clear Sky': 'Clear Sky',
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
    'Dr. Caballeron': 'Caballeron',
    'Dr. Fauna': 'Dr Fauna',
    'Dr. Hooves': 'Dr Hooves',
    'Dragon Lord Torch': 'Dragon Lord Torch',
    'Ember': 'Ember',
    'Fancy Pants': 'Fancy Pants',
    'Featherweight': 'Featherweight',
    'Female Pony 2': 'Female Pony 2',
    "Flash Sentry": "Flash Sentry",
    'Filthy Rich': 'Filthy Rich',
    'Firelight': 'Firelight',
    'Flam': 'Flam',
    'Flash Magnus': 'Flash Magnus',
    'Fleetfoot': 'Fleetfoot',
    'Flim': 'Flim',
    'Flurry': 'Flurry Heart',
    'Flurry Heart': 'Flurry Heart',
    'Fluttershy': 'Fluttershy',
    'Gabby': 'Gabby',
    'Gallus': 'Gallus',
    'Garble': 'Garble',
    'Gilda': 'Gilda',
    'Gladmane': 'Gladmane',
    "Gloriosa Daisy": "Gloriosa Daisy",
    'Goldgrape': 'Goldgrape',
    'Goldie Delicious': 'Goldie Delicious',
    'Grampa Gruff': 'Grampa Gruff',
    'Grand Pear': 'Grand Pear',
    'Granny Smith': 'Granny Smith',
    'Grogar': 'Grogar',
    'Grubber': 'Grubber',
    'Gustave Le Grand': 'Gustave Le Grand',
    'High Winds': 'High Winds',
    'Hoity Toity': 'Hoity Toity',
    'Hoo\'far': 'Hoofar',
    'Horsey': 'Horsey',
    'Igneous': 'Igneous',
    'Iron Will': 'Iron Will',
    'Jack Pot': 'Jack Pot',
    'Juniper Montage': 'Juniper Montage',
    'Lemon Hearts': 'Lemon Hearts',
    'Lemon Zest': 'Lemon Zest',
    'Lighthoof': 'Lighthoof',
    'Lightning Dust': 'Lightning Dust',
    'Lily Valley': 'Lily Valley',
    'Limestone': 'Limestone',
    'Lix Spittle': 'Lix Spittle',
    'Louise': 'Louise',
    'Luggage Cart': 'Luggage Cart',
    'Luna': 'Luna',
    'Luster Dawn': 'Luster Dawn',
    'Lyra Heartstrings': 'Lyra Heartstrings',
    'Lyra': 'Lyra Heartstrings',
    'Ma Hooffield': 'Ma Hooffield',
    'Mane-iac': 'Mane-iac',
    'Marble': 'Marble',
    'Matilda': 'Matilda',
    'Mane Allgood': 'Mane Allgood',
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
    'Nurse Redheart': 'Nurse Redheart',
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
    'Sans Smirk': 'Sans Smirk',
    'Sapphire Shores': 'Sapphire Shores',
    'Sassy Saddles': 'Sassy Saddles',
    'Scootaloo': 'Scootaloo',
    'Seaspray': 'Seaspray',
    'Shimmy Shake': 'Shimmy Shake',
    'Shining Armor': 'Shining Armor',
    'Short Fuse': 'Short Fuse',
    'Silver Spoon': 'Silver Spoon',
    'Silverstream': 'Silverstream',
    'Skeedaddle': 'Skeedaddle',
    'Sky Beak': 'Sky Beak',
    'Sky Stinger': 'Sky Stinger',
    'Sludge': 'Sludge',
    'Smolder': 'Smolder',
    'Snails': 'Snails',
    'Snap Shutter': 'Snap Shutter',
    'Snips': 'Snips',
    'Soarin': 'Soarin',
    'Sombra': 'Sombra',
    'Somnambula': 'Somnambula',
    "Sonata Dusk": "Sonata Dusk",
    'Songbird Serenade': 'Songbird Serenade',
    'Sour Sweet': 'Sour Sweet',
    'Spike': 'Spike',
    'Spitfire': 'Spitfire',
    'Spoiled Rich': 'Spoiled Rich',
    'Spur': 'Spur',
    'Star Swirl': 'Star Swirl',
    'Starlight': 'Starlight',
    'Stellar Flare': 'Stellar Flare',
    'Steve': 'Steve',
    'Storm Creature': 'Storm Creature',
    'Stormy Flare': 'Stormy Flare',
    'Stygian': 'Stygian',
    'Sugar Belle': 'Sugar Belle',
    'Sugarcoat': 'Sugarcoat',
    'Sunburst': 'Sunburst',
    'Sunny Flare': 'Sunny Flare',
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
    'Wallflower': 'Wallflower',
    'Whinnyfield': 'Whinnyfield',
    'Wind Rider': 'Wind Rider',
    'Wind Sprint': 'Wind Sprint',
    'Windy Whistles': 'Windy Whistles',
    'Yona': 'Yona',
    'Young Granny Smith': 'Young Granny Smith',
    'Zecora': 'Zecora',
    'Zephyr': 'Zephyr',
    'Zesty Gourmand': 'Zesty Gourmand',
}

TAGS = {
    'Amused': 'Amused',
    'Angry': 'Angry',
    'Annoyed': 'Annoyed',
    'Anxious': 'Anxious',
    'Bored': 'Bored',
    'Canterlot Voice': 'Canterlot Voice',
    'Confused': 'Confused',
    'Crazy': 'Crazy',
    'Curious': 'Curious',
    'Disgust': 'Disgust',
    'Dizzy': 'Dizzy',
    'Excited': 'Excited',
    'Exhausted': 'Exhausted',
    'Fear': 'Fear',
    'Happy': 'Happy',
    'Laughing': 'Laughing',
    'Love': 'Love',
    'Muffled': 'Muffled',
    'Nervous': 'Nervous',
    'Neutral': 'Neutral',
    'Sad': 'Sad',
    'Sarcastic': 'Sarcastic',
    'Serious': 'Serious',
    'Shouting': 'Shouting',
    'Singing': 'Singing',
    'Smug': 'Smug',
    'Surprised': 'Surprised',
    'Tired': 'Tired',
    'Whining': 'Whining',
    'Whispering': 'Whispering',
    'amused': 'Amused',
    'angry': 'Angry',
    'annoyed': 'Annoyed',
    'anxious': 'Anxious',
    'bored': 'Bored',
    'canterlot voice': 'Canterlot Voice',
    'confused': 'Confused',
    'crazy': 'Crazy',
    'curious': 'Curious',
    'disgust': 'Disgust',
    'dizzy': 'Dizzy',
    'excited': 'Excited',
    'exhausted': 'Exhausted',
    'fear': 'Fear',
    'happy': 'Happy',
    'laughing': 'Laughing',
    'love': 'Love',
    'muffled': 'Muffled',
    'nervous': 'Nervous',
    'neutral': 'Neutral',
    'sad': 'Sad',
    'sarcastic': 'Sarcastic',
    'serious': 'Serious',
    'shouting': 'Shouting',
    'singing': 'Singing',
    'smug': 'Smug',
    'surprised': 'Surprised',
    'tired': 'Tired',
    'whining': 'Whining',
    'whispering': 'Whispering',
}
_tag_regex = '|'.join(TAGS.keys())

NOISE = {
    '': '',
    'Clean': '',
    'clean': '',
    'Noisy': 'Noisy',
    'noisy': 'Noisy',
    'Very Noisy': 'Very Noisy',
    'verynoisy': 'Very Noisy',
}

EPISODES = {
    's1e1': 'fim:s1e1',
    's1e2': 'fim:s1e2',
    's1e3': 'fim:s1e3',
    's1e4': 'fim:s1e4',
    's1e5': 'fim:s1e5',
    's1e6': 'fim:s1e6',
    's1e7': 'fim:s1e7',
    's1e8': 'fim:s1e8',
    's1e9': 'fim:s1e9',
    's1e10': 'fim:s1e10',
    's1e11': 'fim:s1e11',
    's1e12': 'fim:s1e12',
    's1e13': 'fim:s1e13',
    's1e14': 'fim:s1e14',
    's1e15': 'fim:s1e15',
    's1e16': 'fim:s1e16',
    's1e17': 'fim:s1e17',
    's1e18': 'fim:s1e18',
    's1e19': 'fim:s1e19',
    's1e20': 'fim:s1e20',
    's1e21': 'fim:s1e21',
    's1e22': 'fim:s1e22',
    's1e23': 'fim:s1e23',
    's1e24': 'fim:s1e24',
    's1e25': 'fim:s1e25',
    's1e26': 'fim:s1e26',
    's2e1': 'fim:s2e1',
    's2e2': 'fim:s2e2',
    's2e3': 'fim:s2e3',
    's2e4': 'fim:s2e4',
    's2e5': 'fim:s2e5',
    's2e6': 'fim:s2e6',
    's2e7': 'fim:s2e7',
    's2e8': 'fim:s2e8',
    's2e9': 'fim:s2e9',
    's2e10': 'fim:s2e10',
    's2e11': 'fim:s2e11',
    's2e12': 'fim:s2e12',
    's2e13': 'fim:s2e13',
    's2e14': 'fim:s2e14',
    's2e15': 'fim:s2e15',
    's2e16': 'fim:s2e16',
    's2e17': 'fim:s2e17',
    's2e18': 'fim:s2e18',
    's2e19': 'fim:s2e19',
    's2e20': 'fim:s2e20',
    's2e21': 'fim:s2e21',
    's2e22': 'fim:s2e22',
    's2e23': 'fim:s2e23',
    's2e24': 'fim:s2e24',
    's2e25': 'fim:s2e25',
    's2e26': 'fim:s2e26',
    's3e1': 'fim:s3e1',
    's3e2': 'fim:s3e2',
    's3e3': 'fim:s3e3',
    's3e4': 'fim:s3e4',
    's3e5': 'fim:s3e5',
    's3e6': 'fim:s3e6',
    's3e7': 'fim:s3e7',
    's3e8': 'fim:s3e8',
    's3e9': 'fim:s3e9',
    's3e10': 'fim:s3e10',
    's3e11': 'fim:s3e11',
    's3e12': 'fim:s3e12',
    's3e13': 'fim:s3e13',
    's4e1': 'fim:s4e1',
    's4e2': 'fim:s4e2',
    's4e3': 'fim:s4e3',
    's4e4': 'fim:s4e4',
    's4e5': 'fim:s4e5',
    's4e6': 'fim:s4e6',
    's4e7': 'fim:s4e7',
    's4e8': 'fim:s4e8',
    's4e9': 'fim:s4e9',
    's4e10': 'fim:s4e10',
    's4e11': 'fim:s4e11',
    's4e12': 'fim:s4e12',
    's4e13': 'fim:s4e13',
    's4e14': 'fim:s4e14',
    's4e15': 'fim:s4e15',
    's4e16': 'fim:s4e16',
    's4e17': 'fim:s4e17',
    's4e18': 'fim:s4e18',
    's4e19': 'fim:s4e19',
    's4e20': 'fim:s4e20',
    's4e21': 'fim:s4e21',
    's4e22': 'fim:s4e22',
    's4e23': 'fim:s4e23',
    's4e24': 'fim:s4e24',
    's4e25': 'fim:s4e25',
    's4e26': 'fim:s4e26',
    's5e1': 'fim:s5e1',
    's5e2': 'fim:s5e2',
    's5e3': 'fim:s5e3',
    's5e4': 'fim:s5e4',
    's5e5': 'fim:s5e5',
    's5e6': 'fim:s5e6',
    's5e7': 'fim:s5e7',
    's5e8': 'fim:s5e8',
    's5e9': 'fim:s5e9',
    's5e10': 'fim:s5e10',
    's5e11': 'fim:s5e11',
    's5e12': 'fim:s5e12',
    's5e13': 'fim:s5e13',
    's5e14': 'fim:s5e14',
    's5e15': 'fim:s5e15',
    's5e16': 'fim:s5e16',
    's5e17': 'fim:s5e17',
    's5e18': 'fim:s5e18',
    's5e19': 'fim:s5e19',
    's5e20': 'fim:s5e20',
    's5e21': 'fim:s5e21',
    's5e22': 'fim:s5e22',
    's5e23': 'fim:s5e23',
    's5e24': 'fim:s5e24',
    's5e25': 'fim:s5e25',
    's5e26': 'fim:s5e26',
    's6e1': 'fim:s6e1',
    's6e2': 'fim:s6e2',
    's6e3': 'fim:s6e3',
    's6e4': 'fim:s6e4',
    's6e5': 'fim:s6e5',
    's6e6': 'fim:s6e6',
    's6e7': 'fim:s6e7',
    's6e8': 'fim:s6e8',
    's6e9': 'fim:s6e9',
    's6e10': 'fim:s6e10',
    's6e11': 'fim:s6e11',
    's6e12': 'fim:s6e12',
    's6e13': 'fim:s6e13',
    's6e14': 'fim:s6e14',
    's6e15': 'fim:s6e15',
    's6e16': 'fim:s6e16',
    's6e17': 'fim:s6e17',
    's6e18': 'fim:s6e18',
    's6e19': 'fim:s6e19',
    's6e20': 'fim:s6e20',
    's6e21': 'fim:s6e21',
    's6e22': 'fim:s6e22',
    's6e23': 'fim:s6e23',
    's6e24': 'fim:s6e24',
    's6e25': 'fim:s6e25',
    's6e26': 'fim:s6e26',
    's7e1': 'fim:s7e1',
    's7e2': 'fim:s7e2',
    's7e3': 'fim:s7e3',
    's7e4': 'fim:s7e4',
    's7e5': 'fim:s7e5',
    's7e6': 'fim:s7e6',
    's7e7': 'fim:s7e7',
    's7e8': 'fim:s7e8',
    's7e9': 'fim:s7e9',
    's7e10': 'fim:s7e10',
    's7e11': 'fim:s7e11',
    's7e12': 'fim:s7e12',
    's7e13': 'fim:s7e13',
    's7e14': 'fim:s7e14',
    's7e15': 'fim:s7e15',
    's7e16': 'fim:s7e16',
    's7e17': 'fim:s7e17',
    's7e18': 'fim:s7e18',
    's7e19': 'fim:s7e19',
    's7e20': 'fim:s7e20',
    's7e21': 'fim:s7e21',
    's7e22': 'fim:s7e22',
    's7e23': 'fim:s7e23',
    's7e24': 'fim:s7e24',
    's7e25': 'fim:s7e25',
    's7e26': 'fim:s7e26',
    's8e1': 'fim:s8e1',
    's8e2': 'fim:s8e2',
    's8e3': 'fim:s8e3',
    's8e4': 'fim:s8e4',
    's8e5': 'fim:s8e5',
    's8e6': 'fim:s8e6',
    's8e7': 'fim:s8e7',
    's8e8': 'fim:s8e8',
    's8e9': 'fim:s8e9',
    's8e10': 'fim:s8e10',
    's8e11': 'fim:s8e11',
    's8e12': 'fim:s8e12',
    's8e13': 'fim:s8e13',
    's8e14': 'fim:s8e14',
    's8e15': 'fim:s8e15',
    's8e16': 'fim:s8e16',
    's8e17': 'fim:s8e17',
    's8e18': 'fim:s8e18',
    's8e19': 'fim:s8e19',
    's8e20': 'fim:s8e20',
    's8e21': 'fim:s8e21',
    's8e22': 'fim:s8e22',
    's8e23': 'fim:s8e23',
    's8e24': 'fim:s8e24',
    's8e25': 'fim:s8e25',
    's8e26': 'fim:s8e26',
    's9e1': 'fim:s9e1',
    's9e2': 'fim:s9e2',
    's9e3': 'fim:s9e3',
    's9e4': 'fim:s9e4',
    's9e5': 'fim:s9e5',
    's9e6': 'fim:s9e6',
    's9e7': 'fim:s9e7',
    's9e8': 'fim:s9e8',
    's9e9': 'fim:s9e9',
    's9e10': 'fim:s9e10',
    's9e11': 'fim:s9e11',
    's9e12': 'fim:s9e12',
    's9e13': 'fim:s9e13',
    's9e14': 'fim:s9e14',
    's9e15': 'fim:s9e15',
    's9e16': 'fim:s9e16',
    's9e17': 'fim:s9e17',
    's9e18': 'fim:s9e18',
    's9e19': 'fim:s9e19',
    's9e20': 'fim:s9e20',
    's9e21': 'fim:s9e21',
    's9e22': 'fim:s9e22',
    's9e23': 'fim:s9e23',
    's9e24': 'fim:s9e24',
    's9e25': 'fim:s9e25',
    's9e26': 'fim:s9e26',
    'EQG Dance Magic': 'eqg:dance magic',
    'EQG Forgotten Friendship': 'eqg:forgotten friendship',
    'EQG Friendship Games': 'eqg:friendship games',
    'EQG Legend of Everfree': 'eqg:legend of everfree',
    'EQG Mirror Magic': 'eqg:mirror magic',
    'EQG Movie Magic': 'eqg:movie magic',
    'EQG Original': 'eqg:original',
    'EQG Rainbow Rocks': 'eqg:rainbow rocks',
    'EQG Roller Coaster of Friendship': None,
    'EQG Roller Coaster of Friendship Special Source':
    'eqg:roller coaster of friendship',
    'EQG Holidays Unwrapped': 'eqg:holidays unwrapped',
    'MLP Movie': 'fim:mlp movie',
    '214 outtakes': 'outtakes:s2e14',
    '421 outtakes': 'outtakes:s4e21',
    '506 outtakes': 'outtakes:s5e6',
    '509 outtakes': 'outtakes:s5e9',
    '624 outtakes': 'outtakes:s6e24',
    '713 outtakes': 'outtakes:s7e13',
    '819 outtakes': 'outtakes:s8e19',
    '823 outtakes': 'outtakes:s8e23',
    '922 outtakes': 'outtakes:s9e22',
    '924 outtakes': 'outtakes:s9e24',
    's2e4_Street Magic With Trixie': 'eqg:s2e4',
    's2e5_Sic Skateboard': 'eqg:s2e5',
    's2e6_Street Chic': 'eqg:s2e6',
    's2e7_Game Stream': 'eqg:s2e7',
    's2e8_Best in Show The Preshow': 'eqg:s2e8',
    'Arizona': None,
    'Oleander and Fred': None,
    'Pom': None,
    'Tianhuo': None,
    'Velvet': None,
    'TFH': None,
    'Noise samples': None,
    'Applejack': None,
    'Fluttershy': None,
    'Nightmare Moon': None,
    'Pinkie Pie': None,
    'Rainbow Dash': None,
    'Rarity': None,
    'Spike': None,
}

# these are only necessary where there are conflicting transcripts
LABEL_EPISODES = {
    'fim_s08e01.txt': 'fim:s8e1',
    'fim_s08e02.txt': 'fim:s8e2',
}


class ClipperLabelSet(LocalFiles):
    def __init__(self, path: str):
        LocalFiles.__init__(self, get_directory(path))

    def _accept_path(self, path: str):
        return ((path.startswith('fim_') or path.startswith('eqg_'))
                and path.endswith('.txt'))

    def _wrap_path(self, path: str):
        return ClipperLabels(path)

    def collect(self, result):
        for file in self.get_files():
            for key in file.labels:
                if key not in result:
                    result[key] = []
                result[key].extend(file.labels[key])


class ClipperLabels:
    def __init__(self, path: str):
        self.path = path
        self.labels = {}

        with open(path, 'rb') as labelfile:
            labeldata = labelfile.read().decode('utf-8')

        for line in labeldata.split('\r\n'):
            if line.strip() == '':
                continue

            try:
                audio_name = audio_name_from_label_line(line, self.labels)
                label = _parse_label(path, line)

                assert audio_name not in self.labels
                self.labels[audio_name] = [label]

            except AssertionError as e:
                if not datapipes.__dry_run__:
                    raise e
                print(e)


def audio_name_from_label_line(line: str, known_paths):
    base = line.split('\t')[-1].strip()
    return fix_audio_fn(base, known_paths)


def _parse_label(source, line):
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
        'source': source,
        'start': start,
        'end': end,
        'character': character,
        'tags': tags,
        'noise': noise_level,
        'transcript': transcript
    }


class PonySorterLabelSet(LocalFiles):
    def __init__(self, path: str):
        LocalFiles.__init__(self, get_directory(path))

    def _accept_path(self, path: str):
        return ((path.startswith('fim_') or path.startswith('eqg_'))
                and path.endswith('.json'))

    def _wrap_path(self, path: str):
        return PonySorterLabels(path)

    def collect(self, result):
        for file in self.get_files():
            for key in file.labels:
                if key not in result:
                    result[key] = []
                result[key].extend(file.labels[key])


class PonySorterLabels:
    def __init__(self, path: str):
        self.path = path
        self.labels = {}

        data = json.loads(open(path, encoding='utf-8').read())

        for label_data in data['labels']:
            character_key = label_data['character']
            assert character_key in CHARACTERS, \
             'Missing character {} in clipper_in.CHARACTERS for {}'.format(character_key, path)
            character = CHARACTERS[character_key]

            # get tags
            if label_data['mood'] == ['canterlot', 'voice']:
                # hack because "canterlot voice" is treated as two tags
                label_data['mood'] = ['canterlot voice']

            for key in label_data['mood']:
                assert key in TAGS, \
                 f'Unknown tag {key} in {path}'
            tags = [TAGS[x] for x in label_data['mood']]

            # noise level
            noise_key = label_data['noise_level']
            assert noise_key in NOISE, \
             'Missing noise tag {} in clipper_in.NOISE for {}'.format(noise_key, path)
            noise = NOISE[noise_key]

            label = {
                'source': path,
                'start': label_data['start'],
                'end': label_data['end'],
                'character': character,
                'tags': tags,
                'noise': noise,
                'transcript': label_data['transcript']
            }
            audio_name = audio_name_from_json_data(label_data, self.labels)

            assert audio_name not in self.labels
            self.labels[audio_name] = self.labels.get(audio_name, [])
            self.labels[audio_name].append(label)


def audio_name_from_json_data(label_data, known_paths):
    seconds = round(label_data['start'])
    hh = seconds // 3600
    mm = (seconds % 3600) // 60
    ss = seconds % 60
    timestamp = '%02d_%02d_%02d' % (hh, mm, ss)

    character = label_data['character']
    mood = ' '.join([x.capitalize() for x in label_data['mood']])
    noise = NOISE[label_data['noise_level']]
    transcript = label_data['transcript']

    base = f'{timestamp}_{character}_{mood}_{noise}_{transcript}'
    return fix_audio_fn(base, known_paths)


def fix_audio_fn(base, known_paths):
    base = re.sub(r'[?]', '_', base)
    base = remove_non_ascii(base)
    base = base.strip(' .')
    # base = base.replace('...', '.')

    if base not in known_paths:
        return base

    duplicate_count = 1
    modified = base
    while modified in known_paths:
        duplicate_count += 1
        modified = '{}-{}'.format(base, duplicate_count)

    return modified


def remove_non_ascii(text):
    return re.sub(r'[^\x00-\x7f]', '', text)


class ClipperDataset(LocalFiles):
    def __init__(self, path: str):
        LocalFiles.__init__(self, path)

        if datapipes.__verbose__:
            print('reading transcipts and labels from labels.text files')

        self.labels = {}
        ClipperLabelSet(path).collect(self.labels)
        PonySorterLabelSet(path).collect(self.labels)

        if datapipes.__verbose__:
            print(f'parsed {len(self.labels)} labels')

    def _accept_path(self, path: str):
        return os.path.splitext(path)[-1].lower() in AUDIO_EXTENSIONS

    def _wrap_path(self, path: str):
        if not is_accepted_audio(path):
            return None

        audio_name = get_name(os.path.splitext(path)[0])
        audio_name = remove_non_ascii(audio_name)

        audio_name = audio_name.strip('. ')

        assert audio_name in self.labels, \
         'Missing audio name {} in labels'.format(audio_name)

        return ClipperFile(path, self.labels[audio_name])


def is_accepted_audio(path):
    clipper_directory = get_name(get_directory(path))
    assert clipper_directory in EPISODES, \
     f'Unknown directory name {clipper_directory} in {path}'

    return EPISODES[clipper_directory] != None


class ClipperFile:
    def __init__(self, audio_path: str, options):
        self.episode = episode_from_path(audio_path)

        if self.episode == None:
            self.reference = None
            return

        label = get_best_label(self.episode, options)
        base_filename = os.path.splitext(audio_path)[0]
        self.audio_path = audio_path
        self.label = label

        self.reference = normalize_path('{}-{}-{}-{}'.format(
            self.label['character'], self.episode, self.label['start'],
            self.label['end']))


def equal_labels(label1, label2):
    if label1.keys() != label2.keys():
        return False

    for key, value in label1.items():
        if key == 'source':
            continue

        if label2[key] != value:
            return False

    return True


def episode_from_label_path(path: str):
    episode_string = get_name(path)
    return LABEL_EPISODES.get(episode_string, None)


def filter_options_by_episode(target_episode, options):
    for opt in options:
        source_episode = episode_from_label_path(opt['source'])
        if source_episode == None or source_episode == target_episode:
            yield opt


def get_best_label(episode, options):
    options = list(filter_options_by_episode(episode, options))

    for opt in options:
        if opt['source'].endswith('.json'):
            return opt

    candidate = options[0]
    for opt in options[1:]:
        assert equal_labels(candidate, opt), \
         "Can't decide between {}".format(json.dumps(options, sort_keys=True,
          indent=4, separators=(',', ': ')))

    return candidate


def episode_from_path(path: str):
    clipper_directory = get_name(get_directory(path))
    assert clipper_directory in EPISODES, \
     f'Unknown episode name {clipper_directory} in {path}'

    return EPISODES[clipper_directory]
