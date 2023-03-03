import ya_nowcast_info as nowcast
import time
import threading
import atexit
import RPi.GPIO as GPIO
import os
import random

PIN_GREEN = 37
PIN_YELLOW = 35
PIN_RED = 33

ALL_PINS = [PIN_GREEN, PIN_YELLOW, PIN_RED]

UPDATE_INTERVAL_MIN = 200
UPDATE_INTERVAL_MAX = 300

STATE = {
    'pins': [],
    'blinking': False,
    'change': True
}

def main():
    setup_gpio()
    clear_gpio()
    atexit.register(clear_gpio)
    update_info()
    start_indicator_loop()

def setup_gpio():
    """ Setup GPIO for application """

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)

    for pin in ALL_PINS:
        GPIO.setup(pin, GPIO.OUT)

def clear_gpio():
    """ Set all pins to LOW state """

    for pin in ALL_PINS:
        GPIO.output(pin, GPIO.LOW)

def update_info():
    """ Update display information based on nowcast """

    nowcast_data = nowcast.get_info()

    if nowcast_data is not None:
        now_time = time.strftime('%Y-%m-%d, %H:%M')
        print('[{}] {}'.format(now_time, nowcast_data['raw']))
        
        # Oinklog
        os.system('python3 /home/pi/projects/oinklog_client.py "NC: {}"'.format(nowcast_data['raw']))

        info = nowcast_data['info']
        STATE['blinking'] = info['going']

        if info['minutes'] > -1:
            STATE['pins'] = [get_event_pin(info)]
        else:
            STATE['pins'] = []
    else:
        # Error state
        STATE['pins'] = [PIN_GREEN, PIN_YELLOW, PIN_RED]
        STATE['blinking'] = True

    STATE['change'] = True

    # Re-run after certain time
    update_interval = random.randint(UPDATE_INTERVAL_MIN, UPDATE_INTERVAL_MAX)
    timer = threading.Timer(update_interval, update_info)
    timer.start()

def get_event_pin(info):
    """ Get pin number that will be in HIGH state """

    time = info['minutes']

    if info['going']:
        # Falling now
        if not info['ending']:
            return PIN_RED
        elif time > 30:
            return PIN_YELLOW
        else:
            return PIN_GREEN
    else:
        # No precipitation
        if not info['starting']:
            return PIN_GREEN
        elif time > 30:
            return PIN_YELLOW
        else:
            return PIN_RED

def start_indicator_loop():
    tick = 0

    while True:
        if STATE['change'] or STATE['blinking']:
            STATE['change'] = False
            clear_gpio()

            if not STATE['blinking'] or (tick % 2 == 0):
                for pin in STATE['pins']:
                    GPIO.output(pin, GPIO.HIGH)

        time.sleep(1)
        tick += 1

if __name__ == '__main__':
    main()
