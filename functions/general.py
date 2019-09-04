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


def add_constraints(objs, min_shift=(0, 0, 0), max_shift=(0, 0, 0), use_limits=[False, False, False, False, False, False]):
    for obj in objs:
        if obj.type != "MESH": continue

        limit = obj.constraints.get("Limit Location")
        if limit is not None:
            obj.constraints.remove(limit)
        limit = obj.constraints.new("LIMIT_LOCATION")

        imx = obj.matrix_world.inverted()
        world_loc = obj.matrix_world.to_translation()
        rot = obj.matrix_world.to_quaternion()

        X = world_loc.dot(mathutils_mult(rot, Vector((1, 0, 0))))
        Y = world_loc.dot(mathutils_mult(rot, Vector((0, 1, 0))))
        Z = world_loc.dot(mathutils_mult(rot, Vector((0, 0, 1))))

        limit.use_min_x = use_limits[0]
        limit.use_min_y = use_limits[1]
        limit.use_min_z = use_limits[2]
        limit.use_max_x = use_limits[3]
        limit.use_max_y = use_limits[4]
        limit.use_max_z = use_limits[5]
        limit.use_transform_limit = False

        limit.owner_space = "LOCAL"
        limit.min_x, limit.max_x = X + min_shift[0], X + max_shift[0]
        limit.min_y, limit.max_y = Y + min_shift[1], Y + max_shift[1]
        limit.min_z, limit.max_z = Z + min_shift[2], Z + max_shift[2]
