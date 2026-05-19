import serial
import serial.tools.list_ports
import keyboard
import time

BAUD = 115200

def find_hub_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        print(f"  Found: {p.device} - {p.description}")
        if 'LEGO' in p.description or 'Technic' in p.description or 'Prime' in p.description:
            return p.device
    if ports:
        return ports[0].device
    return None

print("Scanning for SPIKE Prime hub...")
PORT = find_hub_port()

if PORT is None:
    print("No COM port found. Connect the hub via USB and try again.")
    exit(1)

print(f"Connecting on {PORT} ...")

up_was_pressed    = False
down_was_pressed  = False
l_was_pressed     = False
k_was_pressed     = False
j_was_pressed     = False

forward_on  = False
backward_on = False

with serial.Serial(PORT, BAUD, timeout=1) as ser:
    print("Connected! Controls:")
    print("  UP    = toggle forward    DOWN  = toggle backward")
    print("  LEFT  = turn left 90°    RIGHT = turn right 90°")
    print("  L     = gear open        K     = gear close      J = gear stop")
    print("  ESC   = quit")

    while not keyboard.is_pressed('esc'):
        up_pressed   = keyboard.is_pressed('up')
        down_pressed = keyboard.is_pressed('down')
        l_pressed    = keyboard.is_pressed('l')
        k_pressed    = keyboard.is_pressed('k')
        j_pressed    = keyboard.is_pressed('j')

        # toggle forward on rising edge
        if up_pressed and not up_was_pressed:
            forward_on = not forward_on
            backward_on = False

        # toggle backward on rising edge
        if down_pressed and not down_was_pressed:
            backward_on = not backward_on
            forward_on = False

        # turns cancel movement
        if keyboard.is_pressed('right'):
            forward_on = False
            backward_on = False
            ser.write(b'\x1b[C')
        elif keyboard.is_pressed('left'):
            forward_on = False
            backward_on = False
            ser.write(b'\x1b[D')
        elif forward_on:
            ser.write(b'\x1b[A')
        elif backward_on:
            ser.write(b'\x1b[B')
        elif l_pressed and not l_was_pressed:
            ser.write(b'L')
        elif k_pressed and not k_was_pressed:
            ser.write(b'K')
        elif j_pressed and not j_was_pressed:
            ser.write(b'J')
        else:
            ser.write(b'x')

        up_was_pressed   = up_pressed
        down_was_pressed = down_pressed
        l_was_pressed    = l_pressed
        k_was_pressed    = k_pressed
        j_was_pressed    = j_pressed
        time.sleep(0.05)

    ser.write(b'x')
    print("Stopped.")