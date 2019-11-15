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
import math

# Blender imports
import bpy
from bpy.types import Object
import bmesh
from bmesh.types import BMesh, BMVert, BMEdge, BMFace
from mathutils import Vector, Matrix, Color
from mathutils.bvhtree import BVHTree

# Module imports
from .python_utils import *


def smooth_bm_faces(faces:iter):
    """ set given bmesh faces to smooth """
    faces = confirm_iter(faces)
    for f in faces:
        f.smooth = True


# all functions below this line were adapted from code by Patrick Moore
# https://github.com/patmo141/bmesh_utilities


###############################
### Topology Operators   ######
###############################
# COMPLETE
# also known as 'face_neighbors_by_edge'/'face_neighbors_by_face' in 'cut_mesh'
def face_neighbors(bmface:BMFace, by:str="edges", limit:set=set()):
    neighbors = []
    for ed in getattr(bmface, by):
        if ed in limit: continue
        neighbors += [f for f in ed.link_faces if f != bmface]
    return neighbors

# COMPLETE
def face_neighbors_strict(bmface:BMFace):
    neighbors = []
    for ed in bmface.edges:
        if not (ed.verts[0].is_manifold and ed.verts[1].is_manifold):
            if len(ed.link_faces) == 1:
                print("found an ed, with two non manifold verts")
            continue
        neighbors += [f for f in ed.link_faces if f != bmface]
    return neighbors


# COMPLETE
def vert_neighbors(bmvert:BMVert):
    neighbors = [ed.other_vert(bmvert) for ed in bmvert.link_edges]
    return neighbors

# COMPLETE
# also known as 'vert_neighbors' in 'cut_mesh'
def vert_neighbors_manifold(bmvert:BMVert):
    return [v for v in vert_neighbors(bmvert) if v.is_manifold]

#https://blender.stackexchange.com/questions/92406/circular-order-of-edges-around-vertex
# Return edges around param vertex in counter-clockwise order
def connectedEdgesFromVertex_CCW(vertex):
    vertex.link_edges.index_update()
    first_edge = vertex.link_edges[0]

    edges_CCW_order = []

    edge = first_edge
    while edge not in edges_CCW_order:
        edges_CCW_order.append(edge)
        edge = rightEdgeForEdgeRegardToVertex(edge, vertex)

    return edges_CCW_order
# Return the right edge of param edge regard to param vertex
#https://blender.stackexchange.com/questions/92406/circular-order-of-edges-around-vertex
def rightEdgeForEdgeRegardToVertex(edge:BMEdge, vertex):
    right_loop = None

    for loop in edge.link_loops:
        if loop.vert == vertex:
            right_loop = loop
            break
    return loop.link_loop_prev.edge


def decrease_vert_selection(bme:BMesh, selected_verts, iterations:int=1):
    """ remove outer layer of selection

    TODO, treat this as a region growing subtraction of the border
    rather than iterate the whole selection each time.
    """

    # make a copy instead of modify in place, in case
    # oritinal selection is important
    sel_verts = set(selected_verts)

    def is_boundary(v):
        return not all([ed.other_vert(v) in sel_verts for ed in v.link_edges])

    for i in range(iterations):

        border = [v for v in sel_verts if is_boundary(v)] #TODO...smarter way to find new border...connected to old border
        sel_verts.difference_update(border)

    return sel_verts
def increase_vert_selection(bme:BMesh, selected_verts, iterations:int=1):
    """ grow outer layer of selection

    TODO, treat this as a region growing subtraction of the border
    rather than iterate the whole selection each time.
    """

    # make a copy instead of modify in place, in case
    # oritinal selection is important
    sel_verts = set(selected_verts)

    new_verts = set()
    for v in sel_verts:
        new_verts.update(vert_neighbors(v))

    iters = 0
    while iters < iterations and new_verts:
        iters += 1
        new_candidates = set()
        for v in new_verts:
            new_candidates.update(vert_neighbors(v))

        new_verts = new_candidates - sel_verts

        if new_verts:
            sel_verts |= new_verts

    return sel_verts


# COMPLETE
def grow_selection(bme:BMesh, start_faces:set, max_iters:int=1000):
    """ a simple "select more" faces algorithm

    Parameters:
        bme (BMesh): BMesh object
        start_faces (set, list): original selection of BMFaces
        max_iters (int): maximum recursions to select neightbors

    Returns:
        set(BMFaces)
    """

    total_selection = set(start_faces)
    new_faces = set()
    for f in start_faces:
        new_faces.update(face_neighbors_by_vert(f))

    print("there were %i start_faces" % len(start_faces))
    print("there are %i new_faces" % len(new_faces))

    iters = 0
    while iters < max_iters and len(new_faces):
        iters += 1
        candidates = set()
        for f in new_faces:
            candidates.update(face_neighbors(f))

        new_faces = candidates - total_selection
        if new_faces:
            total_selection |= new_faces

    if iters == max_iters:
        print("max iterations reached")

    return total_selection


def flood_selection_by_verts(bme:BMesh, selected_faces:set, seed_face:BMFace, max_iters:int=1000):
    """

    Parameters:
        bme (BMesh): BMesh object
        selected_faces (set, list): should create a closed face loop to contain "flooded" selection
                                    if an empty set, selection willg grow to non manifold boundaries
        seed_face (BMFace): a face within/out selected_faces loop
        max_iters (int): maximum recursions to select neightbors

    Returns:
        set(BMFaces)
    """
    total_selection = set([f for f in selected_faces])
    levy = set([f for f in selected_faces])  #it's funny because it stops the flood :-)

    new_faces = set(face_neighbors_strict(seed_face)) - levy
    iters = 0
    while iters < max_iters and new_faces:
        iters += 1
        new_candidates = set()
        for f in new_faces:
            new_candidates.update(face_neighbors_strict(f))

        new_faces = new_candidates - total_selection

        if new_faces:
            total_selection |= new_faces
    if iters == max_iters:
        print("max iterations reached")
    return total_selection

def flood_selection_faces(bme:BMesh, selected_faces:set, seed_face:BMFace, max_iters:int=1000, verbose:bool=True):
    """

    Parameters:
        bme (BMesh): BMesh object
        selected_faces (set, list): should create a closed face loop to contain "flooded" selection
                                    if an empty set, selection will grow to non manifold boundaries
        seed_face (BMFace): a face within/out selected_faces loop
        max_iters (int): maximum recursions to select neightbors
        verbose (bool): print helpful information

    Returns:
        set(BMFaces)
    """
    total_selection = set(selected_faces)
    levy = set(selected_faces)  #it's funny because it stops the flood :-)

    new_faces = set(face_neighbors(seed_face)) - levy
    iters = 0
    while iters < max_iters and new_faces:
        iters += 1
        new_candidates = set()
        for f in new_faces:
            new_candidates.update(face_neighbors(f))

        new_faces = new_candidates - total_selection

        if new_faces:
            total_selection |= new_faces

    if verbose and iters == max_iters:
        print("max iterations reached")

    return total_selection

