# Author: Christopher Gearhart

# System imports
from numba import cuda, jit, prange
import numpy as np
from colorsys import rgb_to_hsv, hsv_to_rgb

# Blender imports
# NONE!

# Module imports
# NONE!

import os
os.environ['NUMBAPRO_NVVM']      = r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v10.1\nvvm\bin\nvvm64_33_0.dll'
os.environ['NUMBAPRO_LIBDEVICE'] = r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v10.1\nvvm\libdevice'


# @jit(nopython=True, parallel=True)
@cuda.jit('void(float64[:], float64[:], int32[:], int32[:], int32)')
def pad_pixels_cuda(new_pixels, old_pixels, size, old_size, channels):
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


@cuda.jit('void(float64[:], float64[:], float64[:], int32, int32, int32, bool_, float64)')
def blend_pixels_cuda(new_pixels, im1_pixels, im2_pixels, width, height, blend_type, use_clamp, factor):
    # Compute flattened index inside the array
    pos = cuda.grid(1)
    if pos < new_pixels.size:  # Check array boundaries
        # MIX
        if blend_type == 0:
            new_pixels[pos] = im1_pixels[pos] * (1 - factor) + im2_pixels[pos] * factor
        # ADD
        elif blend_type == 1:
            new_pixels[pos] = im1_pixels[pos] + im2_pixels[pos] * factor
        # SUBTRACT
        elif blend_type == 2:
            new_pixels[pos] = im1_pixels[pos] - im2_pixels[pos] * factor
        # CLAMP
        if use_clamp:
            new_pixels[pos] = min(1, new_pixels[pos])


@cuda.jit#('void(float64[:], float64, float64)')
def adjust_bright_contrast_cuda(pixels, bright, contrast):
    # Compute flattened index inside the array
    pos = cuda.grid(1)
    if pos < pixels.size:  # Check array boundaries
        # apply brightness and contrast
        pixels[pos] = contrast * (pixels[pos] - 0.5) + 0.5 + bright


@cuda.jit('void(float64[:], float64[:], int32[:], bool_, int32, int32)')
def dilate_pixels_cuda(new_pixels, old_pixels, pixel_dist, dist_method, width, height):
    mult = 1 if pixel_dist[0] > 0 else -1
    # Compute flattened index inside the array
    pos = cuda.grid(1)
    if pos < new_pixels.size:  # Check array boundaries
        # get current row/column
        x = pos / height
        row = round((x % 1) * height)
        col = round(x - (x % 1))
        pixel_number = width * row + col
        # compute maximum surrounding value at pixel number
        max_val = old_pixels[pixel_number]
        for c in range(-pixel_dist[0], pixel_dist[0] + 1):
            for r in range(-pixel_dist[1], pixel_dist[1] + 1):
                if not (0 < col + c < width and 0 < row + r < height):
                    continue
                if dist_method:
                    width_amt = abs(c) / pixel_dist[0]
                    height_amt = abs(r) / pixel_dist[1]
                    ratio = (width_amt - height_amt) / 2 + 0.5
                    weighted_dist = pixel_dist[0] * ratio + ((1 - ratio) * pixel_dist[1])
                    dist = (c**2 + r**2) ** 0.5
                    if dist > weighted_dist + 0.5:
                        continue
                pixel_number1 = width * (row + r) + (col + c)
                cur_val = old_pixels[pixel_number1]
                if cur_val * mult > max_val * mult:
                    max_val = cur_val
        new_pixels[pixel_number] = max_val


def get_gpu_info(array_size, stream=None):
    threadsperblock = 1024
    blockspergrid = (array_size + threadsperblock - 1) // threadsperblock
    if stream:
        return blockspergrid, threadsperblock, stream
    else:
        return blockspergrid, threadsperblock
