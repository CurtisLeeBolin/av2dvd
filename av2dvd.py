#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  av2dvd.py
#
#  Copyright 2014 Curtis Lee Bolin <CurtisLeeBolin@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import argparse, os, subprocess, shlex, time, re, datetime, shutil

class av2dvd:
	def __init__(self, filename, aspect=None):
		self.aspect = aspect
		self.filename = filename
		self.title, self.fileExtension = os.path.splitext(filename)
		self.outputDir = os.getcwd()

	def runSubprocess(self, args):
		p = subprocess.Popen(shlex.split(args), stderr=subprocess.PIPE)
		stdoutData, stderrData = p.communicate()
		stderrData = stderrData.decode(encoding='utf-8', errors='ignore')
		return stderrData

	def log(self, s, _print=False):
		if _print:
			print(s)
		else:
			s = '\n\n\n{}\n\n\n'.format(s)
		with open('{}/{}_av2dvd_.log'.format(self.outputDir, self.title), 'a', encoding='utf-8') as f:
			f.write('{}\n'.format(s))

	def analizing_av(self):
		self.log('{} Analizing {}'.format(time.strftime('%X'), self.title), True)
		_16_9 = 16/9
		_4_3  =  4/3
		audioBitrateDict = {
			'mono' : 192,
			'stereo' : 192,
			'2' : 192,
			'2 channels' : 192,
			'5.1' : 448,
			'5.1(side)' : 448,
			'7.1' : 640
		}
		args = 'ffmpeg -i {}'.format(self.filename.__repr__())
		stderrData = self.runSubprocess(args)
		duration = re.findall('Duration: (.*?),', stderrData)[-1]
		durationList = duration.split(':')
		if duration != 'N/A':
			durationSec = 60 * 60 * int(durationList[0]) + 60 * int(durationList[1]) + float(durationList[2])
			cropDetectStart =  str(datetime.timedelta(seconds=(durationSec / 10)))
			cropDetectDuration =  str(datetime.timedelta(seconds=(durationSec / 100)))
			audioCh = re.findall(' Hz, (.*?),', stderrData)[-1]
			audio_bitrate = audioBitrateDict.get(audioCh, None)
			if audio_bitrate:
				video_bitrate = int(( (4590208 * 8) / durationSec ) - audio_bitrate)
				if video_bitrate > 8000:
					self.video_bitrate = '8000k'
				else:
					self.video_bitrate = '{}k'.format(video_bitrate)
			else:
				self.video_bitrate = None
		else:
			cropDetectStart = '0'
			cropDetectDuration = '60'
			self.video_bitrate = None
		args = 'ffmpeg -i {} -ss {} -t {} -filter:v cropdetect -an -sn -f rawvideo -y {}'.format(self.filename.__repr__(), cropDetectStart, cropDetectDuration, os.devnull)
		self.log(args)
		stderrData = self.runSubprocess(args)
		self.log(stderrData)
		if self.aspect:
			self.crop = ''
			self.aspect_ratio = self.aspect
		else:
			crop = re.findall('crop=(.*?)\n', stderrData)[-1]
			cropList = crop.split(':')
			w = int(cropList[0])
			h = int(cropList[1])
			delta_16_9 = (w/h) - _16_9
			delta_4_3  = (w/h) -  _4_3
			if delta_16_9 < delta_4_3:
				self.aspect_ratio = '16:9'
			else:
				self.aspect_ratio = '4:3'

	def create_VOB(self):
		self.log('{} Creating VOB.'.format(time.strftime('%X')), True)
		if self.video_bitrate:
			args = 'ffmpeg -i {filename} -aspect {aspect_ratio} -map_metadata -1 -metadata title={title} -target ntsc-dvd -q:v 0 -b:v {video_bitrate} -y {outputDir}/{title}.vob'.format(filename=self.filename.__repr__(), aspect_ratio=self.aspect_ratio, title=self.title.__repr__(), outputDir=self.outputDir.__repr__(), video_bitrate=self.video_bitrate)
		else:
			args = 'ffmpeg -i {filename} -aspect {aspect_ratio} -map_metadata -1 -metadata title={title} -target ntsc-dvd -q:v 0 -y {outputDir}/{title}.vob'.format(filename=self.filename.__repr__(), aspect_ratio=self.aspect_ratio, title=self.title.__repr__(), outputDir=self.outputDir.__repr__())			
		self.log(args)
		stderrData = self.runSubprocess(args)
		self.log(stderrData)

	def create_DVD_structure(self):
		self.log('{} Creating DVD File Structure.'.format(time.strftime('%X')), True)
		os.environ['VIDEO_FORMAT'] = 'NTSC'
		args = 'dvdauthor -o {outputDir}/{title}/ -t {outputDir}/{title}.vob'.format(outputDir=self.outputDir.__repr__(), title=self.title.__repr__())
		self.log(args)
		stderrData = self.runSubprocess(args)
		args = 'dvdauthor -T -o {outputDir}/{title}/'.format(outputDir=self.outputDir.__repr__(), title=self.title.__repr__())
		self.log(args)
		stderrData = self.runSubprocess(args)
		self.log(stderrData)
		os.remove('{outputDir}/{title}.vob'.format(outputDir=self.outputDir, title=self.title))

	def create_ISO(self):
		self.log('{} Creating ISO.'.format(time.strftime('%X')), True)
		args = 'genisoimage -dvd-video -o {title}.iso {outputDir}/{title}'.format(outputDir=self.outputDir.__repr__(), title=self.title.__repr__())
		self.log(args)
		stderrData = self.runSubprocess(args)
		self.log(stderrData)
		shutil.rmtree('{outputDir}/{title}'.format(outputDir=self.outputDir, title=self.title))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		prog='av2dvd.py',
		description='Audio Video to DVD',
		epilog='Copyright 2014 Curtis lee Bolin <CurtisLeeBolin@gmail.com>'
	)
	parser.add_argument(
		nargs=1,
		dest='filename',
		help='The audio video file you want turned into a dvd.'
	)
	parser.add_argument('-a', '--aspect',
		dest='aspect',
		help='Force an aspect ratio.  eg. 16:9'
	)
	args = parser.parse_args()

	dvd = av2dvd(args.filename[0], args.aspect)

	dvd.analizing_av()
	dvd.create_VOB()
	dvd.create_DVD_structure()
	dvd.create_ISO()