def flood_selection_edge_loop(bme:BMesh, edge_loop:set, seed_face:BMFace, max_iters:int=1000, verbose:bool=True):
    """

    Parameters:
        bme (BMesh): BMesh object
        edge_loop (set, list): should create a closed face loop to contain "flooded" selection
                               if an empty set, selection will grow to non manifold boundaries
        seed_face (BMFace): a face within/out selected_faces loop
        max_iters (int): maximum recursions to select neightbors
        verbose (bool): print helpful information

    Returns:
        set(BMFaces)
    """
    edge_levy = set(edge_loop)

    total_selection = set()
    total_selection.add(seed_face)

    #face_levy = set()
    #for e in edge_loop:
    #    face_levy.update([f for f in e.link_faces])  # it's funny because it stops the flood :-)

    new_faces = set(face_neighbors(seed_face, limit=edge_levy)) #- face_levy
    iters = 0
    while iters < max_iters and new_faces:
        iters += 1
        new_candidates = set()
        for f in new_faces:
            new_candidates.update(face_neighbors(f, limit=edge_levy))

        new_faces = (new_candidates - total_selection)
        #remove = set()
        #for f in new_faces:
        #    if any([e for e in f.edges if e in edge_levy]):
        #        remove.add(f)

        if new_faces:
            total_selection |= new_faces
            #new_faces -= face_levy
    if iters == max_iters:
        print("max iterations reached")


    return total_selection

def grow_selection_to_find_face(bme:BMesh, start_face:BMFace, stop_face:BMFace, max_iters:int=1000, verbose:bool=True):
    """ Grows selection iterartively with neighbors until stop face is reached

    contemplating indexes vs faces themselves?  will try both ways for speed

    Parameters:
        bme (BMesh): BMesh object
        start_face (BMFace): face to grow selection from
        stop_face (BMFace): stop growing selection if this face is reached
        max_iters (int): maximum recursions to select neightbors
        verbose (bool): print helpful information

    Returns:
        set(BMFaces)
    """

    total_selection = set([start_face])
    new_faces = set(face_neighbors(start_face))

    if stop_face in new_faces:
        total_selection |= new_faces
        return total_selection

    iters = 0
    while iters < max_iters and stop_face not in new_faces:
        iters += 1
        candidates = set()
        for f in new_faces:
            candidates.update(face_neighbors(f))

        new_faces = candidates - total_selection
        if new_faces:
            total_selection |= new_faces

    if iters == max_iters:
        print("max iterations reached")

    return total_selection

def grow_to_find_mesh_end(bme:BMesh, start_face:BMFace, max_iters:int=20, verbose:bool=True):
    """ Grows selection until a non manifold face is reached.

    Parameters:
        bme (BMesh): BMesh object
        start_face (list): first face to grow selection from
        max_iters (int): maximum recursions to select neightbors
        verbose (bool): print helpful information

    Returns:
        a dictionary with keys 'VERTS' 'EDGES' containing lists of the corresponding data

    geom = dictionary
    geom['end'] = BMFace or None, the first non manifold face to be found
    geom['faces'] = list [BMFaces], all the faces encountered on the way

    """

    geom = {}

    total_selection = set([start_face])
    new_faces = set(face_neighbors(start_face))

    def not_manifold(faces):
        for f in faces:
            if not all([ed.is_manifold for ed in f.edges]):
                return f
        return None

    iters = 0
    stop_face = not_manifold(new_faces)
    if stop_face:
        total_selection |= new_faces
        geom["end"] = stop_face
        geom["faces"] = total_selection
        return geom

    while new_faces and iters < max_iters and not stop_face:
        iters += 1
        candidates = set()
        for f in new_faces:
            candidates.update(face_neighbors(f))

        new_faces = candidates - total_selection
        if new_faces:
            total_selection |= new_faces
            stop_face = not_manifold(new_faces)

    if iters == max_iters:
        if verbose:
            print("max iterations reached")
        geom["end"] = None
    elif not stop_face:
        if verbose:
            print("completely manifold mesh")
        geom["end"] = None
    else:
        geom["end"] = stop_face

    geom["faces"] = total_selection
    return geom

# COMPLETE. TODO: support 'edges' item_type
def bmesh_loose_parts(bme:BMesh, item_type:str="faces", selected:set=None, max_iters:int=100, verbose=False):
    """ Gets list of loose parts in bmesh

    Parameters:
        bme (BMesh): BMesh object
        item_type (str): string in ['faces', 'edges', 'verts'] for type of item on islands to be returned
        selected (set, list, None): selected BMFaces/BMEdges/BMVerts (must match item_type)
        max_iters (int): maximum number of loose parts to be found

    Returns:
        list of islands (lists) of BMFaces/BMVerts
    """
    assert item_type in ("faces", "edges", "verts")

    # get set of total faces/edges/verts
    if selected is None or len(selected) == 0:
        total_items = set(getattr(bme, item_type)[:])
    else:
        total_items = set(selected)  # don't want to modify initial set

    islands = []
    iters = 0
    while len(total_items) and iters < max_iters:
        iters += 1
        seed = total_items.pop()

        if item_type == "faces":
            island = flood_selection_faces(bme, {}, seed, max_iters=10000, verbose=verbose)
        elif item_type == "edges":
            raise Exception("Edges not yet supported by bmesh_loose_parts function")
        elif item_type == "verts":
            island = flood_island_within_selected_verts(bme, total_items, seed, max_iters=10000, verbose=verbose)

        islands.append(island)
        total_items.difference_update(island)

    return islands

