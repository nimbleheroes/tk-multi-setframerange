# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import MaxPlus

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
        ticks = MaxPlus.Core.EvalMAXScript("ticksperframe").GetInt()
        current_in = MaxPlus.Animation.GetAnimRange().Start() / ticks
        current_out = MaxPlus.Animation.GetAnimRange().End() / ticks
        current_fps = None  # TODO: get frame rate for 3dsmax
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

        ticks = MaxPlus.Core.EvalMAXScript("ticksperframe").GetInt()
        range = MaxPlus.Interval(in_frame * ticks, out_frame * ticks)
        MaxPlus.Animation.SetRange(range)
