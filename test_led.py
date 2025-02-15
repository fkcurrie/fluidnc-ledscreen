#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Display a simple test pattern of 3 shapes on a single 64x32 matrix panel.
Run like this:
$ python test_led.py
"""

# Try the specific import for the alpha version
try:
    from adafruit_blinka_raspberry_pi5_piomatter import (
        PioMatter, 
        Geometry, 
        Orientation, 
        Colorspace,
        Pinout  # Import Pinout separately
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Please check if the package is installed correctly")
    exit(1)

import numpy as np
from PIL import Image, ImageDraw

# Set up display dimensions
width = 64
height = 32

try:
    # Initialize display geometry
    geometry = Geometry(
        width=width, 
        height=height, 
        n_addr_lines=4,
        rotation=Orientation.Normal
    )

    # Create canvas and drawing context
    canvas = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Create framebuffer
    framebuffer = np.asarray(canvas) + 0  # Make a mutable copy

    # Initialize matrix with corrected Pinout reference
    matrix = PioMatter(
        colorspace=Colorspace.RGB888Packed,
        pinout=Pinout.AdafruitMatrixBonnet,  # Changed from PioMatter.Pinout to just Pinout
        framebuffer=framebuffer,
        geometry=geometry
    )

    # Draw test shapes
    draw.rectangle((2, 2, 10, 10), fill=(0, 136, 0))     # Green square
    draw.ellipse((14, 2, 22, 10), fill=(136, 0, 0))      # Red circle
    draw.polygon([(28, 2), (32, 10), (24, 10)], fill=(0, 0, 136))  # Blue triangle

    # Update the display
    framebuffer[:] = np.asarray(canvas)
    matrix.show()

    print("Test pattern should now be visible on the LED matrix")
    input("Press enter to exit")

except Exception as e:
    print(f"Error: {e}")
    print("Please make sure the LED matrix is properly connected") 