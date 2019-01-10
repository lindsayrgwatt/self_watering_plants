# Self Watering Plant System

Goal is to create a self-watering plant system with following characteristics:

1. User can set the desired moisture level in soil and alter it as desired
2. System will monitor moisture level in soil
3. If soil moisture drops below user's threshold, system will pump water
4. If water runs out before moisture level reached, turn off the pump and let the user know that the pump is out of water
5. After the user adds water, let them push a button to return to normal
6. Debug mode to understand value of different variables
7. Simple, legible and maintainable code (vs. optimized for speed, brevity, etc.)

Out of scope:

1. Logging any data
2. Passing data to a website
3. Directly monitoring water levels so that user does not need to push a button to restart normal operations

Bill of materials:

1. Micropython board (I'm using a 1.0 from the original Kickstarter campaign)
2. Philmore 10 Amp Relay SPDT Coil: 3 VDC/120mA No.86-103
3. [Hall effect sensor](http://www.hobbytronics.co.uk/yf-s201-water-flow-meter) for water flow
4. [Capacitive moisture level sensor](https://www.dfrobot.com/wiki/index.php/Capacitive_Soil_Moisture_Sensor_SKU:SEN0193) - benefit is corrosion resistance
5. Pump?
