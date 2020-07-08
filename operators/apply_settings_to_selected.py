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

# Blender imports
import bpy
from bpy.types import Operator
from mathutils import Matrix, Vector

# Addon imports
from .setup_phys_drawing import *
from ..functions import *

class PHYSICS_OT_apply_settings_to_selected(Operator, interactive_sim_drawing):
    """ Apply rigid body settings (type, collision shape) to selected objects """
    bl_idname = "physics.apply_settings_to_selected"
    bl_label = "Apply Settings to Selected"
    bl_options = {"REGISTER","UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 0 and context.active_object is not None and context.scene.name == "Interactive Physics Session"

    def execute(self, context):
        try:
            active_obj = context.active_object
            for obj in context.selected_objects:
                obj.lock_location = active_obj.lock_location
                obj.lock_rotation = active_obj.lock_rotation
                if obj.rigid_body is not None and active_obj.rigid_body is not None:
                    obj.rigid_body.type = active_obj.rigid_body.type
                    obj.rigid_body.collision_shape = active_obj.rigid_body.collision_shape
                    obj.rigid_body.collision_margin = active_obj.rigid_body.collision_margin
            return {"FINISHED"}
        except:
            interactive_physics_handle_exception()
            return {"CANCELLED"}

    #############################################
