
import usys as sys
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Color

hub = PrimeHub()
left_motor  = Motor(Port.B)
right_motor = Motor(Port.F, Direction.COUNTERCLOCKWISE)
gear_motor  = Motor(Port.D)

SPEED = 500
GEAR_SPEED = 200
TURN_ANGLE = 90  

moving = None  
hub.light.on(Color.BLUE)

def read_key():
    ch = sys.stdin.read(1)
    if ch == '\x1b':
        sys.stdin.read(1)  
        arrow = sys.stdin.read(1)
        if arrow == 'A': return 'up'
        if arrow == 'B': return 'down'
        if arrow == 'C': return 'right'
        if arrow == 'D': return 'left'
        return None
    return ch

while True:
    cmd = read_key()

    if cmd == 'up':
        if moving == 'forward':
            moving = None
            left_motor.brake()
            right_motor.brake()
            hub.display.char('S')
            hub.light.on(Color.BLUE)
        else:
            moving = 'forward'
            left_motor.run(SPEED)
            right_motor.run(SPEED)
            hub.display.char('F')
            hub.light.on(Color.GREEN)

    elif cmd == 'down':
        if moving == 'backward':
            moving = None
            left_motor.brake()
            right_motor.brake()
            hub.display.char('S')
            hub.light.on(Color.BLUE)
        else:
            moving = 'backward'
            left_motor.run(-SPEED)
            right_motor.run(-SPEED)
            hub.display.char('B')
            hub.light.on(Color.RED)

    elif cmd == 'left':
        moving = None
        hub.display.char('L')
        hub.light.on(Color.YELLOW)
        left_motor.run_angle(SPEED, -TURN_ANGLE, wait=False)
        right_motor.run_angle(SPEED, TURN_ANGLE)

    elif cmd == 'right':
        moving = None
        hub.display.char('R')
        hub.light.on(Color.YELLOW)
        left_motor.run_angle(SPEED, TURN_ANGLE, wait=False)
        right_motor.run_angle(SPEED, -TURN_ANGLE)

    elif cmd in ('l', 'L'):
        gear_motor.run(GEAR_SPEED)
        hub.display.char('G')
        hub.light.on(Color.WHITE)

    elif cmd in ('k', 'K'):
        gear_motor.run(-GEAR_SPEED)
        hub.display.char('C')
        hub.light.on(Color.MAGENTA)

    elif cmd in ('j', 'J'):
        gear_motor.brake()
        hub.display.char('S')
        hub.light.on(Color.BLUE)

    elif cmd is not None:
        moving = None
        left_motor.brake()
        right_motor.brake()
        hub.display.char('S')
        hub.light.on(Color.BLUE)