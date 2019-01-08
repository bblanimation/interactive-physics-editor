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
from bpy.types import Panel

class PHYSICS_PT_interactive_editor(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Interactive Physics Editor"
    bl_idname      = "VIEW3D_PT_interactive_editor"
    bl_context     = "objectmode"
    bl_category    = "Physics"

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        col = layout.column(align=True)
        if context.scene.name != "Interactive Physics Session":
            col.operator("physics.setup_interactive_sim", text="New Interactive Physics Session", icon="PHYSICS")
        else:
            col.label("Object Behavior:")
            split = col.split(align=True)
            col = split.column(align=True)
            col.operator("rigidbody.objects_add", text="Make Active").type = 'ACTIVE'
            col = split.column(align=True)
            col.operator("rigidbody.objects_add", text="Make Passive").type = 'PASSIVE'

            col = layout.column(align=True)
            split = col.split(align=True)
            col = split.column(align=True)
            col.label("Location")
            col.prop(scn, "phys_lock_loc_x")
            col.prop(scn, "phys_lock_loc_y")
            col.prop(scn, "phys_lock_loc_z")
            col = split.column(align=True)
            col.label("Rotation")
            col.prop(scn, "phys_lock_rot_x")
            col.prop(scn, "phys_lock_rot_y")
            col.prop(scn, "phys_lock_rot_z")

            col = layout.column(align=True)
            col.prop(scn, "phys_collision_margin")

            layout.split()
            col = layout.column(align=True)
            col.scale_y = 0.7
            col.label("Press 'RETURN' to commit")
            col.label("Press 'ESC' to cancel")
