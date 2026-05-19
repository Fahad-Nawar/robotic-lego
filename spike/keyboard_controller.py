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

        # toggle backward on rising edge (UP key)
        if up_pressed and not up_was_pressed:
            backward_on = not backward_on
            forward_on = False

        # toggle forward on rising edge (DOWN key)
        if down_pressed and not down_was_pressed:
            forward_on = not forward_on
            backward_on = False

        # turns cancel movement
        if keyboard.is_pressed('right'):
            forward_on = False
            backward_on = False
            ser.write(b'\x1b[D')
        elif keyboard.is_pressed('left'):
            forward_on = False
            backward_on = False
            ser.write(b'\x1b[C')
        elif forward_on:
            ser.write(b'\x1b[A')
        elif backward_on:
            ser.write(b'\x1b[B')
        elif l_pressed:
            ser.write(b'L')
        elif k_pressed:
            ser.write(b'K')
        else:
            ser.write(b'x')

        up_was_pressed   = up_pressed
        down_was_pressed = down_pressed
        time.sleep(0.05)

    ser.write(b'x')
    print("Stopped.")