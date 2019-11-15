# Copyright (C) 2020 Christopher Gearhart
# chris@bblanimation.com
# http://bblanimation.com/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# System imports
import math

# Blender imports
import bpy
from mathutils import Matrix, Vector

# Module imports
# NONE!


def get_saturation_matrix(s:float):
    """ returns saturation matrix from saturation value """
    sr = (1 - s) * 0.3086  # or 0.2125
    sg = (1 - s) * 0.6094  # or 0.7154
    sb = (1 - s) * 0.0820  # or 0.0721
    return Matrix(((sr + s, sr, sr), (sg, sg + s, sg), (sb, sb, sb + s)))


def gamma_correct(rgba:list, val:float=2.0167):
    """ gamma correct color by value """
    r, g, b, a = rgba
    r = math.pow(r, val)
    g = math.pow(g, val)
    b = math.pow(b, val)
    return [r, g, b, a]


def gamma_correct_linear_to_srgb(color:list):
    """ gamma correct color from linear to sRGB """
    new_color = list()
    # see https://en.wikipedia.org/wiki/SRGB#The_forward_transformation_(CIE_XYZ_to_sRGB)
    for u in color:
        if u <= 0.0031308:
            u2 = 12.92 * u
        else:
            u2 = (1.055 * u) ** (1 / 2.4) - 0.055
        new_color.append(u2)
    return new_color


def gamma_correct_srgb_to_linear(color:list):
    """ gamma correct color from sRGB to linear """
    new_color = list()
    # see https://en.wikipedia.org/wiki/SRGB#The_reverse_transformation
    for u in color:
        if u <= 0.04045:
            u2 = u / 12.92
        else:
            u2 = ((u + 0.055) / 1.055) ** 2.4
        new_color.append(u2)
    return new_color


def rgb_to_bw(color:list, gamma_correct:bool=True):
    r, g, b = color[:3]
    new_color = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if gamma_correct:
        new_color = gamma_correct_linear_to_srgb([new_color])[0]
    return new_color


def get_average(rgba0:Vector, rgba1:Vector, weight:float):
    """ returns weighted average of two rgba values """
    return (rgba1 * weight + rgba0) / (weight + 1)


def rgba_distance(c1, c2, awt=1):
    r1, g1, b1, a1 = c1
    r2, g2, b2, a2 = c2
    # a1 = c1[3]
    # # r1, g1, b1 = rgb_to_lab(c1[:3])
    # r1, g1, b1 = colorsys.rgb_to_hsv(r1, g1, b1)
    # a2 = c2[3]
    # # r2, g2, b2 = rgb_to_lab(c2[:3])
    # r2, g2, b2 = colorsys.rgb_to_hsv(r1, g1, b1)
    # diff =  0.33 * ((r1 - r2)**2)
    # diff += 0.33 * ((g1 - g2)**2)
    # diff += 0.33 * ((b1 - b2)**2)
    # diff += 1.0 * ((a1 - a2)**2)
    diff =  0.30 * ((r1 - r2)**2)
    diff += 0.59 * ((g1 - g2)**2)
    diff += 0.11 * ((b1 - b2)**2)
    diff += awt * ((a1 - a2)**2)
    return diff
