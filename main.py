import glob
import re
import time
from datetime import timedelta, datetime
import os
import configparser
import logging
import logging.config
import yaml


def handle(videofile, index, timestamp):
	logging.debug("-"+videofile + " ["+str(index) +"] "+" @ "+timestamp+"-")
	time_object = datetime.strptime(timestamp, '%H:%M:%S')
	logging.debug("  timestamp: " + str(time_object.time()))
	start_time = (time_object + timedelta(seconds=-45)).time()
	logging.debug("    start_time: " + str(start_time))
	duration = 60

	arguments = f"-ss {start_time}s -t {duration}"
	flags = "-loglevel error -hide_banner"
	basename = os.path.basename(videofile)
	logging.debug("    Basename: " + basename)
	output_filename = os.path.join(target_directory, re.sub(r'\.', f"_{index}.", basename))
	logging.debug("    output_filename: " + output_filename)
	isExist = os.path.exists(output_filename)
	if not isExist:
		command = f"ffmpeg {arguments} -i {videofile} {flags} {output_filename}"
		logging.debug("    Command: " + command)
		os.system(command)
		time_of_event = datetime.fromtimestamp(os.path.getmtime(videofile)) + timedelta(hours=time_object.hour, minutes=time_object.minute, seconds=time_object.second)
		logging.debug("    time_of_event: " + time_of_event.strftime('%Y-%m-%d %H:%M:%S'))
		utime = time.mktime(time_of_event.timetuple())
		os.utime(output_filename, (utime, utime))

def createDirectory(path):
	isExist = os.path.exists(path)
	if not isExist:
		# Create a new directory because it does not exist
		os.makedirs(path)

def read_config():
	global directory 
	global target_directory
	global processed_directory
	global gopro_highlight_parser_directory
	config = configparser.ConfigParser()
	config.read("config.ini")
	directory = config.get("gopro", "directory")
	target_directory = config.get("gopro", "target_directory")
	processed_directory = config.get("gopro", "processed_directory")
	gopro_highlight_parser_directory = config.get("gopro", "gopro_highlight_parser_directory")


def initiate():
	with open('logging.conf', 'r') as f:
		log_cfg = yaml.safe_load(f.read())
		logging.config.dictConfig(log_cfg)

	read_config()
	createDirectory(target_directory)
	createDirectory(processed_directory)

def move_to_processed(filename):
	isExist = os.path.exists(filename)
	if isExist:
		target = os.path.join(processed_directory, os.path.basename(filename))
		os.rename(filename, target)

def createIndexFiles():
	files = glob.glob(os.path.join(directory, "*.MP4"))
	for f in files:
		logging.debug(f"Processing {f} file...")
		script = os.path.join(gopro_highlight_parser_directory, 'GP\ Highlight\ Extractor.py')
		os.system(f"python3 {script} {f}")

def cleanup(directory):
	thm = os.path.join(directory, "*.THM")
	lrv = os.path.join(directory, "*.LRV")
	os.system(f"rm {thm}")
	os.system(f"rm {lrv}")


def do_it():
	initiate()

	createIndexFiles()
	res = glob.glob(os.path.join(directory,"*.txt"))

	for filename in res:
		with open(filename) as f:
			videofile = f.readline().strip()
			index = 0
			for line in f.readlines():
				timestamp = line.strip()
				if timestamp:
					index = index + 1
					timestamp = re.sub(r'^.*?: ', '', timestamp) # remove the index
					timestamp = re.sub(r'\..*?$', '', timestamp) # remove the milliseconds
					handle(videofile, index, timestamp)
		move_to_processed(filename)
		move_to_processed(videofile)

	cleanup(directory)

do_it()