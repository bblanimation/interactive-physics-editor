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
            split.operator("interactive_physics_editor.report_error", text="Report Error", icon="URL")
            split.operator("interactive_physics_editor.close_report_error", text="", icon="PANEL_CLOSE")

        col = layout.column(align=True)
        if context.scene.name != "Interactive Physics Session":
            col.operator("physics.setup_ipe", text="New Interactive Physics Session", icon="PHYSICS")
        else:
            obj = bpy.context.active_object
            if obj is None or obj.rigid_body is None:
                col.label(text="Object is not rigid body")
                return

            col = layout.column(align=True)
            col.label(text="Rigid Body:")
            col.prop(obj.rigid_body, "type", text="")
            col.prop(obj.rigid_body, "friction", text="Friction")

            # layout.separator()

            col = layout.column(align=True)
            col.label(text="Collision Shape:")
            col.prop(obj.rigid_body, "collision_shape", text="")
            col.prop(obj.rigid_body, "collision_margin", text="Margin")

            # layout.separator()
            #
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

            layout.separator()

            col = layout.column(align=True)
            col.operator("physics.apply_settings_to_selected")

            layout.split()
            col = layout.column(align=True)
            col.scale_y = 0.7
            col.label(text="Press 'SHIFT' + 'RETURN' to commit")
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

        # layout.prop(scn.physics, "use_gravity", text="Enable Gravity")
        layout.active = scn.use_gravity and scn.physics.use_gravity
        layout.prop(scn, "gravity", text="")


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
    #     self.layout.prop(scn.physics, text="")

    def draw(self, context):
        layout = self.layout
        obj = context.object

        layout.prop(obj.constraints["Limit Location"], "owner_space", text="Convert")

        row = layout.row(align=False)
        col = row.column(align=True)
        col.active = not obj.lock_location[0]
        col.prop(obj.limit_location, "loc_tolerance", text="Tol X", index=0)
        row.prop(obj, "lock_location", text="", index=0)

        row = layout.row(align=False)
        col = row.column(align=True)
        col.active = not obj.lock_location[1]
        col.prop(obj.limit_location, "loc_tolerance", text="Tol Y", index=1)
        row.prop(obj, "lock_location", text="", index=1)

        row = layout.row(align=False)
        col = row.column(align=True)
        col.active = not obj.lock_location[2]
        col.prop(obj.limit_location, "loc_tolerance", text="Tol Z", index=2)
        row.prop(obj, "lock_location", text="", index=2)

        layout.operator("physics.recenter_tolerance_at_origin", icon="OBJECT_ORIGIN" if b280() else "OUTLINER_DATA_EMPTY").loc = True


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
        obj = context.object

        row = layout.row(align=False)
        col = row.column(align=True)
        col.active = not obj.lock_rotation[0]
        col.prop(obj.limit_location, "rot_tolerance", text="Tol X", index=0)
        row.prop(obj, "lock_rotation", text="", index=0)

        row = layout.row(align=False)
        col = row.column(align=True)
        col.active = not obj.lock_rotation[1]
        col.prop(obj.limit_location, "rot_tolerance", text="Tol Y", index=1)
        row.prop(obj, "lock_rotation", text="", index=1)

        row = layout.row(align=False)
        col = row.column(align=True)
        col.active = not obj.lock_rotation[2]
        col.prop(obj.limit_location, "rot_tolerance", text="Tol Z", index=2)
        row.prop(obj, "lock_rotation", text="", index=2)

        layout.operator("physics.recenter_tolerance_at_origin", icon="OBJECT_ORIGIN" if b280() else "OUTLINER_DATA_EMPTY").rot = True


class PHYSICS_PT_editor_actions(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI" if b280() else "TOOLS"
    bl_label       = "Editor Actions"
    bl_idname      = "PHYSICS_PT_editor_actions"
    bl_context     = "objectmode"
    bl_category    = "Physics"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        if context.scene.name != "Interactive Physics Session":
            return False
        return True

    def draw(self, context):
        layout = self.layout
        layout.operator("physics.close_ipe", text="Close Session", icon="FILE_TICK").status = "CLOSE"
        layout.operator("physics.close_ipe", text="Cancel Session", icon="PANEL_CLOSE").status = "CANCEL"
