# Copyright (C) 2019 Christopher Gearhart
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
import os
from math import *

# Blender imports
import bpy
import bmesh
import mathutils
from mathutils import Vector, Euler, Matrix
from bpy_extras import view3d_utils
from bpy.types import Object, Scene, Event
try:
    from bpy.types import ViewLayer, LayerCollection
except ImportError:
    ViewLayer = None
    LayerCollection = None

# Module imports
from .python_utils import confirm_iter, confirm_list
from .wrappers import blender_version_wrapper
from .reporting import b280


#################### PREFERENCES ####################


@blender_version_wrapper("<=", "2.79")
def get_preferences(ctx=None):
    return (ctx if ctx else bpy.context).user_preferences
@blender_version_wrapper(">=", "2.80")
def get_preferences(ctx=None):
    return (ctx if ctx else bpy.context).preferences


def get_addon_preferences():
    """ get preferences for current addon """
    if not hasattr(get_addon_preferences, "prefs"):
        folderpath, foldername = os.path.split(get_addon_directory())
        addons = get_preferences().addons
        if not addons[foldername].preferences:
            return None
        get_addon_preferences.prefs = addons[foldername].preferences
    return get_addon_preferences.prefs


def get_addon_directory():
    """ get root directory of current addon """
    addons = get_preferences().addons
    folderpath = os.path.dirname(os.path.abspath(__file__))
    while folderpath:
        folderpath, foldername = os.path.split(folderpath)
        if foldername in {"common", "functions", "addons"}:
            continue
        if foldername in addons:
            break
    else:
        raise NameError("Did not find addon directory")
    return os.path.join(folderpath, foldername)


#################### OBJECTS ####################


def delete(objs, remove_meshes:bool=False):
    """ efficient deletion of objects """
    objs = confirm_iter(objs)
    for obj in objs:
        if obj is None:
            continue
        if remove_meshes:
            m = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if remove_meshes and m is not None:
            bpy.data.meshes.remove(m)


def duplicate(obj:Object, linked:bool=False, link_to_scene:bool=False):
    """ efficient duplication of objects """
    copy = obj.copy()
    if not linked and copy.data:
        copy.data = copy.data.copy()
    unhide(copy, render=False)
    if link_to_scene:
        link_object(copy)
    return copy


@blender_version_wrapper("<=","2.79")
def set_active_obj(obj:Object, scene:Scene=None):
    scene = scene or bpy.context.scene
    scene.objects.active = obj
@blender_version_wrapper(">=","2.80")
def set_active_obj(obj:Object, view_layer:ViewLayer=None):
    view_layer = view_layer or bpy.context.view_layer
    view_layer.objects.active = obj


@blender_version_wrapper("<=","2.79")
def select(obj_list, active:bool=False, only:bool=False):
    """ selects objs in list (deselects the rest if 'only') """
    # confirm obj_list is a list of objects
    obj_list = confirm_iter(obj_list)
    # deselect all if selection is exclusive
    if only:
        deselect_all()
    # select objects in list
    for obj in obj_list:
        if obj is not None and not obj.select:
            obj.select = True
    # set active object
    if active:
        set_active_obj(obj_list[0])
@blender_version_wrapper(">=","2.80")
def select(obj_list, active:bool=False, only:bool=False):
    """ selects objs in list (deselects the rest if 'only') """
    # confirm obj_list is a list of objects
    obj_list = confirm_iter(obj_list)
    # deselect all if selection is exclusive
    if only:
        deselect_all()
    # select objects in list
    for obj in obj_list:
        if obj is not None and not obj.select_get():
            obj.select_set(True)
    # set active object
    if active:
        set_active_obj(obj_list[0])


def select_all():
    """ selects all objs in scene """
    select(bpy.context.scene.objects)


def select_geom(geom):
    """ selects verts/edges/faces in 'geom' iterable """
    # confirm geom is an iterable of vertices
    geom = confirm_iter(geom)
    # select vertices in list
    for v in geom:
        if v and not v.select:
            v.select = True


