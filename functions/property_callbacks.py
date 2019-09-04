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


def update_lock_loc(self, context):
    context.active_object.lock_location = self.lock_loc


def update_lock_rot(self, context):
    context.active_object.lock_rotation = self.lock_rot


def update_collision_margin(self, context):
    scn = bpy.context.scene
    for obj in scn.objects:
        obj.rigid_body.collision_margin = self.collision_margin


def update_collision_shape(self, context):
    scn = bpy.context.scene
    for obj in scn.objects:
        obj.rigid_body.collision_shape = self.collision_shape


def update_enable_gravity(self, context):
    scn = bpy.context.scene
    scn.use_gravity = self.use_gravity


def update_constraint(self, context):
    scn = bpy.context.scene
    constraints = [obj.constraints["Limit Location"] for obj in scn.objects if "Limit Location" in obj.constraints]
    for constraint in constraints:
        setattr(constraint, )