def walk_non_man_edge(bme:BMesh, start_edge:BMEdge, stop:set, max_iters:int=5000):
    """

    Parameters:
        bme (BMesh): BMesh object
        start_edge (BMEdge): edge to start walking from
        stop (set): set of verts or edges to stop when reached
        max_iters (int): maximum recursions to select neightbors

    Returns:
        list of edge loops
    """

    # stop criteria
    #  found element in stop set
    #  found starting edge (completed loop)
    #  found vert with 2 other non manifold edges

    def next_pair(prev_ed, prev_vert):
        v_next = prev_ed.other_vert(prev_vert)
        eds = [e for e in v_next.link_edges if not e.is_manifold and e != prev_ed]
        print(eds)
        if len(eds):
            return eds[0], v_next
        else:
            return None, None

    chains = []
    for v in start_edge.verts:
        edge_loop = []
        prev_v = start_edge.other_vert(v)
        prev_ed = start_edge
        next_ed, next_v = next_pair(prev_ed, prev_v)
        edge_loop += [next_ed]
        iters = 0
        while next_ed and next_v and not (next_ed in stop or next_v in stop) and iters < max_iters:
            iters += 1

            next_ed, next_v = next_pair(next_ed, next_v)
            if next_ed:
                edge_loop += [next_ed]

        chains += [edge_loop]

    return chains

# segmentation only
def flood_island_within_selected_verts(bme:BMesh, selected_verts:set, seed_element, max_iters:int=10000, verbose:bool=False):
    """ final all connected verts to seed element that are witin selected_verts

    Parameters:
        bme (BMesh): BMesh object
        selected_verts (list, set): selected vertices
                                    if an empty set, selection will grow to non manifold boundaries
        seed_element (BMVert, BMFace): a vertex or face within/out perimeter verts loop
        stop (set): set of verts or edges to stop when reached
        max_iters (int): maximum recursions to select neightbors
        verbose (bool): print helpful information

    Returns:
        set of verticies
    """

    selected_verts = set(selected_verts)

    flood_selection = set()
    flood_selection.add(seed_element)
    new_verts = set([v for v in vert_neighbors(seed_element) if v in selected_verts])

    if verbose:
        print("there are %i new_verts at first iteration" % len(new_verts))
    iters = 0
    while iters < max_iters and new_verts:
        iters += 1
        new_candidates = set()
        for v in new_verts:
            new_candidates.update(vert_neighbors(v))

        new_verts = new_candidates & selected_verts
        if verbose:
            print("at iteration %i there are %i new_verts" % (iters, len(new_verts)))

        if new_verts:
            flood_selection |= new_verts
            selected_verts -= new_verts

    if verbose and iters == max_iters:
        print("max iterations reached")

    return flood_selection

# segmentation only
def flood_selection_vertex_perimeter(bme:BMesh, perimeter_verts:set, seed_element, max_iters:int=10000):
    """ final all connected verts to seed element that are witin selected_verts

    Parameters:
        bme (BMesh): BMesh object
        perimeter_verts (list, set): should create a closed edge loop to contain "flooded" selection.
                                     if an empty set, selection will grow to non manifold boundaries
        seed_element (BMVert, BMFace): a vertex or face within/out perimeter verts loop
        max_iters (int): maximum recursions to select neightbors

    Returns:
        set of verticies
    """

    flood_selection = set()
    if type(seed_element) is BMVert:
        flood_selection.add(seed_element)
        new_verts = set(vert_neighbors(seed_element)) - perimeter_verts

    elif type(seed_element) is BMFace:
        flood_selection.update(seed_element.verts[:])
        for v in seed_element.verts:
            new_verts = set(vert_neighbors(v)) - perimeter_verts

    flood_selection |= perimeter_verts

    iters = 0
    while iters < max_iters and new_verts:
        iters += 1
        new_candidates = set()
        for v in new_verts:
            new_candidates.update(vert_neighbors(v))

        new_verts = new_candidates - flood_selection

        if new_verts:
            flood_selection |= new_verts

    if iters == max_iters:
        print("max iterations reached")

    return flood_selection

# segmentation only
def partition_faces_between_edge_boundaries(bme:BMesh, input_faces:set, boundary_edges:set, max_iters:int=1000):
    """

    Parameters:
        bme (BMesh): BMesh object
        input_faces (list, set):
        boundary_edges (list, set):
        max_iters (int): maximum recursions to select neightbors

    Returns:
        list of islands (lists) of BMFaces
    """

    if len(input_faces) == 0:
        input_faces = set(bme.faces[:])

    iters = 0
    islands = []
    while len(input_faces) and iters < max_iters:
        iters += 1

        seed_face = input_faces.pop()
        island = flood_selection_edge_loop(bme, boundary_edges, seed_face, max_iters=10000)

        input_faces.difference_update(island)

        islands += [island]

    return islands


def edge_loops_from_bmedges(bme:BMesh, bm_edges:list, ret:dict={"VERTS"}):
    """
    Parameters:
        bme (BMesh): BMEsh object
        bm_edges (list): an UNORDERED list of edge indices in the bmesh
        ret (dict): a dictionary with {'VERTS', 'EDGES'}  which determines what data to return

    Returns:
        geom_dict: a dictionary with keys 'VERTS' 'EDGES' containing lists of the corresponding data

                   geom_dict['VERTS'] =   [ [1, 6, 7, 2], ...]

                   closed loops have matching start and end vert indices
                   closed loops will not have duplicate edge indices

    Notes:  This method is not "smart" in any way, and does not leverage BMesh
    connectivity data.  Therefore it could iterate  len(bm_edges)! (factorial) times
    There are better methods to use if your bm_edges are already in order  This is mostly
    used to sort non_man_edges = [ed.index for ed in bmesh.edges if not ed.is_manifold]
    There will be better methods regardless that utilize walking some day....
    """
    geom_dict = dict()
    geom_dict["VERTS"] = []
    geom_dict["EDGES"] = []
    edges = bm_edges.copy()

    while edges:
        current_edge = bmesh.edges[edges.pop()]

        vert_e, vert_st = current_edge.verts[:]
        vert_end, vert_start = vert_e.index, vert_st.index
        line_poly = [vert_start, vert_end]
        ed_loop = [current_edge.index]
        ok = True
        while ok:
            ok = False
            # for i, ed in enumerate(edges):
            i = len(edges)
            while i:
                i -= 1
                ed = bmesh.edges[edges[i]]
                v_1, v_2 = ed.verts
                v1, v2 = v_1.index, v_2.index
                if v1 == vert_end:
                    line_poly.append(v2)
                    ed_loop.append(ed.index)
                    vert_end = line_poly[-1]
                    ok = 1
                    del edges[i]
                    # break
                elif v2 == vert_end:
                    line_poly.append(v1)
                    ed_loop.append(ed.index)
                    vert_end = line_poly[-1]
                    ok = 1
                    del edges[i]
                    # break
                elif v1 == vert_start:
                    line_poly.insert(0, v2)
                    ed_loop.insert(0, ed.index)
                    vert_start = line_poly[0]
                    ok = 1
                    del edges[i]
                    # break
                elif v2 == vert_start:
                    line_poly.insert(0, v1)
                    ed_loop.insert(0, ed.index)
                    vert_start = line_poly[0]
                    ok = 1
                    del edges[i]
                    # break

        if "VERTS" in ret:
            geom_dict["VERTS"] += [line_poly]
        if "EDGES" in ret:
            print("adding edge loop to dict")
            geom_dict["EDGES"] += [ed_loop]

    return geom_dict

