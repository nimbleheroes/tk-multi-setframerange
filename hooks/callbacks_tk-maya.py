from maya import OpenMaya

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class FrameDataCallbacks(HookBaseClass):
    """
    Hook called to set and unset callbacks in the DCC
    """

    def set_open_file_callback(self, func=None):
        """
        set_open_file_callback will set a callback function for
            when a file is opened
        """
        if func:
            OpenMaya.MEventMessage.addEventCallback("PostSceneRead", func)

    def unset_open_file_callback(self, func=None, callback=None):
        """
        unset_open_file_callback will remove a callback function for
            when a file is opened
        """
        if callback:
            OpenMaya.MEventMessage.removeCallback(callback)