def deselect_geom(geom):
    """ deselects verts/edges/faces in 'geom' iterable """
    # confirm geom is an iterable of vertices
    geom = confirm_iter(geom)
    # select vertices in list
    for v in geom:
        if v and v.select:
            v.select = False


@blender_version_wrapper("<=","2.79")
def deselect(obj_list):
    """ deselects objs in list """
    # confirm obj_list is a list of objects
    obj_list = confirm_list(obj_list)
    # select/deselect objects in list
    for obj in obj_list:
        if obj is not None and obj.select:
            obj.select = False
@blender_version_wrapper(">=","2.80")
def deselect(obj_list):
    """ deselects objs in list """
    # confirm obj_list is a list of objects
    obj_list = confirm_list(obj_list)
    # select/deselect objects in list
    for obj in obj_list:
        if obj is not None and obj.select_get():
            obj.select_set(False)


@blender_version_wrapper("<=","2.79")
def deselect_all():
    """ deselects all objs in scene """
    for obj in bpy.context.selected_objects:
        if obj.select:
            obj.select = False
@blender_version_wrapper(">=","2.80")
def deselect_all():
    """ deselects all objs in scene """
    selected_objects = bpy.context.selected_objects if hasattr(bpy.context, "selected_objects") else [obj for obj in bpy.context.view_layer.objects if obj.select_get()]
    deselect(selected_objects)


@blender_version_wrapper("<=","2.79")
def is_selected(obj):
    return obj.select
@blender_version_wrapper(">=","2.80")
def is_selected(obj):
    return obj.select_get()


@blender_version_wrapper("<=","2.79")
def hide(obj:Object, viewport:bool=True, render:bool=True):
    if not obj.hide and viewport:
        obj.hide = True
    if not obj.hide_render and render:
        obj.hide_render = True
@blender_version_wrapper(">=","2.80")
def hide(obj:Object, viewport:bool=True, render:bool=True):
    if not obj.hide_viewport and viewport:
        obj.hide_viewport = True
    if not obj.hide_render and render:
        obj.hide_render = True


@blender_version_wrapper("<=","2.79")
def unhide(obj:Object, viewport:bool=True, render:bool=True):
    if obj.hide and viewport:
        obj.hide = False
    if obj.hide_render and render:
        obj.hide_render = False
@blender_version_wrapper(">=","2.80")
def unhide(obj:Object, viewport:bool=True, render:bool=True):
    if obj.hide_viewport and viewport:
        obj.hide_viewport = False
    if obj.hide_render and render:
        obj.hide_render = False


@blender_version_wrapper("<=","2.79")
def is_obj_visible_in_viewport(obj:Object):
    scn = bpy.context.scene
    return any([obj.layers[i] and scn.layers[i] for i in range(20)])
@blender_version_wrapper(">=","2.80")
def is_obj_visible_in_viewport(obj:Object):
    return obj.visible_get()


@blender_version_wrapper("<=","2.79")
def link_object(o:Object, scene:Scene=None):
    scene = scene or bpy.context.scene
    scene.objects.link(o)
@blender_version_wrapper(">=","2.80")
def link_object(o:Object, scene:Scene=None):
    scene = scene or bpy.context.scene
    scene.collection.objects.link(o)


@blender_version_wrapper("<=","2.79")
def unlink_object(o:Object, scene:Scene=None, all:bool=False):
    bpy.context.scene.objects.unlink(o)
@blender_version_wrapper(">=","2.80")
def unlink_object(o:Object, scene:Scene=None, all:bool=False):
    if not all:
        scene = scene or bpy.context.scene
        scene.collection.objects.unlink(o)
    else:
        for coll in o.users_collection:
            coll.objects.unlink(o)


