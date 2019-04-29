import random
import time
from datetime import datetime
import bme680
import RPi.GPIO as GPIO
import os
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from copy import deepcopy

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess
# Sensor config
sensor = bme680.BME680()
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
# Input display pins (Joystick and Buttons:
L_pin = 27 
R_pin = 23 
C_pin = 4 
U_pin = 17 
D_pin = 22 
A_pin = 5 
B_pin = 6

GPIO.setmode(GPIO.BCM) 
GPIO.setup(A_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(B_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(L_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(R_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(U_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(D_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(C_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up 

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
# Initialize library.
disp.begin()
# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0
# Start statemachine, mainscreen should come up after start
show_mainscreen = True
temp_current = False
temp_yesterday = False
show_info = False

# Load default font.
font = ImageFont.truetype("Gameplay.ttf", 20)
font2 = ImageFont.load_default()
# Callbacks for user interaction 
def isr_shutdown(channel):
    draw.rectangle((0,0,width,height), outline=0, fill=255)
    disp.image(image)
    disp.display()
    time.sleep(.2)
    os.system("sudo shutdown -h now")
#Reboot wenn pressing B-Button    
GPIO.add_event_detect(B_pin, GPIO.FALLING, callback=isr_shutdown, bouncetime=300)
def isr_mainscreen(channel):
    global show_mainscreen
    global temp_current
    global temp_yesterday
    global show_info

    show_mainscreen = True
    temp_current = False
    temp_yesterday = False
    show_info = False
GPIO.add_event_detect(U_pin, GPIO.FALLING, callback=isr_mainscreen, bouncetime=300)
def isr_temp_current(channel):
    global show_mainscreen
    global temp_current
    global temp_yesterday
    global show_info
    show_mainscreen = False
    temp_current = True
    temp_yesterday = False
    show_info = False
GPIO.add_event_detect(L_pin, GPIO.FALLING, callback=isr_temp_current, bouncetime=300)    
def isr_temp_yesterday(channel):
    global show_mainscreen
    global temp_current
    global temp_yesterday
    global show_info
    show_mainscreen = False
    temp_current = False
    temp_yesterday = True
    show_info = False
GPIO.add_event_detect(R_pin, GPIO.FALLING, callback=isr_temp_yesterday, bouncetime=300)    
def isr_show_info(channel):
    global show_mainscreen
    global temp_current
    global temp_yesterday
    global show_info
    show_mainscreen = False
    temp_current =False
    temp_yesterday = False
    show_info = True
GPIO.add_event_detect(D_pin, GPIO.FALLING, callback=isr_show_info, bouncetime=300)
temp_values_current = [0]* 120
temp_values_yesterday = [0]* 120

def fkt_show_mainscreen():
    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    now = datetime.now()
    now_format = "%02d:%02d:%02d %02d/%02d/%04d" % (now.hour, now.minute, now.second, now.day, now.month, now.year)
        
    if sensor.get_sensor_data():
        temperature = "%.1f C" % (sensor.data.temperature)
        sensor_output = "{0:.1f} hPa {1:.1f} %RH".format(sensor.data.pressure, sensor.data.humidity)

        draw.text((x, top),       temperature,  font=font, fill=255)
        draw.text((x, top+24),    sensor_output,  font=font2, fill=255)                    
        draw.text((x, top+48),    now_format, font=font2, fill=255)
    # Display image.
    disp.image(image)
    disp.display()
def fkt_temp_current():
    global temp_values_current
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    for i in range(0,120):
        draw.point((i,63-temp_values_current[i]), fill=255)
    disp.image(image)
    disp.display()
def fkt_temp_yesterday():
    global temp_values_yesterday
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    for i in range(0,120):
        draw.point((i,63-temp_values_yesterday[i]), fill=255)
    disp.image(image)
    disp.display()
def save_temp_values():
    global temp_values_current
    global temp_values_yesterday
    now = datetime.now()
    if (now.minute % 12 == 0) & (now.second == 30):
        if sensor.get_sensor_data():
            temperature = int(round(sensor.data.temperature))
            temp_values_current[now.hour*5 + int(now.minute/12)] = temperature
            print temp_values_current
    if (now.hour == 24) & (now.minute == 0 ):
        if (now.second == 40):
            temp_values_yesterday = deepcopy(temp_values_current)
            temp_values_current = [0]* 120
            time.sleep(0.5)
try:
    while True:
        if show_mainscreen == True:
		    fkt_show_mainscreen()
        elif temp_current == True:
            fkt_temp_current()
        elif temp_yesterday == True:
            fkt_temp_yesterday()
        save_temp_values()
        time.sleep(0.7)
except KeyboardInterrupt:
    GPIO.cleanup()
    print "\nBye"
