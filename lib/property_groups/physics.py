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
from .limits import *
from ...functions.property_callbacks import *


class PhysicsProperties(bpy.types.PropertyGroup):
    lock_loc: BoolVectorProperty(
        name="Lock",
        size=3,
        subtype="XYZ",
        update=update_lock_loc,
        default=(False, False, False),
        )
    lock_rot: BoolVectorProperty(
        name="Lock",
        size=3,
        subtype="XYZ",
        update=update_lock_rot,
        default=(True, True, True),
        )
    collision_margin: FloatProperty(
        name="Collision Margin",
        min=-1, max=1,
        step=1,
        update=update_collision_margin,
        default=0.0,
    )
    collision_shape: EnumProperty(
        name="Collision Shape",
        items=[
            ("CONVEX_HULL", "Convex (fast)", "Objects collide with other objects using a convex collision shape"),
            ("MESH", "Concave", "Objects collide with other objects using a concave collision shape (best for hollow objects)"),
        ],
        update=update_collision_shape,
        default="MESH",
    )
    use_gravity: BoolProperty(
        name="Use Gravity",
        update=update_enable_gravity,
        default=False,
    )
    status: EnumProperty(
        name="Interactive Physics Editor state",
        items=[
            ("RUNNING", "Running", "", 0),
            ("CLOSE", "Close", "", 1),
            ("CANCEL", "Cancel", "", 2),
        ],
        default="RUNNING",
    )
