# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
An app that syncs the frame range between a scene and a shot in Shotgun.

"""
import os
import traceback

from tank.platform import Application
from tank.platform.qt import QtGui
import tank


class SetEditData(Application):
    """
    tk-multi-setframerange is a Shotgun toolkit application that allows you to set and get the
        frame range and frame rate from shotgun regardless of your specific DCC application.

    Standard applications come implemented for you but you are able to implement support for
        custom engines through the provided hooks.
    """

    def init_app(self):
        """
        App entry point
        """
        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError(
                "Cannot load the Set Editorial Data application! "
                "Your current context does not have an entity (e.g. "
                "a current Shot, current Asset etc). This app requires "
                "an entity as part of the context in order to work."
            )

        # We grab the menu name from the settings so that the user is able to register multiple instances
        # of this app with different frame range fields configured.
        self.engine.register_command(self.get_setting("menu_name"), self.run_app)

        # Set a callback here to run on file open if the DCC supports it.
        self.open_file_callback = self.set_open_file_callback(self.update_callback)

    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return True

    def destroy_app(self):
        """
        App teardown
        """
        self.logger.debug("Destroying sg_set_editorial_data")

        # Unset the open_file_callback.
        self.unset_open_file_callback(self.update_callback, self.call)

    def run_app(self):
        """
        Callback from when the menu is clicked.

        The default callback will first query the frame range from shotgun and validate the data.
        If there is missing Shotgun data it will popup a QMessageBox dialog alerting the user.

        Assuming all data exists in shotgun, it will set the frame range with the newly
            queried data and popup a QMessageBox with results.

        """
        try:
            update_data = self._check_current_file()

            if update_data:
                self._update_dialog(*update_data)
            else:
                message = "Your workfile is up to date with the \n"
                message += "latest editorial data in Shotgun."
                QtGui.QMessageBox.information(None, "You're all good!", message)
                return

        except tank.TankError:
            message = "There was a problem updating your scene frame data.\n"
            QtGui.QMessageBox.warning(None, "Frame data not updated!", message)
            error_message = traceback.format_exc()
            self.logger.error(error_message)

    ###############################################################################################
    # implementation

    def get_editorial_data_from_shotgun(self):
        """
        get_editorial_data_from_shotgun will query shotgun for the
            'sg_in_frame_field', 'sg_out_frame_field', 'sg_frame_rate_field'
            setting values and return a tuple of (in, out, frame_rate).

        If the fields specified in the settings do not exist in your Shotgun site, this will raise
            a tank.TankError letting you know which field is missing.

        :returns: Tuple of (in, out, frame_rate)
        :rtype: tuple[int,int,float]
        :raises: tank.TankError
        """
        # we know that this exists now (checked in init)
        entity = self.context.entity
        project = self.context.project

        sg_entity_type = self.context.entity["type"]
        sg_filters = [["id", "is", entity["id"]]]

        sg_in_field = self.get_setting("sg_in_frame_field")
        sg_out_field = self.get_setting("sg_out_frame_field")
        sg_frame_rate_field = self.get_setting("sg_frame_rate_field")
        fields = [sg_in_field, sg_out_field, sg_frame_rate_field]

        data = self.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=fields)

        # check if fields exist!
        if sg_in_field not in data:
            raise tank.TankError(
                "Configuration error: Your current context is connected to a Shotgun "
                "%s. This entity type does not have a "
                "field %s.%s!" % (sg_entity_type, sg_entity_type, sg_in_field)
            )

        if sg_out_field not in data:
            raise tank.TankError(
                "Configuration error: Your current context is connected to a Shotgun "
                "%s. This entity type does not have a "
                "field %s.%s!" % (sg_entity_type, sg_entity_type, sg_out_field)
            )

        if not data.get(sg_frame_rate_field):
            proj_data = self.shotgun.find_one("Project", filters=[["id", "is", project["id"]]], fields=fields)
            if sg_frame_rate_field not in proj_data:
                data[sg_frame_rate_field] = None
            else:
                data[sg_frame_rate_field] = proj_data[sg_frame_rate_field]

        return (data[sg_in_field], data[sg_out_field], data[sg_frame_rate_field])

    def get_current_editorial_data(self):
        """
        get_current_frame_range will execute the hook specified in the 'hook_frame_operation'
            setting for this app.
        It will record the result of the hook and return the values as a tuple of (in, out, frame_rate).

        If there is an internal exception thrown from the hook, it will reraise the exception as
            a tank.TankError and write the traceback to the log.
        If the data returned is not in the correct format, tuple with two keys, it will
            also throw a tank.TankError exception.

        :returns: Tuple of (in, out, frame_rate) frame range values.
        :rtype: tuple[int,int,float]
        :raises: tank.TankError
        """
        try:
            result = self.execute_hook_method("hook_frame_operation", "get_editorial_data")
        except Exception as err:
            error_message = traceback.format_exc()
            self.logger.error(error_message)
            raise tank.TankError(
                "Encountered an error while getting the frame data: {}".format(
                    str(err)
                )
            )

        if not isinstance(result, tuple) or (
            isinstance(result, tuple) and len(result) != 3
        ):
            raise tank.TankError(
                "Unexpected type returned from 'hook_frame_operation' for operation get_"
                "frame_range - expected a 'tuple' with (in_frame, out_frame, frame_rate) values but "
                "returned '%s' : %s" % (type(result).__name__),
                result,
            )
        return result

    def set_editorial_data(self, in_frame, out_frame, frame_rate):
        """
        set_current_frame_range will execute the hook specified in the 'hook_frame_operation'
            setting for this app.
        It will pass the 'in_frame', 'out_frame', and 'frame_rate' to the hook.

        If there is an internal exception thrown from the hook, it will reraise the exception as
            a tank.TankError and write the traceback to the log.

        :param int in_frame: The value of in_frame that we want to set in the current session.
        :param int out_frame: The value of out_frame that we want to set in the current session.
        :param float frame_rate: The value of frame_rate that we want to set in the current session.
        :raises: tank.TankError
        """
        try:
            self.execute_hook_method(
                "hook_frame_operation",
                "set_editorial_data",
                in_frame=in_frame,
                out_frame=out_frame,
                frame_rate=frame_rate,
            )
        except Exception as err:
            error_message = traceback.format_exc()
            self.logger.error(error_message)
            raise tank.TankError(
                "Encountered an error while setting the frame data: {}".format(
                    str(err)
                )
            )

    def _check_current_file(self):

        shotgun_edit_data = self.get_editorial_data_from_shotgun()
        current_edit_data = self.get_current_editorial_data()

        # something might need updating, lets get into it
        if shotgun_edit_data != current_edit_data:

            update_range = True
            update_rate = True

            (new_in, new_out, new_rate) = shotgun_edit_data
            (current_in, current_out, current_rate) = current_edit_data

            # If the current range matches the new range or
            # either value in the new range is not set, we can skip
            if (new_in, new_out) == (current_in, current_out) or new_in is None or new_out is None:
                update_range = False

            # If the current_rate matches the new_rate or
            # the new_rate is not set, we dont need to set it
            if (new_rate == current_rate) or new_rate is None:
                update_rate = False

            if update_range or update_rate:
                return shotgun_edit_data, current_edit_data, update_range, update_rate
            else:
                return False

    def set_open_file_callback(self, func=None):
        """
        set_open_file_callback will execute the hook specified in the 'hook_frame_operation'
            setting for this app.
        It will set a callback on file open if the dcc supports it.

        If there is an internal exception thrown from the hook, it will reraise the exception as
            a tank.TankError and write the traceback to the log.
        If the data returned is not in the correct format, tuple with two keys, it will
            also throw a tank.TankError exception.

        :param func func: The function to set as the callback.
        :returns: whatever the callback function returns in case we need to unset the callback.
        :rtype: depends on the DCC
        :raises: tank.TankError
        """
        try:
            callback = self.execute_hook_method("hook_callbacks", "set_open_file_callback", func=func)
        except Exception as err:
            error_message = traceback.format_exc()
            self.logger.error(error_message)
            raise tank.TankError(
                "Encountered an error while setting open file callback: {}".format(
                    str(err)
                )
            )

        return callback

    def unset_open_file_callback(self, func, callback):
        """
        unset_open_file_callback will execute the hook specified in the 'hook_frame_operation'
            setting for this app.
        It will unset a callback on file open if the dcc supports it.

        If there is an internal exception thrown from the hook, it will reraise the exception as
            a tank.TankError and write the traceback to the log.
        If the data returned is not in the correct format, tuple with two keys, it will
            also throw a tank.TankError exception.

        :param func func: The function to unset as the callback.
        :param callback: whatever the set_open_file_callback returned should be set here in
            case the DCC needs it to unset the callback.
        :raises: tank.TankError
        """
        try:
            self.execute_hook_method("hook_callbacks", "unset_open_file_callback", func=func)
        except Exception as err:
            error_message = traceback.format_exc()
            self.logger.error(error_message)
            raise tank.TankError(
                "Encountered an error while setting open file callback: {}".format(
                    str(err)
                )
            )

    def _update_dialog(self, shotgun_edit_data, current_edit_data, update_range=True, update_rate=True):

        (new_in, new_out, new_rate) = shotgun_edit_data
        (current_in, current_out, current_rate) = current_edit_data

        if update_range or update_rate:

            message = "Your workfile has does not match \n"
            message += "the latest editorial data in Shotgun.\n\n"
            if update_range:
                message += "Current start frame: %s\n" % current_in
                message += "New start frame: %s\n\n" % new_in
                message += "Current end frame: %s\n" % current_out
                message += "New end frame: %s\n\n" % new_out
            if update_rate:
                message += "Current frame rate: %s\n" % current_rate
                message += "New frame rate: %s\n\n" % new_rate
            message += "Would you like to update your workfile with\n"
            message += "the latest editorial data?"

            flags = QtGui.QMessageBox.Yes
            flags |= QtGui.QMessageBox.No
            response = QtGui.QMessageBox.question(None, "Question",
                                                  message,
                                                  flags)
            if response == QtGui.QMessageBox.Yes:
                self.set_editorial_data(new_in, new_out, new_rate)

    def update_callback(self):
        try:
            update_data = self._check_current_file()

            if update_data:
                self._update_dialog(*update_data)

        except tank.TankError:
            error_message = traceback.format_exc()
            self.logger.error(error_message)
