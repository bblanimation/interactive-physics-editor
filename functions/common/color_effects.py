# Author: Christopher Gearhart

# System imports
from numba import cuda, jit, prange
import numpy as np
from colorsys import rgb_to_hsv, hsv_to_rgb

# Blender imports
# NONE!

# Module imports
# NONE!


@jit(nopython=True, parallel=True)
def initialize_image_texture(width, height, pixels, channels, new_channels, channel_divisor=1, flip_vertical=False):
    new_pixels = np.empty(width * height * new_channels)
    for i in prange(width * height):
        if flip_vertical:
            x = i / width
            col = round((x % 1) * width)
            row = round(x - (x % 1))
            row = height - row - 1  # here is where the vertical flip happens
            idx2 = (row * width + col) * channels
        else:
            idx2 = i * channels
        if new_channels == 3:
            idx1 = i * 3
            new_pixels[idx1 + 0] = pixels[idx2 + 0] / channel_divisor
            new_pixels[idx1 + 1] = pixels[idx2 + (1 if channels >= 3 else 0)] / channel_divisor
            new_pixels[idx1 + 2] = pixels[idx2 + (2 if channels >= 3 else 0)] / channel_divisor
        else:
            new_pixels[i] = pixels[idx2 + channels - 1] / channel_divisor
    return new_pixels


@jit(nopython=True, parallel=True)
def initialize_gradient_texture(width, height, quadratic):
    pixels = np.empty(width * height)
    for col in prange(height):
        val = 1 - (height - 1 - col) / (height - 1)
        if quadratic:
            val = val ** 0.5
        for row in prange(width):
            pixel_number = width * col + row
            pixels[pixel_number] = val
    return pixels


@jit(nopython=True, parallel=True)
def convert_channels(num_pix, channels, old_pixels, old_channels):
    new_pixels = np.empty(num_pix * channels)
    if channels > old_channels:
        if old_channels == 1:
            for i in prange(num_pix):
                # gamma correct srgb value to linear
                u = old_pixels[i]
                # if u <= 0.04045:
                #     u2 = u / 12.92
                # else:
                #     u2 = ((u + 0.055) / 1.055) ** 2.4
                # store new value to rgb(a) channels
                idx = i * channels
                new_pixels[idx + 0] = u
                new_pixels[idx + 1] = u
                new_pixels[idx + 2] = u
                if channels == 4:
                    new_pixels[idx + 3] = 1
        elif old_channels == 3:
            for i in prange(num_pix):
                idx1 = i * 4
                idx2 = i * 3
                new_pixels[idx1 + 0] = old_pixels[idx2 + 0]
                new_pixels[idx1 + 1] = old_pixels[idx2 + 1]
                new_pixels[idx1 + 2] = old_pixels[idx2 + 2]
                new_pixels[idx1 + 3] = 1
    elif channels < old_channels:
        if channels == 1:
            for i in prange(num_pix):
                # convert rgb to bw
                idx = i * old_channels
                r, g, b = old_pixels[idx:idx + 3]
                u = 0.2126 * r + 0.7152 * g + 0.0722 * b
                # # gamma correct linear value to srgb
                # if u <= 0.0031308:
                #     u2 = 12.92 * u
                # else:
                #     u2 = ((1.055 * u) ** (1 / 2.4)) - 0.055
                # store new value to single channel
                new_pixels[i] = u
        elif channels == 3:
            for i in prange(num_pix):
                idx1 = i * 3
                idx2 = i * 4
                new_pixels[idx1 + 0] = old_pixels[idx2 + 0]
                new_pixels[idx1 + 1] = old_pixels[idx2 + 1]
                new_pixels[idx1 + 2] = old_pixels[idx2 + 2]
    return new_pixels


@jit(nopython=True, parallel=True)
def set_alpha_channel(num_pix, old_pixels, old_channels, value):
    new_pixels = np.empty(num_pix * 4)
    for i in prange(num_pix):
        idx1 = i * 4
        idx2 = i * old_channels
        new_pixels[idx1 + 0] = old_pixels[idx2 + 0]
        new_pixels[idx1 + 1] = old_pixels[idx2 + 1]
        new_pixels[idx1 + 2] = old_pixels[idx2 + 2]
        new_pixels[idx1 + 3] = value
    return new_pixels


@jit(nopython=True, parallel=True)
def resize_pixels(size, channels, old_pixels, old_size):
    new_pixels = np.empty(size[0] * size[1] * channels)
    for col in prange(size[0]):
        col1 = int((col / size[0]) * old_size[0])
        for row in range(size[1]):
            row1 = int((row / size[1]) * old_size[1])
            pixel_number = (size[0] * row + col) * channels
            pixel_number_ref = (old_size[0] * row1 + col1) * channels
            for ch in range(channels):
                new_pixels[pixel_number + ch] = old_pixels[pixel_number_ref + ch]
    return new_pixels


