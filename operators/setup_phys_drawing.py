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
import bmesh
import math

# Blender imports
import bpy
import bgl
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d, region_2d_to_origin_3d, region_2d_to_vector_3d
from bpy.types import SpaceView3D
from bpy.props import *

from ..functions import *

class interactive_sim_drawing():
    ##############################################
    # Draw handler function
    # from CG Cookie's retopoflow plugin

    def ui_start(self):
        # # report something useful to user
        # bpy.context.area.header_text_set("PLACEHOLDER")
        # update dpi
        prefs = get_preferences(bpy.context)
        ui_scale = prefs.view.ui_scale
        pixel_size = prefs.system.pixel_size
        self.dpi = int(72 * ui_scale * pixel_size)


        # add callback handlers
        self.cb_pr_handle = SpaceView3D.draw_handler_add(self.draw_callback_preview,   (bpy.context, ), 'WINDOW', 'PRE_VIEW')
        # self.cb_pv_handle = SpaceView3D.draw_handler_add(self.draw_callback_postview,  (bpy.context, ), 'WINDOW', 'POST_VIEW')
        # self.cb_pp_handle = SpaceView3D.draw_handler_add(self.draw_callback_postpixel, (bpy.context, ), 'WINDOW', 'POST_PIXEL')
        # darken other spaces
        self.spaces = [
            bpy.types.SpaceClipEditor,
            bpy.types.SpaceConsole,
            bpy.types.SpaceDopeSheetEditor,
            bpy.types.SpaceFileBrowser,
            bpy.types.SpaceGraphEditor,
            bpy.types.SpaceImageEditor,
            bpy.types.SpaceInfo,
            bpy.types.SpaceLogicEditor,
            bpy.types.SpaceNLA,
            bpy.types.SpaceNodeEditor,
            bpy.types.SpaceOutliner,
            bpy.types.SpaceProperties,
            bpy.types.SpaceSequenceEditor,
            bpy.types.SpaceTextEditor,
            bpy.types.SpaceTimeline,
            #bpy.types.SpaceUVEditor,       # <- does not exist?
            bpy.types.SpaceUserPreferences,
            #'SpaceView3D',                 # <- specially handled
            ]
        self.areas = [ 'WINDOW', 'HEADER' ]
        # ('WINDOW', 'HEADER', 'CHANNELS', 'TEMPORARY', 'UI', 'TOOLS', 'TOOL_PROPS', 'PREVIEW')
        # self.cb_pp_tools   = SpaceView3D.draw_handler_add(self.draw_callback_cover, (bpy.context, ), 'TOOLS',      'POST_PIXEL')
        self.cb_pp_props   = SpaceView3D.draw_handler_add(self.draw_callback_cover, (bpy.context, ), 'TOOL_PROPS', 'POST_PIXEL')
        self.cb_pp_ui      = SpaceView3D.draw_handler_add(self.draw_callback_cover, (bpy.context, ), 'UI',         'POST_PIXEL')
        self.cb_pp_header  = SpaceView3D.draw_handler_add(self.draw_callback_cover, (bpy.context, ), 'HEADER',     'POST_PIXEL')
        self.cb_pp_all = [
            (s, a, s.draw_handler_add(self.draw_callback_cover, (bpy.context,), a, 'POST_PIXEL'))
            for s in self.spaces
            for a in self.areas
            ]
        self.draw_preview()
        tag_redraw_areas()

    def ui_end(self):
        # remove callback handlers
        if hasattr(self, 'cb_pr_handle'):
            SpaceView3D.draw_handler_remove(self.cb_pr_handle, "WINDOW")
            del self.cb_pr_handle
        if hasattr(self, 'cb_pv_handle'):
            SpaceView3D.draw_handler_remove(self.cb_pv_handle, "WINDOW")
            del self.cb_pv_handle
        if hasattr(self, 'cb_pp_handle'):
            SpaceView3D.draw_handler_remove(self.cb_pp_handle, "WINDOW")
            del self.cb_pp_handle
        if hasattr(self, 'cb_pp_tools'):
            SpaceView3D.draw_handler_remove(self.cb_pp_tools,  "TOOLS")
            del self.cb_pp_tools
        if hasattr(self, 'cb_pp_props'):
            SpaceView3D.draw_handler_remove(self.cb_pp_props,  "TOOL_PROPS")
            del self.cb_pp_props
        if hasattr(self, 'cb_pp_ui'):
            SpaceView3D.draw_handler_remove(self.cb_pp_ui,     "UI")
            del self.cb_pp_ui
        if hasattr(self, 'cb_pp_header'):
            SpaceView3D.draw_handler_remove(self.cb_pp_header, "HEADER")
            del self.cb_pp_header
        if hasattr(self, 'cb_pp_all'):
            for s,a,cb in self.cb_pp_all: s.draw_handler_remove(cb, a)
            del self.cb_pp_all
        tag_redraw_areas()

    def draw_callback_preview(self, context):
        bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)    # save OpenGL attributes
        try:    self.draw_preview()
        except: interactive_physics_handle_exception()
        bgl.glPopAttrib()                           # restore OpenGL attributes

    # def draw_callback_postview(self, context):
    #     # self.drawing.update_dpi()
    #     # self.drawing.set_font_size(12, force=True)
    #     # self.drawing.point_size(1)
    #     # self.drawing.line_width(1)
    #     bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)    # save OpenGL attributes
    #     try:    self.draw_postview()
    #     except: handle_exception()
    #     bgl.glPopAttrib()                           # restore OpenGL attributes

    def draw_callback_postpixel(self, context):
        bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)    # save OpenGL attributes
        try:    self.draw_postpixel()
        except: handle_exception()
        bgl.glPopAttrib()                           # restore OpenGL attributes

    def draw_callback_cover(self, context):
        bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glPushMatrix()
        bgl.glLoadIdentity()
        bgl.glColor4f(0,0,0,0.5)    # TODO: use window background color??
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glBegin(bgl.GL_QUADS)   # TODO: not use immediate mode
        bgl.glVertex2f(-1, -1)
        bgl.glVertex2f( 1, -1)
        bgl.glVertex2f( 1,  1)
        bgl.glVertex2f(-1,  1)
        bgl.glEnd()
        bgl.glPopMatrix()
        bgl.glPopAttrib()

    def draw_preview(self):
        bgl.glEnable(bgl.GL_MULTISAMPLE)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_POINT_SMOOTH)
        bgl.glDisable(bgl.GL_DEPTH_TEST)

        bgl.glMatrixMode(bgl.GL_MODELVIEW)
        bgl.glPushMatrix()
        bgl.glLoadIdentity()
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glPushMatrix()
        bgl.glLoadIdentity()

        # add background gradient
        bgl.glBegin(bgl.GL_TRIANGLES)
        for i in range(0,360,10):
            r0,r1 = i*math.pi/180.0, (i+10)*math.pi/180.0
            x0,y0 = math.cos(r0)*2,math.sin(r0)*2
            x1,y1 = math.cos(r1)*2,math.sin(r1)*2
            bgl.glColor4f(0,0,0.01,0.0)
            bgl.glVertex2f(0,0)
            bgl.glColor4f(0,0,0.01,0.8)
            bgl.glVertex2f(x0,y0)
            bgl.glVertex2f(x1,y1)
        bgl.glEnd()

        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glPopMatrix()
        bgl.glMatrixMode(bgl.GL_MODELVIEW)
        bgl.glPopMatrix()

    def draw_postpixel(self):
        pass

    def draw_text_2d(self, text, font_id=0, color=(1, 1, 1, 1), position=(0, 0)):
        # draw some text
        bgl.glColor4f(*color)
        blf.position(font_id, position[0], position[1], 0)
        blf.size(font_id, 11, self.dpi)
        blf.draw(font_id, text)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

    # def draw_centerpoint(color, point, width=1):
    #     bgl.glLineWidth(width)
    #     bgl.glColor4f(*color)
    #     bgl.glBegin(bgl.GL_POINTS)
    #     bgl.glVertex3f(*point)
    #
    # def Point_to_depth(self, xyz):
    #     xy = location_3d_to_region_2d(self.region, self.r3d, xyz)
    #     if xy is None: return None
    #     oxyz = region_2d_to_origin_3d(self.region, self.r3d, xy)
    #     return (xyz - oxyz).length
    #
    # # def Point2D_to_Vec(self, xy:Point2D):
    # #     if xy is None: return None
    # #     return Vector(region_2d_to_vector_3d(self.actions.region, self.actions.r3d, xy))
    # #
    # # def Point2D_to_Origin(self, xy:Point2D):
    # #     if xy is None: return None
    # #     return Point(region_2d_to_origin_3d(self.actions.region, self.actions.r3d, xy))
    # #
    # # def Point2D_to_Ray(self, xy:Point2D):
    # #     if xy is None: return None
    # #     return Ray(self.Point2D_to_Origin(xy), self.Point2D_to_Vec(xy))
    # #
    # # def Point2D_to_Point(self, xy:Point2D, depth:float):
    # #     r = self.Point2D_to_Ray(xy)
    # #     if r is None or r.o is None or r.d is None or depth is None:
    # #         return None
    # #     return Point(r.o + depth * r.d)
    # #
    # # def size2D_to_size(self, size2D:float, xy:Point2D, depth:float):
    # #     # computes size of 3D object at distance (depth) as it projects to 2D size
    # #     # TODO: there are more efficient methods of computing this!
    # #     p3d0 = self.Point2D_to_Point(xy, depth)
    # #     p3d1 = self.Point2D_to_Point(xy + Vector((size2D,0)), depth)
    # #     return (p3d0 - p3d1).length
    #
    # def update_ui_mouse_pos(self):
    #     if self.loc is None or self.normal is None:
    #         self.clear_ui_mouse_pos()
    #         return
    #     depth = self.Point_to_depth(self.loc)
    #     if depth is None:
    #         self.clear_ui_mouse_pos()
    #         return
    #     rmat = Matrix.Rotation(self.oz.angle(self.normal), 4, self.oz.cross(self.normal))
    #     self.hit = True
    #     self.scale = 1  # self.rfcontext.size2D_to_size(1.0, self.mouse, depth)
    #     self.hit_p = self.loc
    #     self.hit_x = Vector(rmat * self.ox)
    #     self.hit_y = Vector(rmat * self.oy)
    #     self.hit_z = Vector(rmat * self.oz)
    #     self.hit_rmat = rmat
    #
    # def clear_ui_mouse_pos(self):
    #     ''' called when mouse is moved outside View3D '''
    #     self.hit = False
    #     self.hit_p = None
    #     self.hit_x = None
    #     self.hit_y = None
    #     self.hit_z = None
    #     self.hit_rmat = None
    #
    # @staticmethod
    # @blender_version('<','2.79')
    # def update_dpi():
    #     paintbrush._dpi = get_preferences(bpy.context).system.dpi
    #     if get_preferences(bpy.context).system.virtual_pixel_mode == 'DOUBLE':
    #         paintbrush._dpi *= 2
    #     paintbrush._dpi *= get_preferences(bpy.context).system.pixel_size
    #     paintbrush._dpi = int(paintbrush._dpi)
    #     paintbrush._dpi_mult = paintbrush._dpi / 72
    #
    # @staticmethod
    # @blender_version('>=','2.79')
    # def update_dpi():
    #     paintbrush._ui_scale = get_preferences(bpy.context).view.ui_scale
    #     paintbrush._sysdpi = get_preferences(bpy.context).system.dpi
    #     paintbrush._pixel_size = get_preferences(bpy.context).system.pixel_size
    #     paintbrush._dpi = 72 # get_preferences(bpy.context).system.dpi
    #     paintbrush._dpi *= paintbrush._ui_scale
    #     paintbrush._dpi *= paintbrush._pixel_size
    #     paintbrush._dpi = int(paintbrush._dpi)
    #     paintbrush._dpi_mult = paintbrush._ui_scale * paintbrush._pixel_size * paintbrush._sysdpi / 72
    #     s = 'DPI information: scale:%0.2f, pixel:%0.2f, dpi:%d' % (paintbrush._ui_scale, paintbrush._pixel_size, paintbrush._sysdpi)
    #     if s != getattr(paintbrush, '_last_dpi_info', None):
    #         paintbrush._last_dpi_info = s
    #         print(s)
    #
    # def draw_postview(self):
    #     print("HERE")
    #     if not self.hit: return
    #     print("HERE2")
    #
    #     cx,cy,cp = self.hit_x,self.hit_y,self.hit_p
    #     cs_outer = self.scale * self.radius
    #     cs_inner = self.scale * self.radius * math.pow(0.5, 1.0 / self.falloff)
    #     cr,cg,cb = self.color
    #
    #     bgl.glDepthRange(0, 0.999)      # squeeze depth just a bit
    #     bgl.glEnable(bgl.GL_BLEND)
    #     # self.drawing.line_width(2.0)
    #     # self.drawing.point_size(3.0)
    #     bgl.glPointSize(max(1, 3.0 * self._dpi_mult))
    #
    #     ######################################
    #     # draw in front of geometry
    #
    #     bgl.glDepthFunc(bgl.GL_LEQUAL)
    #     bgl.glDepthMask(bgl.GL_FALSE)   # do not overwrite depth
    #
    #     bgl.glColor4f(cr, cg, cb, 0.75 * self.strength)
    #     bgl.glBegin(bgl.GL_TRIANGLES)
    #     for p0,p1 in zip(self.points[:-1], self.points[1:]):
    #         x0,y0 = p0
    #         x1,y1 = p1
    #         outer0 = (cs_outer * ((cx * x0) + (cy * y0))) + cp
    #         outer1 = (cs_outer * ((cx * x1) + (cy * y1))) + cp
    #         inner0 = (cs_inner * ((cx * x0) + (cy * y0))) + cp
    #         inner1 = (cs_inner * ((cx * x1) + (cy * y1))) + cp
    #         bgl.glVertex3f(*outer0)
    #         bgl.glVertex3f(*outer1)
    #         bgl.glVertex3f(*inner0)
    #         bgl.glVertex3f(*outer1)
    #         bgl.glVertex3f(*inner1)
    #         bgl.glVertex3f(*inner0)
    #     bgl.glEnd()
    #
    #     bgl.glColor4f(1, 1, 1, 1)       # outer ring
    #     bgl.glBegin(bgl.GL_LINE_STRIP)
    #     for x,y in self.points:
    #         p = (cs_outer * ((cx * x) + (cy * y))) + cp
    #         bgl.glVertex3f(*p)
    #     bgl.glEnd()
    #
    #     # bgl.glColor4f(1, 1, 1, 0.5)     # inner ring
    #     # bgl.glBegin(bgl.GL_LINE_STRIP)
    #     # for x,y in self.points:
    #     #     p = (cs_inner * ((cx * x) + (cy * y))) + cp
    #     #     bgl.glVertex3f(*p)
    #     # bgl.glEnd()
    #
    #     bgl.glColor4f(1, 1, 1, 0.25)    # center point
    #     bgl.glBegin(bgl.GL_POINTS)
    #     bgl.glVertex3f(*cp)
    #     bgl.glEnd()
    #
    #     # ######################################
    #     # # draw behind geometry (hidden below)
    #     #
    #     # bgl.glDepthFunc(bgl.GL_GREATER)
    #     # bgl.glDepthMask(bgl.GL_FALSE)   # do not overwrite depth
    #     #
    #     # bgl.glColor4f(cr, cg, cb, 0.10 * self.strength)
    #     # bgl.glBegin(bgl.GL_TRIANGLES)
    #     # for p0,p1 in zip(self.points[:-1], self.points[1:]):
    #     #     x0,y0 = p0
    #     #     x1,y1 = p1
    #     #     outer0 = (cs_outer * ((cx * x0) + (cy * y0))) + cp
    #     #     outer1 = (cs_outer * ((cx * x1) + (cy * y1))) + cp
    #     #     inner0 = (cs_inner * ((cx * x0) + (cy * y0))) + cp
    #     #     inner1 = (cs_inner * ((cx * x1) + (cy * y1))) + cp
    #     #     bgl.glVertex3f(*outer0)
    #     #     bgl.glVertex3f(*outer1)
    #     #     bgl.glVertex3f(*inner0)
    #     #     bgl.glVertex3f(*outer1)
    #     #     bgl.glVertex3f(*inner1)
    #     #     bgl.glVertex3f(*inner0)
    #     # bgl.glEnd()
    #     #
    #     # bgl.glColor4f(1, 1, 1, 0.05)    # outer ring
    #     # bgl.glBegin(bgl.GL_LINE_STRIP)
    #     # for x,y in self.points:
    #     #     p = (cs_outer * ((cx * x) + (cy * y))) + cp
    #     #     bgl.glVertex3f(*p)
    #     # bgl.glEnd()
    #     #
    #     # bgl.glColor4f(1, 1, 1, 0.025)   # inner ring
    #     # bgl.glBegin(bgl.GL_LINE_STRIP)
    #     # for x,y in self.points:
    #     #     p = (cs_inner * ((cx * x) + (cy * y))) + cp
    #     #     bgl.glVertex3f(*p)
    #     # bgl.glEnd()
    #
    #     ######################################
    #     # reset to defaults
    #
    #     bgl.glDepthFunc(bgl.GL_LEQUAL)
    #     bgl.glDepthMask(bgl.GL_TRUE)
    #
    #     bgl.glDepthRange(0, 1)
    #
    #     return

    #############################################
