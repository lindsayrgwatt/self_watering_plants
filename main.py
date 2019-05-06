import time
import micropython
import machine
from pyb import ADC, I2C, LCD, Pin, delay

micropython.alloc_emergency_exception_buf(100)

# Following values were obtained by experimenting with the moisture sensor
DRY_DIRT = 3163 # Determined by experimenting with the moisture sensor
SOAKING_DIRT = 1630 # Determined by experimenting with the moisture sensor
DELAY = 1
DELTA = 100 # Determined by experimenting
INCREMENT = 0.05
MAX_MOISTURE = 0.7 # If lower than 1.0, system will shut off if bouncing pushes moisture level up
MIN_MOISTURE = 0.0
FILE_NAME = 'data.txt'
LEFT = 'left'
RIGHT = 'right'

desired_moisture_level = 0.25
moisture_level = -1.0
water_flow_counter = 0

try:
    f = open(FILE_NAME, 'r')
    desired_moisture_level = float(f.read()[0:4])
except OSError:
    print('No file to open')
except ValueError:
    print('Invalid moisture level data')
finally:
    f.close()

# State variables
out_of_water = False
pump_on = False
debug = True

# Set up pins
adc = ADC(Pin.board.X8) # Moisuture sensor uses ADC to get value
lcd = LCD('Y')
water_monitor = Pin('X10', Pin.IN)
pump = Pin('X12', Pin.OUT)
left_button = Pin('X6', Pin.IN, Pin.PULL_UP)
right_button = Pin('X1', Pin.IN, Pin.PULL_UP)

lcd.light(True)

# Interrupt callbacks
def water_incrementer(p):
    global water_flow_counter
    water_flow_counter += 1

def button_pushed(button):
    global out_of_water
    global desired_moisture_level
    if out_of_water:
        out_of_water = False
    elif button == RIGHT:
        desired_moisture_level += INCREMENT
        if desired_moisture_level > MAX_MOISTURE:
            desired_moisture_level = MAX_MOISTURE
        write_moisture_level(desired_moisture_level)
    elif button == LEFT:
        desired_moisture_level -= INCREMENT
        if desired_moisture_level < MIN_MOISTURE:
            desired_moisture_level = MIN_MOISTURE
        write_moisture_level(desired_moisture_level)


def left_button_pushed(p):
    button_pushed(LEFT)
    print("Left button pushed")

def right_button_pushed(p):
    button_pushed(RIGHT)
    print("Right button pushed")

water_monitor.irq(trigger=Pin.IRQ_RISING, handler=water_incrementer)
left_button.irq(trigger=Pin.IRQ_FALLING, handler=left_button_pushed)
right_button.irq(trigger=Pin.IRQ_FALLING, handler=right_button_pushed)

def calculate_moisture_level(input_level):
    numerator = input_level - SOAKING_DIRT
    denominator = DRY_DIRT - SOAKING_DIRT

    level = 1.0 - (numerator * 1.0)/denominator

    return level

def write_moisture_level(level):
    f = open(FILE_NAME, 'w')
    f.write(str(level))
    f.close()

def start_pump():
    global pump_on
    pump_on = True
    pump.value(1)

def stop_pump():
    global pump_on
    pump.value(0)
    pump_on = False

def check_for_water():
    global out_of_water
    global water_flow_counter
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
        first_line = "%.2f | %.2f | %d" % (desired_moisture_level, moisture_level, water_flow_counter)
        lcd.text(first_line,0,0,1) # Doesn’t support newline characters
        second_line = ""
        if out_of_water:
            second_line += "OOW | "
        else:
            second_line += "W | "
        if pump_on:
            second_line += "P ON"
        else:
            second_line += "P OFF"
        lcd.text(second_line,0,10,1)
        third_line = "%d" % adc.read()
        lcd.text(third_line,0,20,1)
    elif out_of_water:
        lcd.text("Out Of Water",0,0,1) # Doesn’t support newline characters
        lcd.text("Fill Tank & Then",0,10,1)
        lcd.text("Hold Any Button",0,20,1)
    else:
        lcd.text("Soil moisture",0,0,1) # Doesn’t support newline characters
        desired = 100 * variables[0]
        second_line = "Desired: % 1.f%%" % desired
        lcd.text(second_line,0,10,1)
        actual = 100 * variables[1]
        third_line = "Actual:  % 1.f%%" % actual
        lcd.text(third_line,0,20,1)
    lcd.show()


# Main program loop
counter = 0
while True:
    if debug:
        print(counter)
        print("pause for a second")
        time.sleep(DELAY)
        counter += 1
    if out_of_water:
        if debug:
            print("out of water")
        update_screen()
    else:
        raw_moisture_value = adc.read()
        moisture_level = calculate_moisture_level(raw_moisture_value)

        if debug:
            update_screen()
        else:
            update_screen([desired_moisture_level, moisture_level])

        if moisture_level <= desired_moisture_level:
            if pump_on:
                if debug:
                    print("check_for_water")
                check_for_water()
            elif not out_of_water:
                if debug:
                    print("start_pump")
                start_pump()
        else:
            if debug:
                print("stop_pump")
            stop_pump()
