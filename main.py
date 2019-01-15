#Goal is to create a self-watering plant system with following characteristics:
#
#1. User can set the desired moisture level in soil and alter it as desired
#2. System will monitor moisture level in soil
#3. If soil moisture drops below user's threshold, system will pump water
#4. If water runs out before moisture level reached, turn off the pump and let the user know that the pump is out of water
#5. After the user adds water, let them push a button to return to normal
import time
from pyb import ADB, I2C, LCD, Pin
from mpr121 import MPR121

# Following values were obtained by experimenting with the moisture sensor
DRY_DIRT = 3163
SOAKING_DIRT = 1630
DELAY = 1
DELTA = 1
INCREMENT = 0.05
MAX_MOISTURE = 1.0
MIN_MOISTURE = 0.0

desired_moisture_level = 0.25
moisture_level = -1.0
water_flow_counter = 0

# State variables
out_of_water = False
pump_on = False
debug = False

# Set up pins
adc = ADC(Pin.board.Y12)
lcd = LCD('X')
water_monitor = Pin('Y1', Pin.IN)
pump = Pin('Y2', Pin.Out)

lcd.light(True)
capacitive_buttons = mpr121.MPR121(I2C(1, I2C.MASTER))

# Interrupt callbacks
def water_incrementer(p):
    water_flow_counter += 1
    water_monitor.irq(trigger=Pin.IRQ_RISING, handler=water_incrementer)

# Helper functions
def poll_buttons():
    input = capacitive_buttons.touch_status()
    # Y == 1, X == 2, B == 4, A == 8; sum of two or more means multitouch
    if out_of_water and input in [1,2,4,8,3,5,9,6,10,12]:
        out_of_water = False
    else:
        if input in [1, 4, 5]:
            desired_moisture_level += INCREMENT
            if desired_moisture_level > MAX_MOISTURE:
                desired_moisture_level = MAX_MOISTURE
        elif input in [2, 8, 10]:
            desired_moisture_level -= INCREMENT
            if desired_moisture_level < MIN_MOISTURE:
                desired_moisture_level = MIN_MOISTURE


def calculate_moisture_level(input_level):
    numerator = input_level - SOAKING_DIRT
    denominator = DRY_DIRT - SOAKING_DIRT

    level = 1.0 - (numerator * 1.0)/denominator

    return level

def start_pump():
    pump_on = True
    pump.value(1)

def stop_pump():
    pump.value(0)
    pump_on = False

def check_for_water():
    original_water_level = water_flow_counter
    time.sleep(DELAY)
    new_water_level = water_flow_counter
    if new_water_level - original_water_level <= DELTA:
        out_of_water = True
        stop_pump()
    water_flow_counter = 0

def update_screen(variables=None):
    lcd.fill(0)
    if debug:
        lcd.text("Debug",0,0,1) # Doesn’t support newline characters
        lcd.text("Debug",0,10,1)
        lcd.text("Debug",0,20,1)
    elif out_of_water:
        lcd.text("Out Of Water",0,0,1) # Doesn’t support newline characters
        lcd.text("Fill Tank",0,10,1)
        lcd.text("Then Push Button",0,20,1)
    else:
        lcd.text("Soil moisture",0,0,1) # Doesn’t support newline characters
        second_line = "Desired: %2.f%" % variables[0]
        lcd.text(second_line,0,10,1)
        third_line = "Actual: %2.f%" % variables[1]
        lcd.text(third_line,0,20,1)
    lcd.show()


# Main program loop
while True:
    poll_buttons()

    if out_of_water:
        update_screen()
    else:
        raw_moisture_value = adc.read()
        moisture_level = calculate_moisture_level(raw_moisture_value)

        update_screen([desired_moisture_level, moisture_level])

        if moisture_level <= desired_moisture_level and not pump_on:
            start_pump()
        elif moisture_level <= desired_moisture_level and pump_on:
            check_for_water()
        elif moisture_level > desired_moisture_level and pump_on:
            stop_pump()
