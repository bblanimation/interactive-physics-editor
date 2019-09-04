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

# System imports
# NONE!

# Blender imports
import bpy
from bpy.types import Panel

# Addon imports
from ..functions.common import *


class PHYSICS_PT_interactive_editor_object_behavior(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI" if b280() else "TOOLS"
    bl_label       = "Object Settings"
    bl_parent_id   = "PHYSICS_PT_interactive_editor"
    bl_idname      = "PHYSICS_PT_interactive_editor_object_behavior"
    bl_context     = "objectmode"
    bl_category    = "Physics"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        if context.scene.name != "Interactive Physics Session":
            return False
        if bpy.context.active_object is None:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        obj = bpy.context.active_object

        col = layout.column(align=True)
        col.operator("physics.apply_settings_to_selected")

        layout.separator()

        col = layout.column(align=True)
        col.label(text="Rigid Body Type:")
        row = col.row(align=True)
        row.prop(obj.rigid_body, "type", text="")

        layout.separator()

        col = layout.column(align=True)
        col.label(text="Collision Shape:")
        col.prop(obj.rigid_body, "collision_shape", text="")
        col.prop(obj.rigid_body, "collision_margin", text="Margin")

        layout.separator()

        # split = layout_split(layout, factor=0.8, align=True)
        # col = split.column(align=True)
        # col.prop(obj, "lock_location")
        # col = split.column(align=True)
        # col.label(text="")
        # col.label(text="(X)")
        # col.label(text="(Y)")
        # col.label(text="(Z)")
        #
        # split = layout_split(layout, factor=0.8, align=True)
        # col = split.column(align=True)
        # col.prop(obj, "lock_rotation")
        # col = split.column(align=True)
        # col.label(text="")
        # col.label(text="(X)")
        # col.label(text="(Y)")
        # col.label(text="(Z)")

        col = layout.column(align=True)
        col.label(text="Lock Location:")
        row = col.row(align=True)
        row.prop(scn.physics, "lock_loc", toggle=True, text="")

        col = layout.column(align=True)
        col.label(text="Lock Rotation:")
        row = col.row(align=True)
        row.prop(scn.physics, "lock_rot", toggle=True, text="")
