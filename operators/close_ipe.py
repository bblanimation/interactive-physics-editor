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

class PHYSICS_OT_close_ipe(Operator, interactive_sim_drawing):
    """ Close current Interactive Physics Editor session """
    bl_idname = "physics.close_ipe"
    bl_label = "Close Session"
    bl_options = {"REGISTER","UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        return True

    def execute(self, context):
        try:
            context.scene.physics.status = self.status
            return {"FINISHED"}
        except:
            interactive_physics_handle_exception()
            return {"CANCELLED"}

    ###################################################
    # class variables

    status: EnumProperty(
        items=[
            ("CLOSE", "Close", "", 0),
            ("CANCEL", "Cancel", "", 1),
        ]
    )

    #############################################
