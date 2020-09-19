# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import nuke

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class FrameOperation(HookBaseClass):
    """
    Hook called to perform a frame operation with the
    current scene
    """

    def get_editorial_data(self, **kwargs):
        """
        get_frame_range will return a tuple of (in_frame, out_frame)

        :returns: Returns the frame range in the form (in_frame, out_frame)
        :rtype: tuple[int, int]
        """
        current_in = int(nuke.root()["first_frame"].value())
        current_out = int(nuke.root()["last_frame"].value())
        current_frame_rate = float(nuke.root()["fps"].value())
        return (current_in, current_out, current_frame_rate)

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

        # unlock
        lock_range = self.parent.get_setting("lock_range")
        locked = nuke.root()["lock_range"].value()
        if locked:
            nuke.root()["lock_range"].setValue(False)
        # set values
        if in_frame and out_frame:
            nuke.root()["first_frame"].setValue(in_frame)
            nuke.root()["last_frame"].setValue(out_frame)
        if frame_rate:
            nuke.root()["fps"].setValue(frame_rate)
        # and lock again
        if locked or lock_range:
            nuke.root()["lock_range"].setValue(True)
