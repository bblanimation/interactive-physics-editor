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


class PHYSICS_PT_interactive_editor(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI" if b280() else "TOOLS"
    bl_label       = "Interactive Physics Editor"
    bl_idname      = "PHYSICS_PT_interactive_editor"
    bl_context     = "objectmode"
    bl_category    = "Physics"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        if bpy.data.texts.find("Interactive Physics Editor log") >= 0:
            split = layout_split(layout, factor=0.9)
            col = split.column(align=True)
            row = col.row(align=True)
            row.operator("interactive_physics_editor.report_error", text="Report Error", icon="URL")
            col = split.column(align=True)
            row = col.row(align=True)
            row.operator("interactive_physics_editor.close_report_error", text="", icon="PANEL_CLOSE")

        col = layout.column(align=True)
        if context.scene.name != "Interactive Physics Session":
            col.operator("physics.setup_interactive_sim", text="New Interactive Physics Session", icon="PHYSICS")
        else:
            layout.split()
            col = layout.column(align=True)
            col.scale_y = 0.7
            col.label(text="Press 'RETURN' to commit")
            col.label(text="Press 'ESC' to cancel")


class PHYSICS_PT_interactive_editor_gravity(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI" if b280() else "TOOLS"
    bl_label       = "Gravity"
    bl_parent_id   = "PHYSICS_PT_interactive_editor"
    bl_idname      = "PHYSICS_PT_interactive_editor_gravity"
    bl_context     = "objectmode"
    bl_category    = "Physics"
    # bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        return context.scene.name == "Interactive Physics Session"

    def draw_header(self, context):
        scn = context.scene
        self.layout.prop(scn.physics, "use_gravity", text="")

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        col = layout.column(align=True)
        # col.prop(scn.physics, "use_gravity", text="Enable Gravity")
        # row = col.row(align=True)
        col.active = scn.use_gravity and scn.physics.use_gravity
        col.prop(scn, "gravity", text="")


class PHYSICS_PT_interactive_editor_limit_location(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI" if b280() else "TOOLS"
    bl_label       = "Limit Location"
    bl_parent_id   = "PHYSICS_PT_interactive_editor"
    bl_idname      = "PHYSICS_PT_interactive_editor_limit_location"
    bl_context     = "objectmode"
    bl_category    = "Physics"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        if context.scene.name != "Interactive Physics Session":
            return False
        if context.active_object is None:
            return False
        return True

    # def draw_header(self, context):
    #     scn = context.scene
    #     self.layout.prop(scn.physics, "use_gravity", text="")

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        col = layout.column()
        row = col.row()
        row.prop(scn.physics.limit_location, "use_min_x")
        row.prop(scn.physics.limit_location, "use_min_y")
        row.prop(scn.physics.limit_location, "use_min_z")
        row = col.row()
        row.prop(scn.physics.limit_location, "min_x")
        row.prop(scn.physics.limit_location, "min_y")
        row.prop(scn.physics.limit_location, "min_z")

        col = layout.column()
        row = col.row()
        row.prop(scn.physics.limit_location, "use_max_x")
        row.prop(scn.physics.limit_location, "use_max_y")
        row.prop(scn.physics.limit_location, "use_max_z")
        row = col.row()
        row.prop(scn.physics.limit_location, "max_x")
        row.prop(scn.physics.limit_location, "max_y")
        row.prop(scn.physics.limit_location, "max_z")


class PHYSICS_PT_interactive_editor_limit_rotation(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI" if b280() else "TOOLS"
    bl_label       = "Limit Rotation"
    bl_parent_id   = "PHYSICS_PT_interactive_editor"
    bl_idname      = "PHYSICS_PT_interactive_editor_limit_rotation"
    bl_context     = "objectmode"
    bl_category    = "Physics"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        if context.scene.name != "Interactive Physics Session":
            return False
        if context.active_object is None:
            return False
        return True

    # def draw_header(self, context):
    #     scn = context.scene
    #     self.layout.prop(scn.physics, "use_gravity", text="")

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        col = layout.column()
        row = col.row()
        row.prop(scn.physics.limit_rotation, "use_min_x")
        row.prop(scn.physics.limit_rotation, "use_min_y")
        row.prop(scn.physics.limit_rotation, "use_min_z")
        row = col.row()
        row.prop(scn.physics.limit_rotation, "min_x")
        row.prop(scn.physics.limit_rotation, "min_y")
        row.prop(scn.physics.limit_rotation, "min_z")

        col = layout.column()
        row = col.row()
        row.prop(scn.physics.limit_rotation, "use_max_x")
        row.prop(scn.physics.limit_rotation, "use_max_y")
        row.prop(scn.physics.limit_rotation, "use_max_z")
        row = col.row()
        row.prop(scn.physics.limit_rotation, "max_x")
        row.prop(scn.physics.limit_rotation, "max_y")
        row.prop(scn.physics.limit_rotation, "max_z")