@blender_version_wrapper("<=","2.79")
def safe_link(obj:Object, protect:bool=False, collections=None):
    # link object to scene
    try:
        link_object(obj)
    except RuntimeError:
        pass
    # remove fake user from object data
    obj.use_fake_user = False
    # protect object from deletion (useful in Bricker addon)
    if hasattr(obj, "protected"):
        obj.protected = protect
@blender_version_wrapper(">=","2.80")
def safe_link(obj:Object, protect:bool=False, collections=[]):
    # link object to target collections (scene collection by default)
    collections = collections or [bpy.context.scene.collection]
    for coll in collections:
        try:
            coll.objects.link(obj)
        except RuntimeError:
            continue
    # remove fake user from object data
    obj.use_fake_user = False
    # protect object from deletion (useful in Bricker addon)
    if hasattr(obj, "protected"):
        obj.protected = protect


def safe_unlink(obj:Object, protect:bool=True):
    # unlink object from scene
    try:
        unlink_object(obj, all=True)
    except RuntimeError:
        pass
    # prevent object data from being tossed on Blender exit
    obj.use_fake_user = True
    # protect object from deletion (useful in Bricker addon)
    if hasattr(obj, "protected"):
        obj.protected = protect


def copy_animation_data(source:Object, target:Object):
    """ copy animation data from one object to another """
    if source.animation_data is None:
        return

    ad = source.animation_data

    properties = [p.identifier for p in ad.bl_rna.properties if not p.is_readonly]

    if target.animation_data is None:
        target.animation_data_create()
    ad2 = target.animation_data

    for prop in properties:
        setattr(ad2, prop, getattr(ad, prop))


def insert_keyframes(objs, keyframe_type:str, frame:int, if_needed:bool=False):
    """ insert key frames for given objects to given frames """
    objs = confirm_iter(objs)
    options = set(["INSERTKEY_NEEDED"] if if_needed else [])
    for obj in objs:
        inserted = obj.keyframe_insert(data_path=keyframe_type, frame=frame, options=options)


@blender_version_wrapper("<=", "2.79")
def new_mesh_from_object(obj:Object):
    return bpy.data.meshes.new_from_object(bpy.context.scene, obj, apply_modifiers=True, settings="PREVIEW")
@blender_version_wrapper(">=", "2.80")
def new_mesh_from_object(obj:Object):
    depsgraph = bpy.context.view_layer.depsgraph
    obj_eval = obj.evaluated_get(depsgraph)
    return bpy.data.meshes.new_from_object(obj_eval)


def apply_modifiers(obj:Object):
    """ apply modifiers to object (may require a depsgraph update before running) """
    m = new_mesh_from_object(obj)
    obj.modifiers.clear()
    obj.data = m


@blender_version_wrapper("<=","2.79")
def light_add(type:str="POINT", radius:float=1.0, align:str="WORLD", location:tuple=(0.0, 0.0, 0.0), rotation:tuple=(0.0, 0.0, 0.0)):
    view_align = align != "WORLD"
    bpy.ops.object.lamp_add(type=type, radius=radius, view_align=view_align, location=location, rotation=rotation)
@blender_version_wrapper(">=","2.80")
def light_add(type:str="POINT", radius:float=1.0, align:str="WORLD", location:tuple=(0.0, 0.0, 0.0), rotation:tuple=(0.0, 0.0, 0.0)):
    bpy.ops.object.light_add(type=type, radius=radius, align=align, location=location, rotation=rotation)


def is_smoke(ob:Object):
    """ check if object is smoke domain """
    if ob is None:
        return False
    for mod in ob.modifiers:
        if mod.type == "SMOKE" and mod.domain_settings and mod.show_viewport:
            return True
    return False


def is_adaptive(ob:Object):
    """ check if smoke domain object uses adaptive domain """
    if ob is None:
        return False
    for mod in ob.modifiers:
        if mod.type == "SMOKE" and mod.domain_settings and mod.domain_settings.use_adaptive_domain:
            return True
    return False

