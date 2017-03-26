#!/usr/bin/env python
# -*- coding: utf-8 -*-

patterns = [
    ('season', '(s?([0-9]{1,2}))[ex]'),
    ('episode', '([ex]([0-9]{2})(?:[^0-9]|$))'),
    ('year', '([\[\(]?((?:19[0-9]|20[01])[0-9])[\]\)]?)'),
    ('resolution', '([0-9]{3,4}p)'),
    ('quality', ('((?:PPV\.)?[HP]DTV|(?:HD)?CAM|B[DR]Rip|(?:HD-?)?TS|'
                 '(?:PPV )?WEB-?DL(?: DVDRip)?|HDRip|DVDRip|DVDRIP|'
                 'CamRip|W[EB]BRip|BluRay|DvDScr|hdtv|telesync)')),
    ('codec', '(xvid|[hx]\.?26[45])'),
    ('audio', ('(MP3|DD5\.?1|Dual[\- ]Audio|LiNE|DTS|'
               'AAC[.-]LC|AAC(?:\.?2\.0)?|'
               'AC3(?:\.5\.1)?)')),
    ('group', '(- ?([^-]+(?:-={[^-]+-?$)?))$'),
    ('region', 'R[0-9]'),
    ('extended', '(EXTENDED(:?.CUT)?)'),
    ('hardcoded', 'HC'),
    ('proper', 'PROPER'),
    ('repack', 'REPACK'),
    ('container', '(MKV|AVI|MP4)'),
    ('widescreen', 'WS'),
    ('website', '^(\[ ?([^\]]+?) ?\])'),
    ('language', '(rus\.eng|ita\.eng)'),
    ('sbs', '(?:Half-)?SBS'),
    ('unrated', 'UNRATED'),
    ('size', '(\d+(?:\.\d+)?(?:GB|MB))'),
    ('3d', '3D')
]

types = {
    'season': 'integer',
    'episode': 'integer',
    'year': 'integer',
    'extended': 'boolean',
    'hardcoded': 'boolean',
    'proper': 'boolean',
    'repack': 'boolean',
    'widescreen': 'boolean',
    'unrated': 'boolean',
    '3d': 'boolean'
}
