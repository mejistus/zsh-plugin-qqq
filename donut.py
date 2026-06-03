#!/usr/bin/env python3
import math
import os
import select
import signal
import sys
import termios
import time
import tty


SHADES = ".,-~:;=!*#$@"


def terminal_size():
    size = os.get_terminal_size()
    return max(size.columns, 20), max(size.lines, 10)


def render(width, height, a_angle, b_angle):
    pixels = [" "] * (width * height)
    depth = [0.0] * (width * height)

    cos_a = math.cos(a_angle)
    sin_a = math.sin(a_angle)
    cos_b = math.cos(b_angle)
    sin_b = math.sin(b_angle)

    radius1 = 1.0
    radius2 = 2.0
    distance = 5.0
    scale = min(width * 0.50, height * 1.05)
    x_center = width // 2
    y_center = height // 2

    theta = 0.0
    while theta < math.tau:
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)

        phi = 0.0
        while phi < math.tau:
            cos_phi = math.cos(phi)
            sin_phi = math.sin(phi)

            circle_x = radius2 + radius1 * cos_theta
            circle_y = radius1 * sin_theta

            x = (
                circle_x * (cos_b * cos_phi + sin_a * sin_b * sin_phi)
                - circle_y * cos_a * sin_b
            )
            y = (
                circle_x * (sin_b * cos_phi - sin_a * cos_b * sin_phi)
                + circle_y * cos_a * cos_b
            )
            z = distance + cos_a * circle_x * sin_phi + circle_y * sin_a
            inverse_z = 1.0 / z

            xp = int(x_center + scale * inverse_z * x)
            yp = int(y_center - scale * 0.50 * inverse_z * y)

            luminance = (
                cos_phi * cos_theta * sin_b
                - cos_a * cos_theta * sin_phi
                - sin_a * sin_theta
                + cos_b * (cos_a * sin_theta - cos_theta * sin_a * sin_phi)
            )

            if 0 <= xp < width and 0 <= yp < height:
                index = xp + width * yp
                if inverse_z > depth[index]:
                    depth[index] = inverse_z
                    shade = max(0, min(len(SHADES) - 1, int(luminance * 8)))
                    pixels[index] = SHADES[shade]

            phi += 0.07
        theta += 0.02

    rows = ["".join(pixels[row * width : (row + 1) * width]) for row in range(height)]
    return "\n".join(rows)


def main():
    fd = sys.stdin.fileno()
    previous_termios = termios.tcgetattr(fd)
    running = True

    def stop(_signum=None, _frame=None):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    try:
        tty.setcbreak(fd)
        sys.stdout.write("\033[?1049h\033[?25l\033[2J")
        sys.stdout.flush()

        a_angle = 0.0
        b_angle = 0.0
        while running:
            width, height = terminal_size()
            frame = render(width, height, a_angle, b_angle)
            sys.stdout.write("\033[H" + frame)
            sys.stdout.flush()

            ready, _, _ = select.select([sys.stdin], [], [], 0.03)
            if ready:
                key = os.read(fd, 8)
                if key:
                    break

            a_angle += 0.07
            b_angle += 0.03
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous_termios)
        sys.stdout.write("\033[2J\033[H\033[?25h\033[?1049l")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