def get_vertices_in_group(obj:Object, vertex_group):
    if isinstance(vertex_group, int):
        if vertex_group >= len(obj.vertex_groups):
            raise IndexError("Index out of range!")
    elif isinstance(vertex_group, str):
        if vertex_group not in obj.vertex_groups:
            raise NameError("'{obj}' has no vertex group, '{vg}'!".format(obj=obj.name, vg=vertex_group))
        vertex_group = obj.vertex_groups[vertex_group].index
    else:
        raise ValueError("Expecting second argument to be of type 'str', or 'int'. Got {}".format(type(vertex_group)))

    return [v for v in obj.data.vertices if vertex_group in [vg.group for vg in v.groups]]


#################### VIEWPORT ####################


def tag_redraw_areas(area_types:iter=["ALL"]):
    """ run tag_redraw for given area types """
    area_types = confirm_list(area_types)
    screens = [bpy.context.screen] if bpy.context.screen else bpy.data.screens
    for screen in screens:
        for area in screen.areas:
            for area_type in area_types:
                if area_type == "ALL" or area.type == area_type:
                    area.tag_redraw()


@blender_version_wrapper("<=", "2.79")
def disable_relationship_lines():
    """ disable relationship lines in VIEW_3D """
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            area.spaces[0].show_relationship_lines = False
@blender_version_wrapper(">=", "2.80")
def disable_relationship_lines():
    """ disable relationship lines in VIEW_3D """
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            area.spaces[0].overlay.show_relationship_lines = False


@blender_version_wrapper(">=", "2.80")
def get_layer_collection(name:str, layer_collection:LayerCollection=None):
    """ recursivly transverse view_layer.layer_collection for a particular name """
    layer_collection = layer_collection or bpy.context.window.view_layer.layer_collection
    if (layer_collection.name == name):
        return layer_collection
    for lc in layer_collection.children:
        found_layer_coll = get_layer_collection(name, lc)
        if found_layer_coll:
            return found_layer_coll


def set_active_scene(scn:Scene):
    """ set active scene in all screens """
    for screen in bpy.data.screens:
        screen.scene = scn


def change_context(context, areaType:str):
    """ Changes current context and returns previous area type """
    last_area_type = context.area.type
    context.area.type = areaType
    return last_area_type


def assemble_override_context(area_type="VIEW_3D"):
    """
    Iterates through the blender GUI's areas & regions to find the View3D space
    NOTE: context override can only be used with bpy.ops that were called from a window/screen with a view3d space
    """
    win      = bpy.context.window
    scr      = win.screen
    areas3d  = [area for area in scr.areas if area.type == area_type]
    region   = [region for region in areas3d[0].regions if region.type == "WINDOW"]
    override = {
        "window": win,
        "screen": scr,
        "area"  : areas3d[0],
        "region": region[0],
        "scene" : bpy.context.scene,
    }
    return override


@blender_version_wrapper("<=","2.79")
def set_layers(layers:iter, scn:Scene=None):
    """ set active layers of scn w/o 'dag ZERO' error """
    assert len(layers) == 20
    scn = scn or bpy.context.scene
    # update scene (prevents dag ZERO errors)
    scn.update()
    # set active layers of scn
    scn.layers = layers


@blender_version_wrapper("<=","2.79")
def open_layer(layer_num:int, scn:Scene=None):
    scn = scn or bpy.context.scene
    layer_list = [i == layer_num - 1 for i in range(20)]
    scn.layers = layer_list
    return layer_list


def viewport_is_orthographic(r3d, cam=None):
    return r3d.view_perspective == "ORTHO" or (r3d.view_perspective == "CAMERA" and cam and cam.type == "ORTHO")


#################### MESHES ####################


def draw_bmesh(bm:bmesh, name:str="drawn_bmesh"):
    """ create mesh and object from bmesh """
    # note: neither are linked to the scene, yet, so they won't show in the 3d view
    m = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, m)

    link_object(obj)          # link new object to scene
    select(obj, active=True)  # select new object and make active (does not deselect other objects)
    bm.to_mesh(m)             # push bmesh data into m
    return obj


