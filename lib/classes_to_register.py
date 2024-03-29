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

from ..operators import *
from ..ui import *
from .property_groups import *
from .preferences import *
from .report_error import *

classes = (
    # property groups
    LimitProperties,
    PhysicsProperties,
    # operators
    PHYSICS_OT_apply_settings_to_selected,
    PHYSICS_OT_close_ipe,
    PHYSICS_OT_recenter_tolerance_at_origin,
    PHYSICS_OT_setup_and_run_ipe,
    # ui
    PHYSICS_PT_interactive_editor,
    # PHYSICS_PT_interactive_editor_object_behavior,
    PHYSICS_PT_interactive_editor_rbw,
    PHYSICS_PT_interactive_editor_rbw_gravity,
    PHYSICS_PT_interactive_editor_limit_location,
    PHYSICS_PT_interactive_editor_limit_rotation,
    PHYSICS_PT_editor_actions,
    # lib
    # INTERPHYS_PT_preferences,
    SCENE_OT_report_error,
    SCENE_OT_close_report_error,
)