# CAN WE DELETE THIS?
def edge_loops_from_bmedges_old(bmesh:BMesh, bm_edges:list):
    """
    Edge loops defined by edges (indices)

    Takes [mesh edge indices] or a list of edges and returns the edge loops

    return a list of vertex indices.
    [ [1, 6, 7, 2], ...]

    closed loops have matching start and end values.
    """
    line_polys = []
    edges = bm_edges.copy()

    while edges:
        current_edge = bmesh.edges[edges.pop()]
        vert_e, vert_st = current_edge.verts[:]
        vert_end, vert_start = vert_e.index, vert_st.index
        line_poly = [vert_start, vert_end]

        ok = True
        while ok:
            ok = False
            #for i, ed in enumerate(edges):
            i = len(edges)
            while i:
                i -= 1
                ed = bmesh.edges[edges[i]]
                v_1, v_2 = ed.verts
                v1, v2 = v_1.index, v_2.index
                if v1 == vert_end:
                    line_poly.append(v2)
                    vert_end = line_poly[-1]
                    ok = 1
                    del edges[i]
                    # break
                elif v2 == vert_end:
                    line_poly.append(v1)
                    vert_end = line_poly[-1]
                    ok = 1
                    del edges[i]
                    #break
                elif v1 == vert_start:
                    line_poly.insert(0, v2)
                    vert_start = line_poly[0]
                    ok = 1
                    del edges[i]
                    # break
                elif v2 == vert_start:
                    line_poly.insert(0, v1)
                    vert_start = line_poly[0]
                    ok = 1
                    del edges[i]
                    #break
        line_polys.append(line_poly)

    return line_polys

def face_region_boundary_loops(bme:BMesh, sel_faces:list):
    """

    Parameters:
        bme (BMesh): BMesh object
        sel_faces (list):  list of face indices

    Returns:
        [face indices], [ed indices]
    """
    face_set = set(sel_faces)
    edges_raw = [ed.index for ed in bme.edges if ed.select and len([f.index for f in ed.link_faces if f.index in face_set]) == 1]

    geom_dict = edge_loops_from_bmedges(bme, edges_raw, ret={"VERTS", "EDGES"})

    return geom_dict


def find_face_loop(bme:BMesh, edge:BMEdge, select:bool=False):
    """ takes a bmedge, and walks perpendicular to it

    Parameters:
        bme (BMesh): BMesh object
        edge (BMEdge): edge to start from
        select (bool): select faces and edges as we go

    Returns:
        [face indices], [ed indices]
    """
    #reality check
    if not len(ed.link_faces): return []

    def ed_to_vect(ed):
        vect = ed.verts[1].co - ed.verts[0].co
        vect.normalize()
        return vect

    def next_edge(cur_face, cur_ed):
        ledges = [ed for ed in cur_face.edges]
        n = ledges.index(cur_ed)
        j = (n+2) % 4
        return cur_face.edges[j]

    def next_face(cur_face, edge):
        if len(edge.link_faces) == 1: return None
        next_face = [f for f in edge.link_faces if f != cur_face][0]
        return next_face

    loop_eds = []
    loop_faces = []
    loop_revs = []

    for f in ed.link_faces:
        if len(f.edges) != 4: continue
        eds = [ed.index]
        fs = [f.index]
        revs = [False]

        f_next = True
        f_cur = f
        ed_cur = ed
        while f_next != f:
            if select:
                f_cur.select_set(True)
                ed_cur.select_set(True)

            ed_next = next_edge(f_cur, ed_cur)
            eds += [ed_next.index]

            parallel = ed_to_vect(ed_next).dot(ed_to_vect(ed_cur)) > 0
            prev_rev = revs[-1]
            rever = parallel == prev_rev
            revs += [rever]

            f_next = next_face(f_cur, ed_next)
            if not f_next: break

            fs += [f_next.index]
            if len(f_next.verts) != 4:
                break

            ed_cur = ed_next
            f_cur = f_next

        #if we looped
        if f_next == f:

            face_loop_fs = fs
            face_loop_eds = eds[:len(eds)-1]

            return face_loop_fs, face_loop_eds
        else:
            if len(fs):
                loop_faces.append(fs)
                loop_eds.append(eds)
                loop_revs.append(revs)

    if len(loop_faces) == 2:
        loop_faces[0].reverse()
        face_loop_fs = loop_faces[0] +  loop_faces[1]
        tip = loop_eds[0][1:]
        tip.reverse()
        face_loop_eds = tip + loop_eds[1]
        rev_tip = loop_revs[0][1:]
        rev_tip.reverse()


    elif len(loop_faces) == 1:
        face_loop_fs = loop_faces[0]
        face_loop_eds = loop_eds[0]

    else:
        face_loop_fs, face_loop_eds = [], []

    return  face_loop_fs, face_loop_eds


