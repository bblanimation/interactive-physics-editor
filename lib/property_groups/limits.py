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

# Blender imports
import bpy
from bpy.props import *

# Module imports
from ...functions.property_callbacks import *


class LimitProperties(bpy.types.PropertyGroup):
    use_min_x = BoolProperty(
        name="Min X",
        update=update_constraint,
    )
    use_min_y = BoolProperty(
        name="Min Y",
        update=update_constraint,
    )
    use_min_z = BoolProperty(
        name="Min Z",
        update=update_constraint,
    )
    min_x = FloatProperty(
        name="",
        update=update_constraint,
    )
    min_y = FloatProperty(
        name="",
        update=update_constraint,
    )
    min_z = FloatProperty(
        name="",
        update=update_constraint,
    )
    use_max_x = BoolProperty(
        name="Max X",
        update=update_constraint,
    )
    use_max_y = BoolProperty(
        name="Max Y",
        update=update_constraint,
    )
    use_max_z = BoolProperty(
        name="Max Z",
        update=update_constraint,
    )
    max_x = FloatProperty(
        name="",
        update=update_constraint,
    )
    max_y = FloatProperty(
        name="",
        update=update_constraint,
    )
    max_z = FloatProperty(
        name="",
        update=update_constraint,
    )