def smooth_mesh_faces(faces:iter):
    """ set given Mesh faces to smooth """
    faces = confirm_iter(faces)
    for f in faces:
        f.use_smooth = True


def junk_mesh():
    """ returns junk mesh (only creates one if necessary) """
    junk_mesh = bpy.data.meshes.get("Bricker_junk_mesh")
    if junk_mesh is None:
        junk_mesh = bpy.data.meshes.new("Bricker_junk_mesh")
    return junk_mesh


#################### RAY CASTING ####################


def get_ray_target(x, y, ray_max=1000):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    cam = bpy.context.camera
    coord = x, y
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    if rv3d.view_perspective == "ORTHO" or (rv3d.view_perspective == "CAMERA" and cam and cam.type == "ORTHO"):
        # move ortho origin back
        ray_origin = ray_origin - (view_vector * (ray_max / 2.0))
    ray_target = ray_origin + (view_vector * 1000)


def get_position_on_grid(mouse_pos, ray_max=1000):
    viewport_region = bpy.context.region
    viewport_r3d = bpy.context.region_data
    viewport_matrix = viewport_r3d.view_matrix.inverted()
    cam_obj = bpy.context.space_data.camera

    # Shooting a ray from the camera, through the mouse cursor towards the grid with a length of 100000
    # If the camera is more than 100000 units away from the grid it won't detect a point
    ray_start = viewport_matrix.to_translation()
    ray_depth = viewport_matrix @ Vector((0, 0, -100000))

    # Get the 3D vector position of the mouse
    ray_end = view3d_utils.region_2d_to_location_3d(viewport_region, viewport_r3d, (mouse_pos[0], mouse_pos[1]), ray_depth)

    # A triangle on the grid plane. We use these 3 points to define a plane on the grid
    point_1 = Vector((0, 0, 0))
    point_2 = Vector((0, 1, 0))
    point_3 = Vector((1, 0, 0))

    # Create a 3D position on the grid under the mouse cursor using the triangle as a grid plane
    # and the ray cast from the camera
    position_on_grid = mathutils.geometry.intersect_ray_tri(point_1, point_2, point_3, ray_end, ray_start, False)
    if position_on_grid is None:
        return None

    if viewport_is_orthographic(viewport_r3d, None if cam_obj is None else cam_obj.data):
        # multiply by ray max
        position_on_grid = position_on_grid * ray_max

    return position_on_grid


#################### OTHER ####################


@blender_version_wrapper("<=","2.79")
def active_render_engine():
    return bpy.context.scene.render.engine
@blender_version_wrapper(">=","2.80")
def active_render_engine():
    return bpy.context.engine


@blender_version_wrapper("<=","2.79")
def depsgraph_update():
    bpy.context.scene.update()
@blender_version_wrapper(">=","2.80")
def depsgraph_update():
    bpy.context.view_layer.depsgraph.update()


@blender_version_wrapper("<=","2.79")
def right_align(layout_item):
    pass
@blender_version_wrapper(">=","2.80")
def right_align(layout_item):
    layout_item.use_property_split = True
    layout_item.use_property_decorate = False


def get_item_by_id(collection, id:int):
    """ get UIlist item from collection with given id """
    success = False
    for item in collection:
        if item.id == id:
            success = True
            break
    return item if success else None


@blender_version_wrapper("<=","2.79")
def layout_split(layout, align=True, factor=0.5):
    return layout.split(align=align, percentage=factor)
@blender_version_wrapper(">=","2.80")
def layout_split(layout, align=True, factor=0.5):
    return layout.split(align=align, factor=factor)


@blender_version_wrapper("<=","2.79")
def bpy_collections():
    return bpy.data.groups
@blender_version_wrapper(">=","2.80")
def bpy_collections():
    return bpy.data.collections


