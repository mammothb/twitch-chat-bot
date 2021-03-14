from colorsys import hls_to_rgb
import random

COLORS = [
    "Blue",
    "BlueViolet",
    "CadetBlue",
    "Chocolate",
    "Coral",
    "DodgerBlue",
    "Firebrick",
    "GoldenRod",
    "Green",
    "HotPink",
    "OrangeRed",
    "Red",
    "SeaGreen",
    "SpringGreen",
    "YellowGreen",
]

CURR_H = 0
DH = 30

def randomize(prime_color):
    global CURR_H
    if prime_color:
        hue = (CURR_H + (0.5 * random.random() + 0.5) * DH) / 360
        saturation = 80 / 100
        luminosity = 60 / 100
        CURR_H += DH
        return "#{:02x}{:02x}{:02x}".format(
            *tuple(clamp(i * 255)
            for i in hls_to_rgb(hue, luminosity, saturation))
        )
    else:
        return random.choice(COLORS)

def clamp(x):
    return int(max(0, min(x, 255)))