@jit(nopython=True, parallel=True)
def resize_pixels_preserve_borders(size, channels, old_pixels, old_size):
    new_pixels = np.empty(len(old_pixels))
    offset_col = int((old_size[0] - size[0]) / 2)
    offset_row = int((old_size[1] - size[1]) / 2)
    for col in prange(old_size[0]):
        col1 = int(((col - offset_col) / size[0]) * old_size[0])
        for row in range(old_size[1]):
            row1 = int(((row - offset_row) / size[1]) * old_size[1])
            pixel_number = (old_size[0] * row + col) * channels
            if 0 <= col1 < old_size[0] and 0 <= row1 < old_size[1]:
                pixel_number_ref = (old_size[0] * row1 + col1) * channels
                for ch in range(channels):
                    new_pixels[pixel_number + ch] = old_pixels[pixel_number_ref + ch]
            else:
                for ch in range(channels):
                    new_pixels[pixel_number + ch] = 0
    return new_pixels


@jit(nopython=True, parallel=True)
def crop_pixels(size, channels, old_pixels, old_size):
    new_pixels = np.empty(size[0] * size[1] * channels)
    offset_col = (old_size[0] - size[0]) // 2
    offset_row = (old_size[1] - size[1]) // 2
    for col in prange(size[0]):
        col1 = col + offset_col
        for row in range(size[1]):
            row1 = row + offset_row
            pixel_number = (size[0] * row + col) * channels
            pixel_number_ref = (old_size[0] * row1 + col1) * channels
            for ch in range(channels):
                new_pixels[pixel_number + ch] = old_pixels[pixel_number_ref + ch]
    return new_pixels


@jit(nopython=True, parallel=True)
def pad_pixels(size, channels, old_pixels, old_size):
    new_pixels = np.empty(size[0] * size[1] * channels)
    offset_col = (size[0] - old_size[0]) // 2
    offset_row = (size[1] - old_size[1]) // 2
    for col in prange(size[0]):
        col1 = col - offset_col
        for row in range(size[1]):
            row1 = row - offset_row
            pixel_number = (size[0] * row + col) * channels
            for ch in range(channels):
                if 0 <= col1 < old_size[0] and 0 <= row1 < old_size[1]:
                    pixel_number_old = (old_size[0] * row1 + col1) * channels
                    new_pixels[pixel_number + ch] = old_pixels[pixel_number_old + ch]
                else:
                    new_pixels[pixel_number + ch] = 0
    return new_pixels


@jit(nopython=True, parallel=True)
def blend_pixels(im1_pixels, im2_pixels, width, height, channels, operation, use_clamp, factor):
    new_pixels = np.empty(width * height * channels)
    if operation == "MIX":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] * (1 - factor) + im2_pixels[i] * factor
    elif operation == "ADD":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] + im2_pixels[i] * factor
    elif operation == "SUBTRACT":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] - im2_pixels[i] * factor
    elif operation == "MULTIPLY":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] - im2_pixels[i] * factor
    elif operation == "DIVIDE":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] / im2_pixels[i]
    elif operation == "POWER":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] ** im2_pixels[i]
    # elif operation == "LOGARITHM":
    #     for i in prange(new_pixels.size):
    #         new_pixels[i] = math.log(im1_pixels[i], im2_pixels[i])
    elif operation == "SQUARE ROOT":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] ** 0.5
    elif operation == "ABSOLUTE":
        for i in prange(new_pixels.size):
            new_pixels[i] = abs(im1_pixels[i])
    elif operation == "MINIMUM":
        for i in prange(new_pixels.size):
            new_pixels[i] = min(im1_pixels[i], im2_pixels[i])
    elif operation == "MAXIMUM":
        for i in prange(new_pixels.size):
            new_pixels[i] = max(im1_pixels[i], im2_pixels[i])
    elif operation == "LESS THAN":
        for i in prange(new_pixels.size):
            new_pixels[i] = 1 if im1_pixels[i] < im2_pixels[i] else 0
    elif operation == "GREATER THAN":
        for i in prange(new_pixels.size):
            new_pixels[i] = 1 if im1_pixels[i] > im2_pixels[i] else 0
    elif operation == "ROUND":
        for i in prange(new_pixels.size):
            new_pixels[i] = round(im1_pixels[i])
    elif operation == "FLOOR":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] - (im1_pixels[i] % 1)
    elif operation == "CEIL":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] + (1 - (im1_pixels[i] % 1))
    # elif operation == "FRACT":
    #     result =
    elif operation == "MODULO":
        for i in prange(new_pixels.size):
            new_pixels[i] = im1_pixels[i] % im2_pixels[i]

    if use_clamp:
        for i in prange(len(new_pixels)):
            new_pixels[i] = max(0, min(1, new_pixels[i]))
    return new_pixels


