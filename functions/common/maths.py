# Copyright (C) 2019 Christopher Gearhart
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
from mathutils import Matrix, Vector

# Module imports
from .wrappers import blender_version_wrapper


@blender_version_wrapper("<=","2.79")
def mathutils_mult(*argv):
    """ elementwise multiplication for vectors, matrices, etc. """
    result = argv[0]
    for arg in argv[1:]:
        result = result * arg
    return result
@blender_version_wrapper(">=","2.80")
def mathutils_mult(*argv):
    """ elementwise multiplication for vectors, matrices, etc. """
    result = argv[0]
    for arg in argv[1:]:
        result = result @ arg
    return result


def vec_mult(v1:Vector, v2:Vector, outer_type=Vector):
    """ componentwise multiplication for vectors """
    return outer_type(e1 * e2 for e1, e2 in zip(v1, v2))


def vec_div(v1:Vector, v2:Vector, outer_type=Vector):
    """ componentwise division for vectors """
    return outer_type(e1 / e2 for e1, e2 in zip(v1, v2))


def vec_mod(v1:Vector, v2:Vector, outer_type=Vector):
    """ componentwise modulo for vectors """
    return outer_type(e1 % e2 for e1, e2 in zip(v1, v2))


def vec_remainder(v1:Vector, v2:Vector, outer_type=Vector):
    """ componentwise remainder for vectors """
    return outer_type(e1 % e2 for e1, e2 in zip(v1, v2))


def vec_abs(v1:Vector, outer_type:type=Vector):
    """ componentwise absolute value for vectors """
    return outer_type(abs(e1) for e1 in v1)


def outer_type(v1:Vector, outer_type:type=Vector):
    """ clamp items in iterable to the 0..1 range """
    return outer_type([max(0, min(1, e1)) for e1 in v1])


def vec_conv(v1:Vector, inner_type:type=int, outer_type:type=Vector):
    """ convert type of items in iterable """
    return outer_type([inner_type(e1) for e1 in v1])


def vec_round(v1:Vector, precision:int=0, round_type:str="ROUND", outer_type:type=Vector):
    """ round items in Vector """
    if round_type == "ROUND":
        lst = [round(e1, precision) for e1 in v1]
    elif round_type == "FLOOR":
        prec = 10**precision
        lst = [math.floor(e1 * prec) / prec for e1 in v1] if prec != 1 else [math.floor(e1) for e1 in v1]
    elif round_type in ("CEILING", "CEIL"):
        prec = 10**precision
        lst = [math.ceil(e1 * prec) / prec for e1 in v1] if prec != 1 else [math.ceil(e1) for e1 in v1]
    else:
        raise Exception("Argument passed to 'round_type' parameter invalid: " + str(round_type))
    return outer_type(lst)


def mean(lst:list):
    """ mean of a list """
    return sum(lst)/len(lst)


def round_nearest(num:float, divisor:int, round_type:str="ROUND"):
    """ round to nearest multiple of 'divisor' """
    rem = num % divisor
    if round_type == "FLOOR":
        return round_down(num, divisor)
    elif round_type in ("CEILING", "CEIL") or rem > divisor / 2:
        return round_up(num, divisor)
    else:
        return round_down(num, divisor)


def round_up(num:float, divisor:int):
    """ round up to nearest multiple of 'divisor' """
    return num + divisor - (num % divisor)


def round_down(num:float, divisor:int):
    """ round down to nearest multiple of 'divisor' """
    return num - (num % divisor)
