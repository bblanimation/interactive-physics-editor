# Copyright (C) 2018 Christopher Gearhart
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

bl_info = {
    "name"        : "Interactive Physics Editor",
    "author"      : "Christopher Gearhart <chris@bblanimation.com> & Patrick Moore <patrick@d3tool.com>",
    "version"     : (1, 1, 5),
    "blender"     : (2, 83, 0),
    "description" : "Simplifies the process of positioning multiple objects in 3D space with collision handling",
    "location"    : "View 3D > Tools > Physics > Interactive Physics Editor",
    "warning"     : "",  # used for warning icon and text in addons panel
    "wiki_url"    : "https://www.blendermarket.com/products/interactive-physics-editor",
    "tracker_url" : "https://github.com/bblanimation/interactive-physics-editor/issues",
    "category"    : "3D View",
}

# Blender imports
import bpy
from bpy.types import Scene
from bpy.props import *

# Addon imports
from .lib.classes_to_register import *
from .lib.property_groups import *
from .lib.keymaps import add_keymaps
from .functions.common import *
from . import addon_updater_ops

# store keymaps here to access after registration
addon_keymaps = []


def register():
    # register classes
    for cls in classes:
        make_annotations(cls)
        bpy.utils.register_class(cls)

    # register properties
    Scene.physics = PointerProperty(type=PhysicsProperties)
    Object.limit_location = PointerProperty(type=LimitProperties)
    Object.limit_rotation = PointerProperty(type=LimitProperties)

    # handle the keymaps
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon: # check this to avoid errors in background case
        km = wm.keyconfigs.addon.keymaps.new(name="Object Mode", space_type="EMPTY")
        add_keymaps(km)
        addon_keymaps.append(km)

    # addon updater code and configurations
    addon_updater_ops.register(bl_info)

def unregister():
    # unregister addon updater
    addon_updater_ops.unregister()

    # handle the keymaps
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()

    # unregister properties
    del Scene.physics
    del Object.limit_location
    del Object.limit_rotation

    # unregister classes
    for cls in classes:
        bpy.utils.unregister_class(cls)
