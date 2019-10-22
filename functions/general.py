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

from .common import *

@blender_version_wrapper("<=", "2.79")
def get_quadview_index(context, x, y):
    for area in context.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        is_quadview = len(area.spaces.active.region_quadviews) == 0
        i = -1
        for region in area.regions:
            if region.type == 'TOOLS':
                if (x >= region.x and
                    y >= region.y and
                    x < region.width + region.x and
                    y < region.height + region.y):

                    return ("TOOLS", None)
            if region.type == 'WINDOW':
                i += 1
                if (x >= region.x and
                    y >= region.y and
                    x < region.width + region.x and
                    y < region.height + region.y):

                    return (area.spaces.active, None if is_quadview else i)
    return (None, None)
@blender_version_wrapper(">=", "2.80")
def get_quadview_index(context, x, y):
    for area in context.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        is_quadview = len(area.spaces.active.region_quadviews) == 0
        i = -1
        for region in area.regions:
            if (x >= region.x and
                y >= region.y and
                x < region.width + region.x and
                y < region.height + region.y):
                if region.type == 'WINDOW':
                    return (area.spaces.active, None if is_quadview else i)
                elif region.type == 'UI':
                    return ("UI", None)
    return (None, None)

def interactive_physics_handle_exception():
    handle_exception(log_name="Interactive Physics Editor log", report_button_loc="Physics > Interactive Physics Editor > Report Error")


def add_constraints(objs, loc=True, rot=True):
    for obj in objs:
        if obj.type != "MESH": continue

        if loc:
            constraint = obj.constraints.get("Limit Location")
            if constraint is not None:
                obj.constraints.remove(constraint)
            constraint = obj.constraints.new("LIMIT_LOCATION")
            constraint.owner_space = "LOCAL"
            constraint.use_transform_limit = False

            # imx = obj.matrix_world.inverted()
            world_loc = obj.matrix_world.to_translation()
            rot = obj.matrix_world.to_quaternion()

            X = world_loc.dot(mathutils_mult(rot, Vector((1, 0, 0))))
            Y = world_loc.dot(mathutils_mult(rot, Vector((0, 1, 0))))
            Z = world_loc.dot(mathutils_mult(rot, Vector((0, 0, 1))))

            update_loc_constraint(obj, constraint, (X, Y, Z))

        if rot:
            constraint = obj.constraints.get("Limit Rotation")
            if constraint is not None:
                obj.constraints.remove(constraint)
            constraint = obj.constraints.new("LIMIT_ROTATION")
            constraint.use_transform_limit = False

            update_rot_constraint(obj, constraint, obj.matrix_world.to_euler())


def update_loc_constraint(obj, constraint, limit):
    tolerance = obj.limit_location.loc_tolerance

    constraint.use_min_x = bool(tolerance[0])
    constraint.use_max_x = bool(tolerance[0])
    constraint.use_min_y = bool(tolerance[1])
    constraint.use_max_y = bool(tolerance[1])
    constraint.use_min_z = bool(tolerance[2])
    constraint.use_max_z = bool(tolerance[2])

    constraint.min_x, constraint.max_x = limit[0] - tolerance[0], limit[0] + tolerance[0]
    constraint.min_y, constraint.max_y = limit[1] - tolerance[1], limit[1] + tolerance[1]
    constraint.min_z, constraint.max_z = limit[2] - tolerance[2], limit[2] + tolerance[2]


def update_rot_constraint(obj, constraint, limit):
    tolerance = obj.limit_location.rot_tolerance

    constraint.use_limit_x = bool(tolerance[0])
    constraint.use_limit_y = bool(tolerance[1])
    constraint.use_limit_z = bool(tolerance[2])

    constraint.min_x, constraint.max_x = limit[0] - tolerance[0], limit[0] + tolerance[0]
    constraint.min_y, constraint.max_y = limit[1] - tolerance[1], limit[1] + tolerance[1]
    constraint.min_z, constraint.max_z = limit[2] - tolerance[2], limit[2] + tolerance[2]