def edge_loop_neighbors(bme:BMesh, edge_loop:list, strict:bool=False, trim_tails:bool=True, expansion:str="EDGES", quad_only:bool=True):
    """

    Parameters:
        bme (BMesh): BMesh object
        edge_loop (list): list of BMEdge indices.  Not necessarily in order, possibly multiple edge loops
        strict (bool): False  - not strict, returns all loops regardless of topology
                       True   - loops must be connected by quads only
                                Only returns  if the parallel loops are exactly the same length as original loop
        trim_tails (bool): will trim p shaped loops or figure 8 loops
        expansion (str): 'EDGES'  - a single edge loop within a mesh will return
                                    2 parallel and equal length edge loops
                         'VERTS'  - a single edge loop within a mesh will return
                                    a single edge loop around the single loop
                                    only use with strict = False
        quad_only (bool): Allow for generic edge loop expansion in triangle meshes if False


    Returns:
        geom_dict: dictionary with keys 'VERTS' 'EDGES' 'FACES'
                   the 'VERTS' and 'EDGES' lists are correlated.
                   e.g. geom_dict['VERTS'][0] and geom_dict['EDGES'][0] are corresponding vert and edge loops
                   However, geom_dict['FACES'][0] may correlate with geom_dict['EDGES'][1]



    """


    ed_loops = edge_loops_from_bmedges(bme, edge_loop, ret={"VERTS", "EDGES"})

    geom_dict = dict()
    geom_dict["VERTS"] = []
    geom_dict["EDGES"] = []
    geom_dict["FACES"] = []

    for v_inds, ed_inds in zip(ed_loops["VERTS"], ed_loops["EDGES"]):

        v0 = bme.verts[v_inds[0]]
        e0 = bme.edges[ed_inds[0]]
        v1 = e0.other_vert(v0)

        orig_eds = set(ed_inds)
        #find all the faces directly attached to this edge loop
        all_faces = set()

        if quad_only:
            if expansion == "EDGES":
                for e_ind in ed_inds:
                    all_faces.update([f.index for f in bme.edges[e_ind].link_faces if len(f.verts) == 4])

            elif expansion == "VERTS":
                for v_ind in v_inds:
                    all_faces.update([f.index for f in bme.verts[v_ind].link_faces if len(f.verts) == 4])

        else:
            for e_ind in ed_inds:
                for v in bme.edges[e_ind].verts:
                    all_faces.update([f.index for f in v.link_faces])

        #find all the edges perpendicular to this edge loop
        perp_eds = set()
        for v_ind in v_inds:
            perp_eds.update([ed.index for ed in bme.verts[v_ind].link_edges if ed.index not in orig_eds])


        parallel_eds = []

        if quad_only:
            for f_ind in all_faces:
                parallel_eds += [ed.index for ed in bme.faces[f_ind].edges if
                             ed.index not in perp_eds and ed.index not in orig_eds
                             and not (all([f.index in all_faces for f in ed.link_faces]) and trim_tails)]
        else:
            for f_ind in all_faces:
                parallel_eds += [ed.index for ed in bme.faces[f_ind].edges if
                                 ed.index not in orig_eds
                                 and not all([f.index in all_faces for f in ed.link_faces])]

            print("Triangle Problems ")
            print(parallel_eds)
        #sort them!
        parallel_loops =  edge_loops_from_bmedges(bme, parallel_eds, ret = {"VERTS", "EDGES"})

        #get the face loops, a little differently, just walk from 2 perpendicular edges

        for ed in v1.link_edges:
            if ed.index not in perp_eds: continue
            f_inds, _e_inds = find_face_loop(bme, ed, select=False)
            #print(f_inds)
            #keep only the part of face loop direclty next door
            if strict:
                f_inds = [f for f in f_inds if f in all_faces]
            geom_dict["FACES"] += [f_inds]

        if strict:
            if all([len(e_loop) == len(ed_inds) for e_loop in parallel_loops["EDGES"]]):
                for v_loop in parallel_loops["VERTS"]:
                    geom_dict["VERTS"] += [v_loop]
                for e_loop in parallel_loops["EDGES"]:
                    geom_dict["EDGES"] += [e_loop]


            elif any([len(e_loop) == len(ed_inds) for e_loop in parallel_loops["EDGES"]]):

                for pvs, peds in zip(parallel_loops["VERTS"],parallel_loops["EDGES"]):
                    if len(peds) == len(ed_inds):
                        geom_dict["VERTS"] += [pvs]
                        geom_dict["EDGES"] += [peds]


        else:
            for v_loop in parallel_loops["VERTS"]:
                geom_dict["VERTS"] += [v_loop]
            for e_loop in parallel_loops["EDGES"]:
                geom_dict["EDGES"] += [e_loop]


    return geom_dict

######################################
# BMESH CREATION FUNCTIONS           #
######################################

def join_bmesh(source, target, src_trg_map, src_mx=None, trg_mx=None):
    """

    """
    L = len(target.verts)
    print("Target has %i verts" % L)

    print("Source has %i verts" % len(source.verts))
    l = len(src_trg_map)
    print("is the src_trg_map being sticky...%i" % l)
    if not src_mx:
        src_mx = Matrix.Identity(4)

    if not trg_mx:
        trg_mx = Matrix.Identity(4)
        i_trg_mx = Matrix.Identity(4)
    else:
        i_trg_mx = trg_mx.inverted()



    new_bmverts = []

    source.verts.ensure_lookup_table()

    for v in source.verts:
        if v.index not in src_trg_map:
            new_ind = len(target.verts)
            new_bv = target.verts.new(i_trg_mx * src_mx * v.co)
            new_bmverts.append(new_bv)
            # new_bv.index = new_ind
            src_trg_map[v.index] = new_ind

    # new_bmverts = [target.verts.new(i_trg_mx * src_mx * v.co) for v in source.verts]# if v.index not in src_trg_map]

    # def src_to_trg_ind(v):
    #    subbed = False
    #    if v.index in src_trg_map:
    #
    #       new_ind = src_trg_map[v.index]
    #        subbed = True
    #    else:
    #        new_ind = v.index + L  #TODO, this takes the actual versts from sources, these verts are in target
    #
    #    return new_ind, subbed

    # new_bmfaces = [target.faces.new(tuple(new_bmverts[v.index] for v in face.verts)) for face in source.faces]
    target.verts.index_update()
    # target.verts.sort()  # does this still work?
    target.verts.ensure_lookup_table()
    # print("new faces")
    # for f in source.faces:
        # print(tuple(src_to_trg_ind(v) for v in f.verts))

    # subbed = set()
    new_bmfaces = []
    for f in source.faces:
        v_inds = []
        for v in f.verts:
            new_ind = src_trg_map[v.index]
            v_inds.append(new_ind)

        new_bmfaces += [target.faces.new(tuple(target.verts[i] for i in v_inds))]

    # new_bmfaces = [target.faces.new(tuple(target.verts[src_to_trg_ind(v)] for v in face.verts)) for face in source.faces]
    target.faces.ensure_lookup_table()
    target.verts.ensure_lookup_table()
    target.verts.index_update()

    # throw away the loose verts...not very elegant with edges and what not
    # n_removed = 0
    # for vert in new_bmverts:
    #    if (vert.index - L) in src_trg_map: #these are verts that are not needed
    #        target.verts.remove(vert)
    #        n_removed += 1

    # bmesh_delete(target, verts=del_verts)

    target.verts.index_update()
    target.verts.ensure_lookup_table()
    target.faces.ensure_lookup_table()

    new_L = len(target.verts)

    if src_trg_map:
        if new_L != L + len(source.verts) -l:
            print("seems some verts were left in that should not have been")

    del src_trg_map

