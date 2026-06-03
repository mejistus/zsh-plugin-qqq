#!/usr/bin/env python3
import math
import os
import select
import signal
import sys
import termios
import time
import tty
from datetime import datetime


SHADES = ".,-~:;=!*#$@"
FONT = {
    "0": ("#####", "#   #", "#   #", "#   #", "#####"),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "#####"),
    "2": ("#####", "    #", "#####", "#    ", "#####"),
    "3": ("#####", "    #", "#####", "    #", "#####"),
    "4": ("#   #", "#   #", "#####", "    #", "    #"),
    "5": ("#####", "#    ", "#####", "    #", "#####"),
    "6": ("#####", "#    ", "#####", "#   #", "#####"),
    "7": ("#####", "    #", "   # ", "  #  ", "  #  "),
    "8": ("#####", "#   #", "#####", "#   #", "#####"),
    "9": ("#####", "#   #", "#####", "    #", "#####"),
    "-": ("     ", "     ", "#####", "     ", "     "),
    ":": ("     ", "  #  ", "     ", "  #  ", "     "),
    " ": ("     ", "     ", "     ", "     ", "     "),
}


def terminal_size():
    size = os.get_terminal_size()
    return max(size.columns, 20), max(size.lines, 10)


def put_text(pixels, width, height, x, y, rows):
    for row_index, row in enumerate(rows):
        yp = y + row_index
        if not 0 <= yp < height:
            continue
        for column_index, char in enumerate(row):
            xp = x + column_index
            if char != " " and 0 <= xp < width:
                pixels[xp + width * yp] = char


def ascii_text(text):
    rows = [""] * 5
    for char_index, char in enumerate(text):
        glyph = FONT.get(char)
        if glyph is None:
            continue
        for row_index, row in enumerate(glyph):
            rows[row_index] += row
            if char_index != len(text) - 1:
                rows[row_index] += " "
    return rows


def centered_rows(rows, width):
    centered = []
    for row in rows:
        if len(row) > width:
            centered.append(row[:width])
            continue
        centered.append(row.center(width))
    return centered


def current_label_rows(width):
    now = datetime.now()
    date_text = now.strftime("%Y-%m-%d")
    time_text = now.strftime("%H:%M:%S")

    if len(ascii_text(date_text)[0]) > width:
        date_text = now.strftime("%m-%d")
    if len(ascii_text(time_text)[0]) > width:
        time_text = now.strftime("%H:%M")

    rows = centered_rows(ascii_text(date_text), width)
    rows += [" " * width]
    rows += centered_rows(ascii_text(time_text), width)
    return rows


def render(width, height, a_angle, b_angle):
    pixels = [" "] * (width * height)
    depth = [0.0] * (width * height)
    label_rows = current_label_rows(width) if height >= 18 and width >= 32 else []
    label_height = len(label_rows)

    cos_a = math.cos(a_angle)
    sin_a = math.sin(a_angle)
    cos_b = math.cos(b_angle)
    sin_b = math.sin(b_angle)

    radius1 = 1.0
    radius2 = 2.0
    distance = 5.0
    donut_height = height - label_height - 2 if label_rows else height
    scale = min(width * 0.50, max(donut_height, 8) * 1.05)
    x_center = width // 2
    y_center = max(0, donut_height // 2)

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

    if label_rows:
        label_y = max(0, height - label_height - 1)
        put_text(pixels, width, height, 0, label_y, label_rows)

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
