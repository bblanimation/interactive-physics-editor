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
def convert_channels(num_pix, channels, old_pixels, old_channels):
    new_pixels = np.empty(num_pix * channels)
    if channels > old_channels:
        if old_channels == 1:
            for i in prange(num_pix):
                # gamma correct srgb value to linear
                u = old_pixels[i]
                if u <= 0.04045:
                    u2 = u / 12.92
                else:
                    u2 = ((u + 0.055) / 1.055) ** 2.4
                # store new value to rgb(a) channels
                idx = i * channels
                new_pixels[idx + 0] = u2
                new_pixels[idx + 1] = u2
                new_pixels[idx + 2] = u2
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
                # gamma correct linear value to srgb
                if u <= 0.0031308:
                    u2 = 12.92 * u
                else:
                    u2 = ((1.055 * u) ** (1 / 2.4)) - 0.055
                # store new value to single channel
                new_pixels[i] = u2
        elif channels == 3:
            for i in prange(num_pix):
                idx1 = i * 3
                idx2 = i * 4
                new_pixels[idx1 + 0] = old_pixels[idx2 + 0]
                new_pixels[idx1 + 1] = old_pixels[idx2 + 1]
                new_pixels[idx1 + 2] = old_pixels[idx2 + 2]
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


# @jit(nopython=True, parallel=True)
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
def blend_pixels(im1_pixels, im2_pixels, size, channels, blend_type, factor):
    new_pixels = np.empty(size[0] * size[1] * channels)
    if blend_type == "MIX":
        for i in prange(len(new_pixels)):
            new_pixels[i] = im1_pixels[i] * (1 - factor) + im2_pixels[i] * factor
    elif blend_type == "ADD":
        for i in prange(len(new_pixels)):
            new_pixels[i] = im1_pixels[i] + im2_pixels[i] * factor
    elif blend_type == "SUBTRACT":
        for i in prange(len(new_pixels)):
            new_pixels[i] = im1_pixels[i] - im2_pixels[i] * factor
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
def dilate_pixels(old_pixels, pixel_dist, step_mode, width, height):
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
                    if not step_mode:
                        width_amt = abs(c) / pixel_dist[0]
                        height_amt = abs(r) / pixel_dist[1]
                        ratio = (width_amt - height_amt) / 2 + 0.5
                        weighted_dist = pixel_dist[0] * ratio + ((1 - ratio) * pixel_dist[1])
                        if ((abs(c)**2 + abs(r)**2) ** 0.5) > weighted_dist + 0.5:
                            continue
                    pixel_number1 = width * (row + r) + (col + c)
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
