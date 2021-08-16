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

class PHYSICS_OT_recenter_tolerance_at_origin(Operator, interactive_sim_drawing):
    """ Center the tolerance for the active object at the current location """
    bl_idname = "physics.recenter_tolerance_at_origin"
    bl_label = "Recenter at Origin"
    bl_options = {"REGISTER","UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        return context.object is not None

    def execute(self, context):
        try:
            add_constraints([context.object], loc=self.loc, rot=self.rot)
            return {"RUNNING_MODAL"}
        except:
            interactive_physics_handle_exception()
            return {"CANCELLED"}

    ###################################################
    # class variables

    loc: BoolProperty(default=False)
    rot: BoolProperty(default=False)

    ################################################
