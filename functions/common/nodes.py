# Author: Christopher Gearhart

# System imports
# NONE!

# Blender imports
import bpy

# Module imports
# NONE!


def get_socket_index(socket):
    """Index of socket"""
    if hasattr(socket, "index"):
        return socket.index
    else:
        node = socket.node
        sockets = node.outputs if socket.is_output else node.inputs
        for i, s in enumerate(sockets):
            if s == socket:
                return i


def get_other_socket(socket):
    """
    Get next real upstream socket.
    This should be expanded to support wifi nodes also.
    Will return None if there isn't a another socket connect
    so no need to check socket.links
    """
    if not socket.is_linked:
        return None
    if not socket.is_output:
        other = socket.links[0].from_socket
    else:
        other = socket.links[0].to_socket

    if other.node.bl_idname == "NodeReroute":
        if not socket.is_output:
            return get_other_socket(other.node.inputs[0])
        else:
            return get_other_socket(other.node.outputs[0])
    else:  #other.node.bl_idname == "WifiInputNode":
        return other


def replace_socket(socket, new_type, new_name=None, new_pos=None):
    """
    Replace a socket with a socket of new_type and keep links
    """

    socket_name = new_name or socket.name
    ng = socket.id_data

    # ng.freeze()

    if socket.is_output:
        outputs = socket.node.outputs
        to_sockets = [l.to_socket for l in socket.links]
        socket_pos = new_pos or get_socket_index(socket)

        outputs.remove(socket)
        new_socket = outputs.new(new_type, socket_name)
        outputs.move(len(outputs)-1, socket_pos)

        for to_socket in to_sockets:
            ng.links.new(new_socket, to_socket)

    else:
        inputs = socket.node.inputs
        from_socket = socket.links[0].from_socket if socket.is_linked else None
        socket_pos = new_pos or get_socket_index(socket)

        inputs.remove(socket)
        new_socket = inputs.new(new_type, socket_name)
        inputs.move(len(inputs)-1, socket_pos)

        if from_socket:
            ng.links.new(from_socket, new_socket)

    # ng.unfreeze()

    return new_socket
