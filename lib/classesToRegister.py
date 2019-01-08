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

from ..operators.setup_phys import *
from ..ui import *
from .preferences import *
from .. import addon_updater_ops

classes = (
    # interactive_physics_editor/addon_updater_ops.py
    addon_updater_ops.OBJECT_OT_addon_updater_install_popup,
    addon_updater_ops.OBJECT_OT_addon_updater_check_now,
    addon_updater_ops.OBJECT_OT_addon_updater_update_now,
    addon_updater_ops.OBJECT_OT_addon_updater_update_target,
    addon_updater_ops.OBJECT_OT_addon_updater_install_manually,
    addon_updater_ops.OBJECT_OT_addon_updater_updated_successful,
    addon_updater_ops.OBJECT_OT_addon_updater_restore_backup,
    addon_updater_ops.OBJECT_OT_addon_updater_ignore,
    addon_updater_ops.OBJECT_OT_addon_updater_end_background,
    # interactive_physics_editor/operators
    PHYSICS_OT_setup_interactive_sim,
    # interactive_physics_editor/ui
    PHYSICS_PT_interactive_editor,
    # interactive_physics_editor/lib
    INTERPHYS_PT_preferences,
)
