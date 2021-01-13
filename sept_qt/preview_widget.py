from sept import errors

from PySide import QtGui, QtCore


class TemplatePreviewWidget(QtGui.QPlainTextEdit):
    resolve_error = QtCore.Signal(object)

    def __init__(self, parser, data_list, text=None, parent=None):
        super(TemplatePreviewWidget, self).__init__(text, parent)
        self.setReadOnly(True)
        self.parser = parser
        self._data_objects = data_list
        self.setEnabled(False)

    @property
    def data_objects(self):
        return self._data_objects

    @data_objects.setter
    def data_objects(self, value):
        """
        List of data dictionaries used to preview data from.

        :param list[dict] value: The data dictionaries
        :return:
        """
        if isinstance(value, dict):
            value = [value]

        self._data_objects = value

    @QtCore.Slot(object)
    def preview_template(self, template):
        """
        preview_template takes a sept.Template object and will attempt
            to resolve the output path for each `data_object` in
            `TemplatePreviewWidget.data_objects`.

        If it encounters an error, it will emit the `resolve_error` signal.
        If the template resolves for all `data_object` dictionaries, it will
            update the text field.

        :param sept.Template template: Template to resolve for each data_object
        """
        _previews = []
        for data_object in self.data_objects:
            try:
                output_data = template.resolve(data_object)
            except errors.ParsingError as err:
                self.resolve_error.emit(err)
                return
            _previews.append(output_data)

        text = "\n".join(_previews)
        self.setPlainText(text)
