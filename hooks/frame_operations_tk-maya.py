# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import maya.cmds as cmds
import pymel.core as pm

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

_maya_valid_fps = [2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20, 23.976, 24, 25, 29.97, 30, 40, 47.952, 48, 50, 59.94, 60, 75,
                   80, 100, 120, 125, 150, 200, 240, 250, 300, 375, 400, 500, 600, 750, 1200, 1500, 2000, 3000, 6000, 44100, 48000]


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
        current_in = int(cmds.playbackOptions(query=True, minTime=True))
        current_out = int(cmds.playbackOptions(query=True, maxTime=True))
        current_frame_rate = self.closest_match(_maya_valid_fps, pm.mel.currentTimeUnitToFPS())
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

        # set frame rate for plackback
        if frame_rate:
            # setting these prefs ensures that keys stay on thier frames
            cmds.optionVar(iv=('keepKeysAtCurrentFrame', 1))
            cmds.optionVar(iv=('roundRangesToWholeValue', 0))

            # maya only supports a set list of frame rates so lets find the closest one to ours
            maya_frame_rate = self.closest_match(_maya_valid_fps, frame_rate)

            # and finally set the frame rate
            cmds.currentUnit(t="{}fps".format(maya_frame_rate))

        # set frame data for plackback
        cmds.playbackOptions(
            minTime=in_frame,
            maxTime=out_frame,
            animationStartTime=in_frame,
            animationEndTime=out_frame,
        )

        # set frame ranges for rendering
        cmds.setAttr("defaultRenderGlobals.startFrame", in_frame)
        cmds.setAttr("defaultRenderGlobals.endFrame", out_frame)

    def closest_match(self, lst, val):
        return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - val))]