@jit(nopython=True, parallel=True)
def math_operation_on_pixels(pixels, operation, clamp, value):
    new_pixels = np.empty(pixels.size)
    if operation == "ADD":
        for i in prange(new_pixels.size):
            new_pixels[i] = pixels[i] + value
    elif operation == "SUBTRACT":
        for i in prange(new_pixels.size):
            new_pixels[i] = pixels[i] - value
    elif operation == "MULTIPLY":
        for i in prange(new_pixels.size):
            new_pixels[i] = pixels[i] * value
    elif operation == "DIVIDE":
        for i in prange(new_pixels.size):
            new_pixels[i] = pixels[i] / value
    elif operation == "POWER":
        for i in prange(new_pixels.size):
            new_pixels[i] = pixels[i] ** value
    # elif operation == "LOGARITHM":
    #     for i in prange(new_pixels.size):
    #         new_pixels[i] = math.log(pixels[i], value)
    elif operation == "SQUARE ROOT":
        for i in prange(new_pixels.size):
            new_pixels[i] = pixels[i] ** 0.5
    elif operation == "ABSOLUTE":
        for i in prange(new_pixels.size):
            new_pixels[i] = abs(pixels[i])
    elif operation == "MINIMUM":
        for i in prange(new_pixels.size):
            new_pixels[i] = min(pixels[i], value)
    elif operation == "MAXIMUM":
        for i in prange(new_pixels.size):
            new_pixels[i] = max(pixels[i], value)
    elif operation == "LESS THAN":
        for i in prange(new_pixels.size):
            new_pixels[i] = 1 if pixels[i] < value else 0
    elif operation == "GREATER THAN":
        for i in prange(new_pixels.size):
            new_pixels[i] = 1 if pixels[i] > value else 0
    elif operation == "ROUND":
        for i in prange(new_pixels.size):
            new_pixels[i] = round(pixels[i])
    elif operation == "FLOOR":
        for i in prange(new_pixels.size):
            new_pixels[i] = pixels[i] - (pixels[i] % 1)
    elif operation == "CEIL":
        for i in prange(new_pixels.size):
            new_pixels[i] = pixels[i] + (1 - (pixels[i] % 1))
    # elif operation == "FRACT":
    #     result =
    elif operation == "MODULO":
        for i in prange(new_pixels.size):
            new_pixels[i] = pixels[i] % value
    # elif operation == "SINE":
    #     result = math.sin(pixels[i])
    # elif operation == "COSINE":
    #     result = math.cos(pixels[i])
    # elif operation == "TANGENT":
    #     result = math.tan(pixels[i])
    # elif operation == "ARCSINE":
    #     result = math.asin(pixels[i])
    # elif operation == "ARCCOSINE":
    #     result = math.acos(pixels[i])
    # elif operation == "ARCTANGENT":
    #     result = math.atan(pixels[i])
    # elif operation == "ARCTAN2":
    #     result = math.atan2(pixels[i], value)

    if clamp:
        for i in prange(new_pixels.size):
            new_pixels[i] = max(0, min(1, new_pixels[i]))
    return new_pixels


@jit(nopython=True, parallel=True)
def clamp_pixels(pixels, minimum, maximum):
    new_pixels = np.empty(pixels.size)
    for i in prange(new_pixels.size):
        new_pixels[i] = max(minimum, min(maximum, pixels[i]))
    return new_pixels


@jit(nopython=True, parallel=True)
def adjust_bright_contrast(pixels, bright, contrast):
    for i in prange(len(pixels)):
        pixels[i] = contrast * (pixels[i] - 0.5) + 0.5 + bright
    return pixels


