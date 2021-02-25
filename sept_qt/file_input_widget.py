import os

from Qt import QtGui, QtWidgets, QtCore

from sept import errors

from .input_widget import TemplateInputWidget


class FileTemplateInputWidget(TemplateInputWidget):
    """
    FileTemplateInputWidget extends the TemplateInputWidget in allowing users
        to interactively create `sept.Template` objects by allowing you to
        load and save your template strings to disk.

    All that TemplateInputWidget needs is a valid `sept.PathTemplateParser`
        instance, however for styling in your GUI application, you can
        optionally pass an `error_colour` that will drive the highlighting
        colour when errors occur.

    *Automatically Load From Disk*
    You may want to automatically populate your FileTemplateInputWidget with
        data that persists on disk.
    This can be done by passing the path to your serialized `sept.Template`
        file into the `disk_path` parameter.

    *Interactivity Timeouts*
    You may also wish to define how long the timeout occurs between the last
        character input and our error highlighting occurs.
    By default this is set at 1250ms but you can override this by passing a
        value to `timeout` during instantiation.

    *Error handling*
    When using this in a larger GUI application, you may want to have a
        centralized place for displaying errors, if that is the case, you can
        send errors to the `recieve_error` slot.
    However, to ensure it visualizes correctly, you will want to ensure your
        error class has "location" and "length" attributes on it that can be
        used to display the highlighting.
    """

    LOAD_TEXT = "Load SEPT template"
    SAVE_TEXT = "Save SEPT template"

    def __init__(
        self, parser, error_colour=None, timeout=None, disk_path=None, parent=None
    ):
        super(FileTemplateInputWidget, self).__init__(
            parser=parser, error_colour=error_colour, timeout=timeout, parent=parent
        )
        self._load_from_disk_button = None
        self._save_to_disk_button = None
        self._disk_path = disk_path

        if disk_path and os.path.exists(disk_path):
            self.load_path(disk_path)

    def load_path(self, path):
        """
        load_path will attempt to read and validate your `sept.Template` from
            the filepath passed in.
        If you errors occur while validating, a popup will handle any exceptions
            from validating the template.

        :param str path: Path to a file on disk containing the template_str.
        """
        try:
            template_str = self._read_from_path(path)
        except errors.SeptError as err:
            import traceback

            message = (
                "Error loading template data from {path}\n"
                "Error was: {error}\n"
                "{long_error}".format(
                    path=path, error=str(err), long_error=traceback.format_exc()
                )
            )
            self._display_error(
                message=message, title="Error loading template data from disk!"
            )
            return
        else:  # No errors
            self.setText(template_str)

    def _build_input_widget(self):
        widget = QtWidgets.QWidget(self)
        widget.setLayout(QtWidgets.QHBoxLayout())
        widget.layout().setSpacing(0)
        widget.layout().setContentsMargins(0, 0, 0, 0)

        line_edit_widget = super(FileTemplateInputWidget, self)._build_input_widget()
        self._load_from_disk_button = QtWidgets.QPushButton("...")
        self._load_from_disk_button.setMaximumWidth(24)
        self._load_from_disk_button.clicked.connect(
            self._handle_load_disk_button_clicked
        )
        self._save_to_disk_button = QtWidgets.QPushButton("Save...")
        self._save_to_disk_button.setMaximumWidth(56)
        self._save_to_disk_button.clicked.connect(self._handle_save_disk_button_clicked)

        widget.layout().addWidget(line_edit_widget)
        widget.layout().addWidget(self._load_from_disk_button)
        widget.layout().addWidget(self._save_to_disk_button)
        return widget

    def _display_error(self, message, title="Error!"):
        QtWidgets.QMessageBox.critical(self, title, message)

    def _display_information(self, message, title="Information!"):
        QtWidgets.QMessageBox.information(self, title, message)

    def _read_from_path(self, path):
        if not os.path.exists(path):
            return
        with open(path, "r") as fh:
            data = fh.read()
        try:
            self.parser.validate_template(data)
        except errors.SeptError:
            raise
        return data

    def _get_folder_path(self):
        path = os.getcwd()
        if self._disk_path is None:
            return path
        elif os.path.isfile(self._disk_path):
            if os.path.exists(self._disk_path):
                path = self._disk_path
            elif os.path.exists(os.path.dirname(self._disk_path)):
                path = os.path.dirname(self._disk_path)

        elif os.path.isdir(self._disk_path):
            if os.path.exists(self._disk_path):
                path = self._disk_path
        return path

    @QtCore.Slot()
    def _handle_save_disk_button_clicked(self):
        if not self.template:
            self._display_information(
                message="Input text box does not contain a valid template. Please fix any errors or type one.",
                title="No valid template",
            )
            return
        path = self._get_folder_path()
        new_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, self.SAVE_TEXT, path)
        with open(new_path, "w") as fh:
            fh.write(self.template._template_str)
        self._display_information(
            message="Template saved successfully to {}".format(new_path),
            title="Success!",
        )

    @QtCore.Slot()
    def _handle_load_disk_button_clicked(self):
        path = self._get_folder_path()

        new_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, self.LOAD_TEXT, path)
        self._disk_path = new_path
        self.load_path(self._disk_path)
