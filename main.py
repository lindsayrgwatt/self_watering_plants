import time
from pyb import ADC, I2C, LCD, Pin

# Following values were obtained by experimenting with the moisture sensor
DRY_DIRT = 3163 # Determined by experimenting with the moisture sensor
SOAKING_DIRT = 1630 # Determined by experimenting with the moisture sensor
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
debug = True

# Set up pins
adc = ADC(Pin.board.Y12) # Moisuture sensor used ADC to get value
lcd = LCD('X')
water_monitor = Pin('Y1', Pin.IN)
pump = Pin('Y2', Pin.OUT)
left_button = Pin('Y3', Pin.IN, Pin.PULL_UP)
right_button = Pin('Y4', Pin.IN, Pin.PULL_UP)

lcd.light(True)

# Interrupt callbacks
def water_incrementer(p):
    global water_flow_counter
    water_flow_counter += 1

def left_button_pushed(p):
    global out_of_water
    global desired_moisture_level
    if out_of_water:
        out_of_water = False
    else:
        desired_moisture_level -= INCREMENT
        if desired_moisture_level < MIN_MOISTURE:
            desired_moisture_level = MIN_MOISTURE

def right_button_pushed(p):
    global out_of_water
    global desired_moisture_level
    if out_of_water:
        out_of_water = False
    else:
        desired_moisture_level += INCREMENT
        if desired_moisture_level > MAX_MOISTURE:
            desired_moisture_level = MAX_MOISTURE


water_monitor.irq(trigger=Pin.IRQ_RISING, handler=water_incrementer)
left_button.irq(trigger=Pin.IRQ_FALLING, handler=left_button_pushed)
right_button.irq(trigger=Pin.IRQ_FALLING, handler=right_button_pushed)

def calculate_moisture_level(input_level):
    numerator = input_level - SOAKING_DIRT
    denominator = DRY_DIRT - SOAKING_DIRT

    level = 1.0 - (numerator * 1.0)/denominator

    return level

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
        lcd.text("Fill Tank",0,10,1)
        lcd.text("Then Hold Any Button",0,20,1)
    else:
        lcd.text("Soil moisture",0,0,1) # Doesn’t support newline characters
        second_line = "Desired: % 1.2f%%" % variables[0]
        lcd.text(second_line,0,10,1)
        third_line = "Actual: % 1.2f%%" % variables[1]
        lcd.text(third_line,0,20,1)
    lcd.show()


# Main program loop
while True:
    if out_of_water:
        update_screen()
    else:
        raw_moisture_value = adc.read()
        moisture_level = calculate_moisture_level(raw_moisture_value)

        if debug:
            update_screen()
        else:
            update_screen([desired_moisture_level, moisture_level])

        if moisture_level <= desired_moisture_level and not pump_on:
            start_pump()
        elif moisture_level <= desired_moisture_level and pump_on:
            check_for_water()
        elif moisture_level > desired_moisture_level and pump_on:
            stop_pump()