@blender_version_wrapper("<=","2.79")
def set_active_scene(scene:Scene):
    bpy.context.screen.scene = scene
@blender_version_wrapper(">=","2.80")
def set_active_scene(scene:Scene):
    bpy.context.window.scene = scene


def set_cursor(cursor):
    # DEFAULT, NONE, WAIT, CROSSHAIR, MOVE_X, MOVE_Y, KNIFE, TEXT,
    # PAINT_BRUSH, HAND, SCROLL_X, SCROLL_Y, SCROLL_XY, EYEDROPPER
    for wm in bpy.data.window_managers:
        for win in wm.windows:
            win.cursor_modal_set(cursor)


@blender_version_wrapper("<=","2.79")
def get_cursor_location():
    return bpy.context.scene.cursor_location
@blender_version_wrapper(">=","2.80")
def get_cursor_location():
    return bpy.context.scene.cursor.location


@blender_version_wrapper("<=","2.79")
def set_cursor_location(loc:tuple):
    bpy.context.scene.cursor_location = loc
@blender_version_wrapper(">=","2.80")
def set_cursor_location(loc:tuple):
    bpy.context.scene.cursor.location = loc


def mouse_in_view3d_window(event):
    regions = dict()
    for region in bpy.context.area.regions:
        regions[region.type] = region
    mouse_pos = Vector((event.mouse_x, event.mouse_y))
    window_dimensions = Vector((regions["WINDOW"].width - regions["UI"].width, regions["WINDOW"].height - regions["HEADER"].height))
    return regions["TOOLS"].width < mouse_pos.x < window_dimensions.x and mouse_pos.y < window_dimensions.y


@blender_version_wrapper("<=","2.79")
def make_annotations(cls):
    """Does nothing in Blender 2.79"""
    return cls
@blender_version_wrapper(">=","2.80")
def make_annotations(cls):
    """Converts class fields to annotations in Blender 2.8"""
    bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if bl_props:
        if "__annotations__" not in cls.__dict__:
            setattr(cls, "__annotations__", {})
        annotations = cls.__dict__["__annotations__"]
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


@blender_version_wrapper("<=","2.79")
def get_annotations(cls):
    return list(dict(cls).keys())
@blender_version_wrapper(">=","2.80")
def get_annotations(cls):
    return cls.__annotations__


@blender_version_wrapper(">=","2.80")
def get_tool_list(space_type, context_mode):
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    cls = ToolSelectPanelHelper._tool_class_from_space_type(space_type)
    return cls._tools[context_mode]


def get_keymap_item(operator:str, keymap:str=None):
    keymaps = bpy.context.window_manager.keyconfigs.user.keymaps
    keymap = keymaps[keymap] if keymap else next(km for km in keymaps if operator in km.keymap_items.keys())
    return keymap.keymap_items[operator]


def called_from_shortcut(event:Event, operator:str, keymap:str=None):
    kmi = get_keymap_item(operator, keymap)
    return (
        kmi.type == event.type and \
        kmi.alt == event.alt and \
        kmi.ctrl == event.ctrl and \
        kmi.oskey == event.oskey and \
        kmi.shift == event.shift and \
        kmi.value == event.value
    )


def new_window(area_type, width=640, height=480):
    # Modify scene settings
    render = bpy.context.scene.render
    orig_settings = {
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage,
        "display_mode": render.display_mode,
    }

    render.resolution_x = width
    render.resolution_y = height
    render.resolution_percentage = 100
    render.display_mode = "WINDOW"  # Call user prefs window

    bpy.ops.render.view_show("INVOKE_DEFAULT")

    # Change area type
    window = bpy.context.window_manager.windows[-1]
    area = window.screen.areas[0]
    area.type = area_type

    # reset scene settings
    for key in orig_settings:
        setattr(render, key, orig_settings[key])

    return window


