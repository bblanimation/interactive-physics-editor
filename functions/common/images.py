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
import numpy as np

# Blender imports
import bpy
from mathutils import Vector
from mathutils.interpolate import poly_3d_calc

# Module imports
from .reporting import b280
from .maths import *
from .colors import *


# reference: https://svn.blender.org/svnroot/bf-extensions/trunk/py/scripts/addons/uv_bake_texture_to_vcols.py
def get_pixel(pixels, pixel_width, uv_coord, channels=4):
    """ get RGBA value for specified coordinate in UV image
    pixels    -- list of pixel data from UV texture image
    size      -- image width
    uv_coord  -- UV coordinate of desired pixel value
    """
    pixel_number = (pixel_width * int(uv_coord.y) + int(uv_coord.x)) * channels
    assert 0 <= pixel_number < len(pixels)
    rgba = pixels[pixel_number:pixel_number + channels]
    return rgba


def get_1d_pixel_array(pixels, size, channels):
    pixels_1d = [pixels[i:i + channels] for i in range(0, len(pixels), channels)]
    return pixels_1d


def get_2d_pixel_array(pixels, size, channels):
    pixels_2d = np.zeros((size[0], size[1], channels)).tolist()
    for row in range(size[0]):
        for col in range(size[1]):
            pixel_number = (col * size[0] + row) * channels
            pixels_2d[row][col] = pixels[pixel_number:pixel_number + channels]

    return pixels_2d


def nearest_uv_coord(loc, img_obj):
    img_size = Vector(img_obj.data.size)
    img_off = Vector(img_obj.empty_image_offset)
    obj_dimensions = Vector((
        img_obj.empty_display_size,
        img_obj.empty_display_size * img_size.y / img_size.x,
    ))
    obj_dimensions = vec_mult(obj_dimensions, img_obj.scale)
    relative_loc = loc.xy - img_obj.location.xy
    pixel_offset = Vector((
        relative_loc.x * (img_size.x / obj_dimensions.x),
        relative_loc.y * (img_size.y / obj_dimensions.y),
    ))
    pixel_loc = Vector(pixel_offset[:2]) - vec_mult(img_size, img_off)
    return pixel_loc


def get_uv_coord(mesh, face, point, image):
    """ returns UV coordinate of target point in source mesh image texture
    mesh  -- mesh data from source object
    face  -- face object from mesh
    point -- coordinate of target point on source mesh
    image -- image texture for source mesh
    """
    # get active uv layer data
    uv_layer = mesh.uv_layers.active
    if uv_layer is None:
        return None
    uv = uv_layer.data
    # get 3D coordinates of face's vertices
    lco = [mesh.vertices[i].co for i in face.vertices]
    # get uv coordinates of face's vertices
    luv = [uv[i].uv for i in face.loop_indices]
    # calculate barycentric weights for point
    lwts = poly_3d_calc(lco, point)
    # multiply barycentric weights by uv coordinates
    uv_loc = sum((p*w for p,w in zip(luv,lwts)), Vector((0,0)))
    # ensure uv_loc is in range(0,1)
    # TODO: possibly approach this differently? currently, uv verts that are outside the image are wrapped to the other side
    uv_loc = Vector((uv_loc[0] % 1, uv_loc[1] % 1))
    # convert uv_loc in range(0,1) to uv coordinate
    image_size_x, image_size_y = image.size
    x_co = round(uv_loc.x * (image_size_x - 1))
    y_co = round(uv_loc.y * (image_size_y - 1))
    uv_coord = (x_co, y_co)

    # return resulting uv coordinate
    return Vector(uv_coord)


def get_uv_pixel_color(scn, obj, face_idx, point, pixels_getter, uv_image=None):
    """ get RGBA value for point in UV image at specified face index """
    if face_idx is None:
        return None
    # get closest material using UV map
    face = obj.data.polygons[face_idx]
    # get uv_layer image for face
    image = get_uv_image(scn, obj, face_idx, uv_image)
    if image is None:
        return None
    # get uv coordinate based on nearest face intersection
    uv_coord = get_uv_coord(obj.data, face, point, image)
    # retrieve rgba value at uv coordinate
    pixels = pixels_getter(image)
    rgba = get_pixel(pixels, image.size[0], uv_coord)
    # gamma correct color value
    if image.colorspace_settings.name == "sRGB":
        rgba = gamma_correct_srgb_to_linear(rgba)
    return rgba


def verify_img(im):
    """ verify image has pixel data """
    return im if im is not None and im.pixels is not None and len(im.pixels) > 0 else None


def get_first_img_from_nodes(obj, mat_slot_idx):
    """ return first image texture found in a material slot """
    mat = obj.material_slots[mat_slot_idx].material
    if mat is None or not mat.use_nodes:
        return None
    nodes_to_check = list(mat.node_tree.nodes)
    active_node = mat.node_tree.nodes.active
    if active_node is not None: nodes_to_check.insert(0, active_node)
    img = None
    for node in nodes_to_check:
        if node.type != "TEX_IMAGE":
            continue
        img = verify_img(node.image)
        if img is not None:
            break
    return img


def get_uv_image(scn, obj, face_idx, uv_image=None):
    """ returns UV image (priority to passed image, then face index, then first one found in material nodes) """
    image = verify_img(uv_image)
    # TODO: Reinstate this functionality for b280()
    if not b280() and image is None and obj.data.uv_textures.active:
        image = verify_img(obj.data.uv_textures.active.data[face_idx].image)
    if image is None:
        try:
            mat_idx = obj.data.polygons[face_idx].material_index
            image = verify_img(get_first_img_from_nodes(obj, mat_idx))
        except IndexError:
            mat_idx = 0
            while image is None and mat_idx < len(obj.material_slots):
                image = verify_img(get_first_img_from_nodes(obj, mat_idx))
                mat_idx += 1
    return image
