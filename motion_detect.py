#!/usr/bin/env python
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
from PIL import Image
import os
import time
import picamera
import spidev

# A primitive motion detect program utilizing the 'raspistill' system command and the tmp-folder of the raspberry pi OS for motion detection,
# reads temperature from a GPIO-sensor and saves a high resolution image (with current temperature and time as overlay text and a timestamp in the filename) 
# into a subfolder of the programs execution directory whenever motion is detected.

print("Starting program...")

# Create new subfolder for images (if needed)
picdir = os.getcwd() + "/motion_detect_pics/"
try:
	existing_picdir = os.listdir(picdir) # List folder content to see if folder already exists
except FileNotFoundError: # if not, create it. (at current working directory)
	os.mkdir(picdir)

# Setting up temperature sensor
# A0 = 0, A1 = 1, etc...
temp_channel = 0 # make sure your temperature sensor is plugged in the same slot as stated here
time.sleep(3)
spi = spidev.SpiDev()
spi.open(0,0)

# Function for capturing a full-size image with temperature and timestamp as overlay text and timestamp in the filename
def saveImg():
        with picamera.PiCamera() as camera:
                camera.resolution = (1280, 960)
                camera.hflip = True
                camera.vflip = True
                camera.start_preview()
                time.sleep(1) # camera focus time
                camera.annotate_text_size = 15
                camera.annotate_text = 'Time: '+time.strftime("%Y-%m-%d -- %H:%M:%S")+'\nTemperature: '+readTemp()+' degrees Celsius'
                filename = "MD_" + time.strftime("%Y%m%d-%H%M%S") # timestamped filename of the image
                camera.capture('motion_detect_pics/'+filename+'.jpg')
                print("Image saved to disk: "+filename+".jpg")

# Function that reads and returns the temperature as Celsius
def readTemp():
    global temp_channel
    # Read SPI data from MCP3004 chip, 4 possible adc's (0 - 3)
    if temp_channel > 3 or temp_channel < 0:
        return -1
    r = spi.xfer2([1,8+temp_channel <<4,0])
    value = ((r[1] &3) <<8)+r[2]
    volts = (value * 3.3) / 1024
    temperature_C = (volts - 0.5) * 100
    return str("{:.2f}".format(temperature_C))

maxFolderSize = 200 * 1024 * 1024 # limit picture folder size to 200 MB

# Keep picture folder size below given value, deleting older images if needed
def manageFolderSize(maximumFolderSize, picture_folder):
    if (getFolderSize(picture_folder) > maximumFolderSize):
        for filename in sorted(os.listdir(picture_folder)):
            if filename.startswith("MD_") and filename.endswith(".jpg"):
                os.system('rm '+picdir+filename+'')
                print ("Deleted %s to avoid filling disk" % filename)
                if (maximumFolderSize > getFolderSize(picture_folder)):
                    return
# Get picture folder size
def getFolderSize(picture_folder):
        folder_size = 0
        for dirpath, dirnames, filenames in os.walk(picture_folder):
                for f in filenames:
                        fp = os.path.join(dirpath, f)
                        folder_size += os.path.getsize(fp)
        return folder_size
    
# setting up GPIO-led:
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
ledi = 21 # GPIO slot for LED
GPIO.setup (ledi, GPIO.OUT)

# motion detect sensitivity parameters
threshold = 30 # how much a pixel has to change to be marked as "changed" 
negativeThreshold = -30 # a negative value threshold
sensitivity = 5 # how many changed pixels before declaring motion

# save a small black and white baseline image to tmp-folder (mounted RAM-partition, so it's fast)
os.system('/opt/vc/bin/raspistill -cfx 128:128 -n -o /tmp/baseline.jpg -w 50 -h 50 -t 1200')
# commit image data to a variable
image1 = Image.open("/tmp/baseline.jpg")
pic_a = image1.load()
print("Motion detection active")
buffer_swap_counter = 0
# Main-loop
while True:

    GPIO.output(ledi, False)
    # save comparison-image to tmp-folder
    os.system('/opt/vc/bin/raspistill -cfx 128:128 -n -o /tmp/comparison.jpg -w 50 -h 50 -t 1200')
    image2 = Image.open("/tmp/comparison.jpg")
    pic_b = image2.load()
    print(".",end="")
    buffer_swap_counter += 1
    # count changed pixels
    changedPixels = 0
    for x in range(0, 50):
        if changedPixels > sensitivity:
            break
        for y in range(0, 50):
            # Just check green channel as it's the highest quality channel
            pixdiff = abs(pic_a[x,y][1] - pic_b[x,y][1])
            if pixdiff > threshold or pixdiff < negativeThreshold:
                changedPixels += 1    
            if changedPixels > sensitivity:
                break
    # if motion is detected, flash LED and take a high resolution picture:
    if changedPixels > sensitivity:
        print("Motion detected at "+time.strftime("%Y-%m-%d -- %H:%M:%S"), end=". ")
        GPIO.output(ledi, True)
        saveImg()
        manageFolderSize(maxFolderSize, picdir)
        # Swap comparison buffers
        pic_a = pic_b
        buffer_swap_counter = 0
    # swap buffers at set intervals to account for slight lighting condition changes:
    if buffer_swap_counter > 5:
        pic_a = pic_b
        buffer_swap_counter = 0
        