@jit(nopython=True, parallel=True)
def adjust_hue_saturation_value(pixels, hue, saturation, value):
    hue_adjust = hue - 0.5
    for i in prange(len(pixels) // 3):
        idx = i * 3
        pixels[idx] = (pixels[idx] + hue_adjust) % 1
        pixels[idx + 1] = pixels[idx + 1] * saturation
        pixels[idx + 2] = pixels[idx + 2] * value
    return pixels


@jit(nopython=True, parallel=True)
def invert_pixels(pixels, factor, channels):
    inverted_factor = 1 - factor
    if channels == 4:
        for i in prange(len(pixels)):
            if i % 4 != 3:
                pixels[i] = (inverted_factor * pixels[i]) + (factor * (1 - pixels[i]))
    else:
        for i in prange(len(pixels)):
            pixels[i] = (inverted_factor * pixels[i]) + (factor * (1 - pixels[i]))
    return pixels


@jit(nopython=True, parallel=True)
def dilate_pixels_dist(old_pixels, pixel_dist, width, height):
    mult = 1 if pixel_dist[0] > 0 else -1
    new_pixels = np.empty(len(old_pixels))
    # for i in prange(width * height):
    #     x = i / height
    #     row = round((x % 1) * height)
    #     col = round(x - (x % 1))
    for col in prange(width):
        for row in prange(height):
            pixel_number = width * row + col
            max_val = old_pixels[pixel_number]
            for c in range(-pixel_dist[0], pixel_dist[0] + 1):
                for r in range(-pixel_dist[1], pixel_dist[1] + 1):
                    if not (0 < col + c < width and 0 < row + r < height):
                        continue
                    width_amt = abs(c) / pixel_dist[0]
                    height_amt = abs(r) / pixel_dist[1]
                    ratio = (width_amt - height_amt) / 2 + 0.5
                    weighted_dist = pixel_dist[0] * ratio + ((1 - ratio) * pixel_dist[1])
                    dist = ((abs(c)**2 + abs(r)**2) ** 0.5)
                    if dist > weighted_dist + 0.5:
                        continue
                    pixel_number1 = width * (row + r) + (col + c)
                    cur_val = old_pixels[pixel_number1]
                    if cur_val * mult > max_val * mult:
                        max_val = cur_val
            new_pixels[pixel_number] = max_val
    return new_pixels


@jit(nopython=True, parallel=True)
def dilate_pixels_step(old_pixels, pixel_dist, width, height):
    mult = 1 if pixel_dist[0] > 0 else -1
    new_pixels = np.empty(len(old_pixels))
    # for i in prange(width * height):
    #     x = i / height
    #     row = round((x % 1) * height)
    #     col = round(x - (x % 1))
    for col in prange(width):
        for row in range(height):
            pixel_number = width * row + col
            max_val = old_pixels[pixel_number]
            for c in range(-pixel_dist[0], pixel_dist[0] + 1):
                if not 0 < col + c < width:
                    continue
                pixel_number1 = width * row + (col + c)
                cur_val = old_pixels[pixel_number1]
                if cur_val * mult > max_val * mult:
                    max_val = cur_val
            new_pixels[pixel_number] = max_val
    old_pixels = new_pixels
    new_pixels = np.empty(len(old_pixels))
    for col in prange(width):
        for row in range(height):
            pixel_number = width * row + col
            max_val = old_pixels[pixel_number]
            for r in range(-pixel_dist[1], pixel_dist[1] + 1):
                if not 0 < row + r < height:
                    continue
                pixel_number1 = width * (row + r) + col
                cur_val = old_pixels[pixel_number1]
                if cur_val * mult > max_val * mult:
                    max_val = cur_val
            new_pixels[pixel_number] = max_val
    return new_pixels


@jit(nopython=True, parallel=True)
def flip_pixels(old_pixels, flip_x, flip_y, width, height, channels):
    new_pixels = np.empty(len(old_pixels))
    for col in prange(width):
        col2 = int((width - col - 1) if flip_x else col)
        for row in prange(height):
            idx = (width * row + col) * channels
            row2 = int((height - row - 1) if flip_y else row)
            flipped_idx = (width * row2 + col2) * channels
            new_pixels[idx:idx + channels] = old_pixels[flipped_idx:flipped_idx + channels]
    return new_pixels


@jit(nopython=True, parallel=True)
def scale_pixels(old_pixels, scale_x, scale_y, width, height, channels):
    new_pixels = np.empty(len(old_pixels))
    for col in prange(width):
        col2 = int((width - col - 1) if flip_x else col)
        for row in prange(height):
            idx = (width * row + col) * channels
            row2 = int((height - row - 1) if flip_y else row)
            flipped_idx = (width * row2 + col2) * channels
            new_pixels[idx:idx + channels] = old_pixels[flipped_idx:flipped_idx + channels]
    return new_pixels


@jit(nopython=True, parallel=True)
def translate_pixels(old_pixels, translate_x, translate_y, wrap_x, wrap_y, width, height, channels):
    new_pixels = np.empty(len(old_pixels))
    for col in prange(width):
        col2 = col - translate_x
        if wrap_x:
            col2 = col2 % width
        for row in prange(height):
            row2 = row - translate_y
            if wrap_y:
                row2 = row2 % height
            idx = (width * row + col) * channels
            if not (0 <= row2 < height and 0 <= col2 < width):
                for ch in range(channels):
                    new_pixels[idx + ch] = 0
            else:
                trans_idx = round((width * row2 + col2) * channels)
                new_pixels[idx:idx + channels] = old_pixels[trans_idx:trans_idx + channels]
    return new_pixels