def join_bmesh2(source, target, src_mx=None, trg_mx=None):

    src_trg_map = dict()
    L = len(target.verts)
    if not src_mx:
        src_mx = Matrix.Identity(4)

    if not trg_mx:
        trg_mx = Matrix.Identity(4)
        i_trg_mx = Matrix.Identity(4)
    else:
        i_trg_mx = trg_mx.inverted()


    new_bmverts = []
    source.verts.ensure_lookup_table()

    for v in source.verts:
        if v.index not in src_trg_map:
            new_ind = len(target.verts)
            new_bv = target.verts.new(i_trg_mx * src_mx * v.co)
            new_bmverts.append(new_bv)
            src_trg_map[v.index] = new_ind


    target.verts.index_update()
    target.verts.ensure_lookup_table()

    new_bmfaces = []
    for f in source.faces:
        v_inds = []
        for v in f.verts:
            new_ind = src_trg_map[v.index]
            v_inds.append(new_ind)

        new_bmfaces += [target.faces.new(tuple(target.verts[i] for i in v_inds))]

    target.faces.ensure_lookup_table()
    target.verts.ensure_lookup_table()
    target.verts.index_update()


    target.verts.index_update()
    target.verts.ensure_lookup_table()
    target.faces.ensure_lookup_table()

    new_L = len(target.verts)


    if new_L != L + len(source.verts):
        print("seems some verts were left out")


def new_bmesh_from_bmelements(geom):
    """

    """

    out_bme = bmesh.new()
    out_bme.verts.ensure_lookup_table()
    out_bme.faces.ensure_lookup_table()

    faces = [ele for ele in geom if type(ele) is BMFace]
    verts = [ele for ele in geom if type(ele) is BMVert]

    vs = set(verts)
    for f in faces:
        vs.update(f.verts[:])

    src_trg_map = dict()
    new_bmverts = []
    for v in vs:

        new_ind = len(out_bme.verts)
        new_bv = out_bme.verts.new(v.co)
        new_bmverts.append(new_bv)
        src_trg_map[v.index] = new_ind

    out_bme.verts.ensure_lookup_table()
    out_bme.faces.ensure_lookup_table()

    new_bmfaces = []
    for f in faces:
        v_inds = []
        for v in f.verts:
            new_ind = src_trg_map[v.index]
            v_inds.append(new_ind)

        new_bmfaces += [out_bme.faces.new(tuple(out_bme.verts[i] for i in v_inds))]

    out_bme.faces.ensure_lookup_table()
    out_bme.verts.ensure_lookup_table()
    out_bme.verts.index_update()


    out_bme.verts.index_update()
    out_bme.verts.ensure_lookup_table()
    out_bme.faces.ensure_lookup_table()

    return out_bme


# doesn't belong here

def join_objects(obs, name:str=""):
    """
    uses BMesh to join objects.  Advantage is that it is context
    agnostic, so no editmode or bpy.ops has to be used.

    Parameters:
        obs (list): list of Blender objects
        name (str): name of new object

    Returns:
        new object with name specified.  Otherwise '_joined' will
        be added to the name of the first object in the list
    """
    target_bme = bmesh.new()
    trg_mx = obs[0].matrix_world
    name = name or obs[0].name + "_joined"

    for ob in obs:
        src_mx = ob.matrix_world

        if ob.data.is_editmode:
            src_bme = bmesh.from_editmesh(ob.data)
        else:
            src_bme = bmesh.new()
            if ob.type == "MESH":
                src_bme.from_object(ob, bpy.context.scene)
            else:
                me = ob.to_mesh(bpy.context.scene, apply_modifiers=True, settings="PREVIEW")
                src_bme.from_mesh(me)
                bpy.data.meshes.remove(me)
        join_bmesh(src_bme, target_bme, src_mx, trg_mx)
        src_bme.free()

    new_me = bpy.data.meshes.new(name)
    new_ob = bpy.data.objects.new(name, new_me)
    new_ob.matrix_world = trg_mx
    target_bme.to_mesh(new_me)
    target_bme.free()
    return new_ob

def join_bmesh_map(source:BMesh, target:BMesh, src_trg_map:set=None, src_mx:Matrix=None, trg_mx:Matrix=None):
    """

    Parameters:
        source (BMesh): BMesh object source
        target (BMesh): BMesh object target
        src_trg_map (set): set of indices
        src_mx (Matrix): matrix of the source BMesh object
        trg_mx (Matrix): matrix of the target BMesh object

    Returns:
        None
    """


    L = len(target.verts)

    if not src_trg_map:
        src_trg_map = {-1:-1}
    l = len(src_trg_map)
    print("There are %i items in the vert map" % len(src_trg_map))
    if not src_mx:
        src_mx = Matrix.Identity(4)

    if not trg_mx:
        trg_mx = Matrix.Identity(4)
        i_trg_mx = Matrix.Identity(4)
    else:
        i_trg_mx = trg_mx.inverted()


    old_bmverts = [v for v in target.verts]  # this will store them in order
    new_bmverts = [] # these will be created in order

    source.verts.ensure_lookup_table()

    for v in source.verts:
        if v.index not in src_trg_map:
            new_ind = len(target.verts)
            new_bv = target.verts.new(i_trg_mx * src_mx * v.co)
            new_bmverts.append(new_bv)  #gross...append
            src_trg_map[v.index] = new_ind

        else:
            print("vert alread in the map %i" % v.index)

    lverts = old_bmverts + new_bmverts

    target.verts.index_update()
    target.verts.ensure_lookup_table()

    new_bmfaces = []
    for f in source.faces:
        v_inds = []
        for v in f.verts:
            new_ind = src_trg_map[v.index]
            v_inds.append(new_ind)

        if any([i > len(lverts)-1 for i in v_inds]):
            print("impending index error")
            print(len(lverts))
            print(v_inds)

        if target.faces.get(tuple(lverts[i] for i in v_inds)):
            print(v_inds)
            continue
        new_bmfaces += [target.faces.new(tuple(lverts[i] for i in v_inds))]

        target.faces.ensure_lookup_table()
    target.verts.ensure_lookup_table()

    new_L = len(target.verts)

    if src_trg_map:
        if new_L != L + len(source.verts) -l:
            print("seems some verts were left in that should not have been")



