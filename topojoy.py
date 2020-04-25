#!/usr/bin/env python
import sys
import os
import time
import argparse
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter

TARGET_DPI = 72

# argument parsing
parser = argparse.ArgumentParser(description='Converts an image of a topographic map into a ridgeline plot')
parser.add_argument("image")
parser.add_argument("--continuous", "-c", action="store_true", help="instead of only drawing the raised portions, draw each plot line continously for the whole width")
parser.add_argument("--lines", "-l", default=100, help="number of plot lines")
parser.add_argument("--scale", "-s", default=50, help="max elevation difference, higher = larger difference between low and high spots on the map")
parser.add_argument("--line-width", "-w", default=3, help="the width of the plot lines")
parser.add_argument("--roughness", "-r", default=5, help="the smoothing factor, higher = smoother terrain, lower = rougher terrain")
parser.add_argument("--line-color", default="white", help="the color of the lines (https://matplotlib.org/3.1.0/gallery/color/named_colors.html)")
parser.add_argument("--background-color", default="black", help="the color of the background (https://matplotlib.org/3.1.0/gallery/color/named_colors.html)")
args = parser.parse_args()

# global pyplot settings
plt.rcParams['axes.facecolor'] = args.background_color
plt.rcParams['figure.facecolor'] = args.background_color
plt.rcParams['savefig.facecolor'] = args.background_color

start_time = time.time()

# load image
im = Image.open(args.image)
width, height = im.size
# convert to 2D array of hue values
im_hsv = im.convert('HSV')
hsv_arr = np.array(im_hsv)
huemap = hsv_arr[:,:,:1]

# I'm assuming that high elevations are red (~0°),
# low elevations are green (~80°) and water is blue (~150°).
# Red with a blue content could also be at the upper end of the hue circle so i'm just setting it to 1°
huemap[huemap > 300] = 0
# To make the difference between water and land not to high I'm capping the maximum hue
huemap[huemap > 120] = 120

# scale the hue values to be in the range from 0 to 1
scaled = (huemap - np.min(huemap)) / (np.max(huemap) - np.min(huemap))
# invert it because in our case a higher hue value means a lower elevation value
scaled *= -1
# since our data is now in the range [0; -1] lets add 1 to bring it to [1; 0]
scaled += 1
# at last scale it with our custom scaling factor to increase the difference between low and high elevations
scaled *= args.scale
# add a blur to smooth the curves
filtered = gaussian_filter(scaled, sigma=args.roughness)

# plot the curves
t = np.linspace(0, width, filtered.shape[1])
plt.figure(figsize=(width/TARGET_DPI, height/TARGET_DPI), dpi=TARGET_DPI)
# we only want to draw every n-th line where n equals the height of the image divided by the number of lines we want
nth_line = np.floor(height / args.lines)
for y in range(0, height):
    if y % nth_line == 0:
        yoff = height - y
        if args.continuous:
            # if continous mode is on we can just plot a single row of out elevation map
            plt.plot(t, filtered[y] + yoff, color=args.line_color, linewidth=args.line_width)
        else:
            # otherwise we have to draw individual segments and hide the ones that are below the threshold
            for px1, px2, py1, py2 in zip(t, t[1:], filtered[y], filtered[y][1:]):
                line_color = args.background_color
                if py1 >= 0.5:
                    line_color = args.line_color
                    plt.plot([px1, px2], [py1 + yoff, py2 + yoff], color=line_color, linewidth=args.line_width)
        print("[{}%] Plotting...    ".format(round(y/height*100)), end="\r")

end_time = time.time()
print("Plotting finished ({}s)".format(round(end_time - start_time, 3)))

plt.grid(False)
plt.axis("off")
save_file_name = "{}-l{}-s{}-b{}-w{}.png".format(os.path.basename(args.image), args.lines, args.scale, args.roughness, args.line_width)
plt.savefig(save_file_name, dpi=TARGET_DPI)
print("Saved to {}".format(save_file_name))
os.startfile(save_file_name, 'open')