def is_navigation_event(event:Event):
    navigation_events = {
        'Rotate View': 'view3d.rotate',
        'Move View': 'view3d.move',
        'Zoom View': 'view3d.zoom',
        'Dolly View': 'view3d.dolly',
        'View Pan': 'view3d.view_pan',
        'View Orbit': 'view3d.view_orbit',
        'View Persp/Ortho': 'view3d.view_persportho',
        'View Numpad': 'view3d.viewnumpad',
        'NDOF Pan Zoom': 'view2d.ndof',
        'NDOF Orbit View with Zoom': 'view3d.ndof_orbit_zoom',
        'NDOF Orbit View': 'view3d.ndof_orbit',
        'NDOF Pan View': 'view3d.ndof_pan',
        'NDOF Move View': 'view3d.ndof_all',
        'View Selected': 'view3d.view_selected',
        'Center View to Cursor': 'view3d.view_center_cursor',
        #'View Navigation': 'view3d.navigate',
    }
    keyconfig_name = "blender" if b280() else "Blender"
    # keyconfig_name = "blender user" if b280() else "Blender"
    if keyconfig_name not in bpy.context.window_manager.keyconfigs:
        print('No keyconfig named "%s"' % keyconfig_name)
        return
    keyconfig = bpy.context.window_manager.keyconfigs[keyconfig_name]
    def translate(text):
        return bpy.app.translations.pgettext(text)
    def get_keymap_items(key):
        nonlocal keyconfig
        if key in keyconfig.keymaps:
            keymap = keyconfig.keymaps[key]
        else:
            keymap = keyconfig.keymaps[translate(key)]
        return keymap.keymap_items
    #navigation_events = { translate(key): val for key,val in navigation_events.items() }
    navigation_idnames = navigation_events.values()
    for kmi in get_keymap_items('3D View'):
        if kmi.name not in navigation_events and kmi.idname not in navigation_idnames:
            continue
        event_type = event.type
        if event_type == "WHEELUPMOUSE":
            event_type = "WHEELINMOUSE"
        if event_type == "WHEELDOWNMOUSE":
            event_type = "WHEELOUTMOUSE"
        if event_type == kmi.type and kmi.value in (event.value, "ANY") and kmi.shift == event.shift and kmi.alt == event.alt and kmi.ctrl == event.ctrl and kmi.oskey == event.oskey:
            return True
    return False


def load_from_library(blendfile_path, data_attr, filenames=None, overwrite_data=False, action="APPEND"):
    data_block_infos = list()
    orig_data_names = lambda: None
    with bpy.data.libraries.load(blendfile_path, link=action == "LINK") as (data_from, data_to):
        # if only appending some of the filenames
        if filenames is not None:
            # rebuild 'data_attr' of data_from based on filenames in 'filenames' list
            filenames = confirm_list(filenames)
            data_group = getattr(data_from, data_attr)
            new_data_group = [data_name for data_name in data_group if data_name in filenames]
            setattr(data_from, data_attr, new_data_group)
        # append data from library ('data_from') to 'data_to'
        setattr(data_to, data_attr, getattr(data_from, data_attr))
        # store copies of loaded attributes to 'orig_data_names' object
        if overwrite_data:
            attrib = getattr(data_from, data_attr)
            if len(attrib) > 0:
                setattr(orig_data_names, data_attr, attrib.copy())
    # overwrite existing data with loaded data of the same name
    if overwrite_data:
        # get attributes to remap
        source_attr = getattr(orig_data_names, data_attr)
        target_attr = getattr(data_to, data_attr)
        for i, data_name in enumerate(source_attr):
            # check that the data doesn't match
            if not hasattr(target_attr[i], "name") or target_attr[i].name == data_name or not hasattr(bpy.data, data_attr): continue
            # remap existing data to loaded data
            data_group = getattr(bpy.data, data_attr)
            data_group.get(data_name).user_remap(target_attr[i])
            # remove remapped existing data
            data_group.remove(data_group.get(data_name))
            # rename loaded data to original name
            target_attr[i].name = data_name
    return getattr(data_to, data_attr)