###################################
#  Faster Bmesh Ops               #
###################################
def bmesh_ops_delete(bme:BMesh, geom:list, context:str="VERTS"):
    """

    Parameters:
        bme (BMesh): BMesh object
        geom (set, list of (BMVert, BMEdge, BMFace)): geometry to remove
        context (enum in ['VERTS', 'EDGES', 'FACES_ONLY', 'EDGES_FACES', 'FACES', 'FACES_KEEP_BOUNDARY', 'TAGGED_ONLY']): geometry types to delete

    Returns:
        None
    """

    verts = set()
    edges = set()
    faces = set()

    for item in geom:
        if type(item) is BMVert:
            verts.add(item)
        elif type(item) is BMEdge:
            edges.add(item)
        elif type(item) is BMFace:
            faces.add(item)

    # Remove geometry
    if context == "VERTS":
        for v in verts:
            bme.verts.remove(v)

    elif context == "EDGES":
        all_verts = set()
        for e in edges:
            all_verts |= set(e.verts)
            bme.edges.remove(e)
        for v in all_verts:
            if len(v.link_edges) == 0:
                bme.verts.remove(v)

    elif context == "FACES_ONLY":
        for f in faces:
            bme.faces.remove(f)

    elif context == "EDGES_FACES":
        remove_faces = set()
        for e in edges:
            remove_faces |= set(e.link_faces)
            bme.edges.remove(e)
        for f in remove_faces:
            if f.is_valid: bme.faces.remove(f)

    elif context.startswith("FACES"):
        all_edges = set()
        remove_edges = set()
        all_verts = set()
        for f in faces:
            remove_edges |= all_edges.intersection(set(f.edges))
            all_edges |= set(f.edges)
            all_verts |= set(f.verts)
            bme.faces.remove(f)
        if context == "FACES":
            all_edges = all_edges - remove_edges
            for e in all_edges:
                if len(e.link_faces) == 0:
                    bme.edges.remove(e)
        for e in remove_edges:
            if e.is_valid: bme.edges.remove(e)
        for v in all_verts:
            if len(v.link_edges) == 0:
                bme.verts.remove(v)

    elif context == "TAGGED_ONLY":
        for v in verts:
            bme.verts.remove(v)
        for e in edges:
            bme.edges.remove(e)
        for f in faces:
            bme.faces.remove(f)

def bmesh_delete(bme:BMesh, verts:set=None, edges:set=None, faces:set=None):
    """

    Parameters:
        bme (BMesh): BMesh object
        verts (set of BMVert): geometry to remove
        edges (set of BMEdge): geometry to remove
        faces (set of BMFace): geometry to remove

    Returns:
        None
    """
    if verts is not None:
        for v in verts:
            if v.is_valid: bme.verts.remove(v)
    if edges is not None:
        for e in edges:
            if e.is_valid: bme.verts.remove(e)
    if faces is not None:
        for f in faces:
            if f.is_valid: bme.verts.remove(f)


# d3g only
def bme_rip_vertex(bme, bmvert):

    for f in list(bmvert.link_faces):
        vs = list(f.verts)  # these come in order
        new_v = bme.verts.new(bmvert.co)

        # find the ripping vert
        ind = vs.index(bmvert)
        # replace it with the new vertex
        vs[ind] = new_v

        # create a new face
        new_f = bme.faces.new(vs)

    bme.verts.remove(bmvert)



####################################
###  Geometric Operators  ##########
####################################
def get_com_bmverts(lverts):
    n_verts = len(lverts)
    COM = Vector((0,0,0))
    for v in lverts:
        COM += v.co
    COM *= 1/n_verts
    return COM

def bound_box_bmverts(bmvs:iter):
    bounds = []
    for i in range(0,3):
        components = [v.co[i] for v in bmvs]
        low = min(components)
        high = max(components)
        bounds.append((low,high))

    return bounds
# Doesn't belong here, but is almost alwasy used on the return of bound_box_bmverts
def bbox_center(bounds):

    x = 0.5 * (bounds[0][0] + bounds[0][1])
    y = 0.5 * (bounds[1][0] + bounds[1][1])
    z = 0.5 * (bounds[2][0] + bounds[2][1])

    return Vector((x,y,z))

#this one goes in geometry because of the flat part
#also a topological operator
def bme_linked_flat_faces(bme:BMesh, start_face:BMFace, angle:float, max_iters=10000):
    """ takes a bmedge, and walks perpendicular to it

    Parameters:
        bme (BMesh): BMesh object
        start_face (BMFace): face to start from
        angle (float): angle in degrees

    Returns:
        list of BMFaces
    """

    no = start_face.normal
    angl_rad = math.pi/180 * angle

    #intiiate the flat faces
    flat_faces = set([start_face])

    #how we detect flat neighbors
    def flat_neighbors(bmf):
        neighbors = set()
        for v in bmf.verts:
            neighbors.update([f for f in v.link_faces if f not in flat_faces and f != bmf])
            flat_neighbors = set([f for f in neighbors if f.normal.dot(no) > 0 and f.normal.angle(no) < angl_rad])
        return flat_neighbors


    new_faces = flat_neighbors(start_face)

    iters = 0
    while len(new_faces) and iters < max_iters:
        iters += 1
        flat_faces |= new_faces

        newer_faces = set()
        for f in new_faces:
            newer_faces |= flat_neighbors(f)

        new_faces = newer_faces

    return list(flat_faces)

