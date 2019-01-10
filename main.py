#Goal is to create a self-watering plant system with following characteristics:
#
#1. User can set the desired moisture level in soil and alter it as desired
#2. System will monitor moisture level in soil
#3. If soil moisture drops below user's threshold, system will pump water
#4. If water runs out before moisture level reached, turn off the pump and let the user know that the pump is out of water
#5. After the user adds water, let them push a button to return to normal
import time
from pyb import ADB, LCD, Pin

# Following values were obtained by experimenting with the moisture sensor
DRY_DIRT = 3163
SOAKING_DIRT = 1630
DELAY = 1
DELTA = 1

desired_moisture_level = 0.25
moisture_level = -1.0
water_flow_counter = 0

# State variables
first_loop = True
out_of_water = False
pump_on = False
debug = False

# Set up pins
adc = ADC(Pin.board.Y12)
lcd = LCD('X')
water_monitor = Pin('Y1', Pin.IN)
pump = Pin('Y2', Pin.Out)

lcd.light(True)

# Interrupt callbacks
def water_incrementer(p):
    water_flow_counter += 1
    water_monitor.irq(trigger=Pin.IRQ_RISING, handler=water_incrementer)

# Helper functions
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
    #TODO - does this need a delay? Does that affect the interrupts at all?
    if first_loop:
        # assign an interrupt to change the desired moisture level
        first_loop = False

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
