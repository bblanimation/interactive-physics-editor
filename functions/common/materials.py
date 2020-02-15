# Copyright (C) 2020 Christopher Gearhart
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
import math

# Blender imports
import bpy
from mathutils import Matrix, Vector

# Module imports
from .maths import *
from .reporting import *


def clear_existing_materials(obj, from_idx=0, from_data=False):
    if from_data:
        obj.data.materials.clear()
    else:
        select(obj, active=True)
        obj.active_material_index = from_idx
        for i in range(from_idx, len(obj.material_slots)):
            # remove material slots
            bpy.ops.object.material_slot_remove()


def set_material(obj, mat, to_data=False, overwrite=True):
    if len(obj.data.materials) == 1 and overwrite:
        if obj.data.materials[0] != mat:
            obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    if not to_data:
        link_material_to_object(obj, mat)


def link_material_to_object(obj, mat, index=-1):
    obj.material_slots[index].link = "OBJECT"
    if obj.material_slots[index].material != mat:
        obj.material_slots[index].material = mat


def get_mat_at_face_idx(obj, face_idx):
    """ get material at target face index of object """
    if len(obj.material_slots) == 0:
        return ""
    face = obj.data.polygons[face_idx]
    slot = obj.material_slots[face.material_index]
    mat = slot.material
    mat_name = mat.name if mat else ""
    return mat_name


def get_material_color(mat_name):
    """ get RGBA value of material """
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        return None
    if mat.use_nodes:
        node = get_first_bsdf_node(mat)
        if not node:
            return None
        r, g, b = node.inputs[0].default_value[:3]
        if node.type in ("BSDF_GLASS", "BSDF_TRANSPARENT", "BSDF_REFRACTION"):
            a = 0.25
        elif node.type in ("VOLUME_SCATTER", "VOLUME_ABSORPTION", "PRINCIPLED_VOLUME"):
            a = node.inputs["Density"].default_value
        else:
            a = node.inputs[0].default_value[3]
    else:
        if b280():
            r, g, b, a = mat.diffuse_color
        else:
            intensity = mat.diffuse_intensity
            r, g, b = Vector((mat.diffuse_color)) * intensity
            a = mat.alpha if mat.use_transparency else 1.0
    return [round(v, 5) for v in [r, g, b, a]]


def get_first_bsdf_node(mat, types:list=None):
    """ get first BSDF node, prioritizing specified types, in mat node tree """
    scn = bpy.context.scene
    if types is None:
        # get material type(s) based on render engine
        if scn.render.engine in ("CYCLES", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
            types = ("BSDF_PRINCIPLED", "BSDF_DIFFUSE")
        elif scn.render.engine == "octane":
            types = ("OCT_DIFFUSE_MAT")
        # elif scn.render.engine == "LUXCORE":
        #     types = ("CUSTOM")
        else:
            types = ()
    # get first node of target type
    mat_nodes = mat.node_tree.nodes
    for node in mat_nodes:
        if node.type in types:
            return node
    # get first node of any BSDF type
    for node in mat_nodes:
        if len(node.inputs) > 0 and node.inputs[0].type == "RGBA":
            return node
    # no valid node was found
    return None
