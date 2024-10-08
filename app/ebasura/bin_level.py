import RPi.GPIO as GPIO
import time
from ..engine import db 
import config
GPIO.setmode(GPIO.BCM)

# Define pin numbers for the two sensors
TRIG_BIN_ONE = 2  # GPIO 2 (Pin 3)
ECHO_BIN_ONE = 3  # GPIO 3 (Pin 5)

# TRIG_BIN_TWO = 4  # GPIO 4 (Pin 7)
# ECHO_BIN_TWO = 17 # GPIO 17 (Pin 11)

GPIO.setup(TRIG_BIN_ONE, GPIO.OUT)
GPIO.setup(ECHO_BIN_ONE, GPIO.IN)

# GPIO.setup(TRIG_BIN_TWO, GPIO.OUT)
# GPIO.setup(ECHO_BIN_TWO, GPIO.IN)


def measure_distance(trigger, echo):
    # Ensure the trigger is low for a short time
    GPIO.output(trigger, False)
    time.sleep(2)
    
    # Send a 10us pulse to trigger
    GPIO.output(trigger, True)
    time.sleep(0.00001)
    GPIO.output(trigger, False)
    
    # Record the time of the start and stop of the echo
    while GPIO.input(echo) == 0:
        pulse_start = time.time()

    while GPIO.input(echo) == 1:
        pulse_end = time.time()

    # Calculate the duration of the pulse
    pulse_duration = pulse_end - pulse_start
    
    # Speed of sound is 34300 cm/s, so distance is time * speed / 2
    distance = pulse_duration * 17150
    distance = round(distance, 2)

    return distance

def recyclable_bin():
    try:
        while True:
            # Measure distance for both bins
            time.sleep(5)
            update_bin_level(config.BIN_ID, measure_distance(TRIG_BIN_ONE, ECHO_BIN_ONE), 1)    
    except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
        print("Keyboard interrupt")
        
        
def non_recyclable_bin():
    try:
        while True:
            # Measure distance for both bins
            time.sleep(5)
            update_bin_level(config.BIN_ID, measure_distance(TRIG_BIN_TWO, ECHO_BIN_TWO), 2)    
    except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
        print("Keyboard interrupt")

def ensure_waste_type_exists(waste_type_id):

    query_check = "SELECT COUNT(*) FROM waste_type WHERE waste_type_id = %s"
    args = (waste_type_id,)

    result = db.fetch_one(query_check, args)
    if result[0] == 0:

        query_insert = "INSERT INTO waste_type (waste_type_id) VALUES (%s)"
        db.update(query_insert, args)

def update_bin_level(bin_id, distance, waste_id):

    distance = min(distance, 100)

    ensure_waste_type_exists(waste_id)

    query_update = """
    UPDATE waste_level 
    SET current_fill_level = %s, last_update = NOW()
    WHERE bin_id = %s AND waste_type_id = %s
    """
    args_update = (distance, bin_id, waste_id)


    if not db.update(query_update, args_update):

        query_insert = """
        INSERT INTO waste_level (bin_id, waste_type_id, current_fill_level, last_update)
        VALUES (%s, %s, %s, NOW())
        """
        args_insert = (bin_id, waste_id, distance)

        if db.update(query_insert, args_insert):
            print(f"Inserted new bin {waste_id} with level {distance} cm.")
        else:
            print(f"Failed to update or insert bin {waste_id}.")
    else:
        print(f"Updated bin {waste_id} with level {distance} cm.")