#Super Weird, Super Specific, Needs to go into it's own file
#Note a very genericly useful utility
def remove_undercuts(context:BMesh, ob:Object, view:Vector, world:bool=True, smooth:bool=True, epsilon:float=0.000001):
    """

    Parameters:
        context (BMesh): BMesh object
        ob (Object): mesh object
        view (Vector): view vector
        world (bool): True if view vector is in world coords
        smooth (bool):
        epsilon (float):

    Returns:
        Bmesh with Undercuts Removed?

    best to make sure normals are consistent beforehand
    best for manifold meshes, however non-man works
    noisy meshes can be compensated for with island threhold

    """


    # careful, this can get expensive with multires
    me = ob.to_mesh(context.scene, True, "RENDER")
    bme = bmesh.new()
    bme.from_mesh(me)
    bme.normal_update()
    bme.verts.ensure_lookup_table()
    bme.edges.ensure_lookup_table()
    bme.faces.ensure_lookup_table()

    bvh = BVHTree.FromBMesh(bme)

    # keep track of the world matrix
    mx = ob.matrix_world

    if world:
        # convert the view vector from  world to local coords
        i_mx = mx.inverted()
        view = i_mx.to_quaternion() * view

    face_directions = [[0]] * len(bme.faces)

    up_faces = set()
    overhang_faces = set()  # all faces pointing away from view
    # precalc all the face directions and store in dict
    for f in bme.faces:
        direction = f.normal.dot(view)

        if direction <= -epsilon:
            overhang_faces.add(f)
        else:
            up_faces.add(f)

        face_directions[f.index] = direction

    print("there are %i up_faces" % len(up_faces))
    print("there are %i down_faces" % len(overhang_faces))


    # for f in bme.faces:
    #    if f in overhangs:
    #        f.select_set(True)
    #    else:
    #        f.select_set(False)

    def face_neighbors_up(bmface:BMFace):
        return [n for n in face_neighbors(bmface) if n in up_faces]

    # remove smal islands from up_faces and add to overhangs
    max_iters = len(up_faces)
    iters_0 = 0
    islands_removed = 0

    up_faces_copy = up_faces.copy()
    upfacing_islands = []  # islands bigger than a certain threshold (by surface area?)
    while len(up_faces_copy) and iters_0 < max_iters:
        iters_0 += 1
        max_iters_1 = len(up_faces)
        seed = up_faces_copy.pop()
        new_faces = set(face_neighbors_up(seed))
        up_faces_copy -= new_faces

        island = set([seed])
        island |= new_faces

        iters_1 = 0
        while iters_1 < max_iters_1 and new_faces:
            iters_1 += 1
            new_candidates = set()
            for f in new_faces:
                new_candidates.update(face_neighbors_up(f))

            new_faces = new_candidates - island

            if new_faces:
                island |= new_faces
                up_faces_copy -= new_faces
        if len(island) < 75: #small patch surrounded by overhang, add to overhang area
            islands_removed += 1
            overhang_faces |= island
        else:
            upfacing_islands += [island]

    print("%i upfacing islands removed" % islands_removed)
    print("there are now %i down faces" % len(overhang_faces))

    def face_neighbors_down(bmface:BMFace):
        return [n for n in face_neighbors(bmface) if n in overhang_faces]

    overhang_faces_copy = overhang_faces.copy()
    overhang_islands = []  # islands bigger than a certain threshold (by surface area?)
    while len(overhang_faces_copy):
        seed = overhang_faces_copy.pop()
        new_faces = set(face_neighbors_down(seed))
        island = set([seed])
        island |= new_faces
        overhang_faces_copy -= new_faces
        iters = 0
        while iters < 100000 and new_faces:
            iters += 1
            new_candidates = set()
            for f in new_faces:
                new_candidates.update(face_neighbors_down(f))

            new_faces = new_candidates - island

            if new_faces:
                island |= new_faces
                overhang_faces_copy -= new_faces
        if len(island) > 75: #TODO, calc overhang factor.  Surface area dotted with direction
            overhang_islands += [island]

    for f in bme.faces:
        f.select_set(False)
    for ed in bme.edges:
        ed.select_set(False)
    for v in bme.verts:
        v.select_set(False)

    island_loops = []
    island_verts = []
    del_faces = set()
    for isl in overhang_islands:
        loop_eds = []
        loop_verts = set()
        del_faces |= isl
        for f in isl:
            for ed in f.edges:
                if len(ed.link_faces) == 1:
                    loop_eds += [ed]
                    loop_verts.update([ed.verts[0], ed.verts[1]])
                elif (ed.link_faces[0] in isl) and (ed.link_faces[1] not in isl):
                    loop_eds += [ed]
                    loop_verts.update([ed.verts[0], ed.verts[1]])
                elif (ed.link_faces[1] in isl) and (ed.link_faces[0] not in isl):
                    loop_eds += [ed]
                    loop_verts.update([ed.verts[0], ed.verts[1]])

            #f.select_set(True)
        island_verts += [list(loop_verts)]
        island_loops += [loop_eds]

    bme.faces.ensure_lookup_table()
    bme.edges.ensure_lookup_table()

    loop_edges = []
    for ed_loop in island_loops:
        loop_edges += ed_loop
        for ed in ed_loop:
            ed.select_set(True)

    loops_tools.relax_loops_util(bme, loop_edges, 5)

    for ed in bme.edges:
        ed.select_set(False)

    exclude_vs = set()
    for vs in island_verts:
        exclude_vs.update(vs)

    smooth_verts = []
    for v in exclude_vs:
        smooth_verts += [ed.other_vert(v) for ed in v.link_edges if ed.other_vert(v) not in exclude_vs]

    ret = bmesh.ops.extrude_edge_only(bme, edges = loop_edges)


    new_fs = [ele for ele in ret["geom"] if type(ele) is BMFace]
    new_vs = [ele for ele in ret["geom"] if type(ele) is BMVert]

    #TODO, ray cast down to base plane?
    for v in new_vs:
        v.co -= 10*view

    for f in new_fs:
        f.select_set(True)

    bmesh_delete(bme, faces=del_faces)

    del_verts = []
    for v in bme.verts:
        if all([f in del_faces for f in v.link_faces]):
            del_verts += [v]
    bmesh_delete(bme, verts=del_verts)


    del_edges = []
    for ed in bme.edges:
        if len(ed.link_faces) == 0:
            del_edges += [ed]
    print("deleting %i edges" % len(del_edges))
    bmesh_ops_delete(bme, geom=del_edges, context="EDGES_FACES")
    bmesh.ops.recalc_face_normals(bme, faces=new_fs)

    bme.normal_update()

    new_me = bpy.data.meshes.new(ob.name + "_blockout")

    obj = bpy.data.objects.new(new_me.name, new_me)
    context.scene.objects.link(obj)

    obj.select = True
    context.scene.objects.active = obj

    bme.to_mesh(obj.data)
    # Get material
    mat = bpy.data.materials.get("Model Material")
    if mat is None:
        # create material
        print("creating model material")
        mat = bpy.data.materials.new(name="Model Material")
        # mat.diffuse_color = Color((0.8, .8, .8))

    # Assign it to object
    obj.data.materials.append(mat)
    print("Model material added")

    mat2 = bpy.data.materials.get("Undercut Material")
    if mat2 is None:
        # create material
        mat2 = bpy.data.materials.new(name="Undercut Material")
        mat2.diffuse_color = Color((0.8, .2, .2))


    obj.data.materials.append(mat2)
    mat_ind = obj.data.materials.find("Undercut Material")
    print("Undercut material is %i" % mat_ind)

    for f in new_faces:
        obj.data.polygons[f.index].material_index = mat_ind

    if world:
        obj.matrix_world = mx

    bme.free()
    del bvh

    return


# segmentation only
def ensure_lookup(bme:BMesh):
    bme.verts.ensure_lookup_table()
    bme.edges.ensure_lookup_table()
    bme.faces.ensure_lookup_table()
