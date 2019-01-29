#!/usr/bin/env python
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
from PIL import Image
import os
import time
import datetime

GPIO.setmode(GPIO.BCM)
sensori = 21
GPIO.setup (sensori, GPIO.OUT)

liike = 0
#havainto = 1
o = 733114
# kuvien (pikseleiden) vertailu. 
# ottaa ensimmäisen vertailukuvan
os.system('/opt/vc/bin/raspistill -n -o /tmp/baseline.jpg -w 32 -h 32 -t 1')
def comparepixel():
	global liike
	global havainto
	#while True:
	data1 = pix1[pixx,pixy]
	data2 = pix2[pixx,pixy]
	
	for i in data1:
		for y in data2:
			tresh = i - y
			#print (tresh)
	if tresh > 30 or tresh < -30:
		GPIO.output(sensori, True)
	if tresh > 30 or tresh < -30:
		liike = liike + 1
					
		#break


#b = 20
while True:
	#os.system('cp / /tmp/baseline.jpg -w 32 -h 32 -t 1')
	#time.sleep (1)
	
	#print ("baseline kuva paivitetty")
	liike = 0
	im1 = Image.open("/tmp/baseline.jpg")
	pix1 = im1.load()
	#a = a-1
	b = 2 # kuinka monta vertailukuvaa otetaan, kunnes baseline kuva päivitetään
	pixx = 0
	pixy = 0
	valmis = 0
	while True:
		if valmis == 1:
			break
		os.system('/opt/vc/bin/raspistill -n -o /tmp/compare.jpg -w 32 -h 32 -t 1')
		#print ("vertailukuva otettu")
		im2 = Image.open("/tmp/compare.jpg")
		GPIO.output(sensori, False)
		valmis = 0
		pixx = 0
		pixy = 0
		pix2 = im2.load()
		b = b - 1
		# kun b tulee nollaan, otetaan kuva vertailukohteeksi
		if b <= 0:
			break
		while True:
			
			# --- Debuggausta varten, näyttää vertailtavana olevan pikselin koordinaatit
			#print ("x-koordinaatti = ",pixx)
			#print ("y-koordinaatti = ",pixy)
			#print ("kierroksia jaljella: ", b)
			# -----
			
			#vaihdetaan uusi pikseli vertailtavaksi
			if pixx == 31:
				pixx = 0
				pixy = pixy+1
			# kun alarivin loppu on saavutettu (eli ei liikehavaintoa) siirretään vertailukuva uudeksi baselinekuvaksi (nopeuttaa hieman toimintaa)
			if pixy == 31:
				os.system('mv /tmp/compare.jpg /tmp/baseline.jpg')
				break
			pixx = pixx+1
			
			# Kun liike on tietyn vahvuinen ottaa valvontakuvan, arvoa vaihtamalla herkkyys muuttuu
			if liike >= 5:
				
				#print (%d:%02d:%02d)
				aika = time.strftime("%Y:%m:%d-%H:%M:%S")
				os.system('/opt/vc/bin/raspistill -o havainnot/'+aika+'.jpg -w 1024 -h 768 -t 1')
				print ("liiketta havaittu, kuva otettu nimella: ",aika, ".jpg" )
				#havainto = havainto+1
				#havaintokuvan jälkeen otetaan uusi baseline kuva
				os.system('/opt/vc/bin/raspistill -n -o /tmp/baseline.jpg -w 32 -h 32 -t 1')
				GPIO.output(sensori, False)
				valmis = 1
				liike = 0
				break
			
			comparepixel()

			
				
