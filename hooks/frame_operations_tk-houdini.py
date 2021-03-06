# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import hou

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class FrameOperation(HookBaseClass):
    """
    Hook called to perform a frame operation with the
    current scene
    """

    def get_editorial_data(self, **kwargs):
        """
        get_editorial_data will return a tuple of (in_frame, out_frame, frame_range)

        :returns: Returns the frame data in the form (in_frame, out_frame, frame_range)
        :rtype: tuple[int, int, float]
        """
        current_in, current_out = hou.playbar.playbackRange()
        current_fps = None  # TODO: get frame rate for houdini
        return (current_in, current_out, current_fps)

    def set_editorial_data(self, in_frame=None, out_frame=None, frame_rate=None, **kwargs):
        """
        set_editorial_data will set the frame range using `in_frame` and `out_frame`
        and the frame rate using `frame_rate`

        :param int in_frame: in_frame for the current context
            (e.g. the current shot, current asset etc)

        :param int out_frame: out_frame for the current context
            (e.g. the current shot, current asset etc)

        :param float frame_rate: frame_range for the current context
            (e.g. the current shot, current asset, or current project)

        """

        # We have to use hscript until SideFX gets around to implementing hou.setGlobalFrameRange()
        hou.hscript("tset `((%s-1)/$FPS)` `(%s/$FPS)`" % (in_frame, out_frame))
        hou.playbar.setPlaybackRange(in_frame, out_frame)
