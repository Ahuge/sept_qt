from sept import errors

from PySide import QtGui, QtCore


class TemplatePreviewWidget(QtGui.QPlainTextEdit):
    """
    TemplatePreviewWidget is a QPlainTextEdit designed to help visualize what
        a specific template would output given certain situations.

    It will attempt to resolve the `sept.Template` object for each example
        case passed in to it's `data_list` parameter.
    If any of these error out, the `resolve_error` signal will emit the error
        and stop resolving.

    Assuming all of the example cases resolve correctly, the QPlainTextEdit
        will update the preview text.
    """

    resolve_error = QtCore.Signal(object)

    def __init__(self, data_list, text=None, parent=None):
        """
        TemplatePreviewWidget takes a list of data dictionaries for resolving
            a template.

        These data dictionaries (`data_list`) are intended to be an example
            subset of your entire dataset.
        We recommend passing no more than 10ish to ensure better performance
            in your GUI application, however that said, you're an adult and
            can pass as many as you'd like.

        When you are ready to generate previews for a `sept.Template` object,
            you can pass the template to the `preview_template` method to get
            your results.

        You should subscribe to the `resolve_error` signal so that you can
            handle errors in resolving.
        When used with the `sept_qt.TemplateInputWidget` class, you can
            connect directly to the `recieve_error` slot.

        :param list[dict] data_list: A list of dictionaries used to resolve a
            `sept.Template` in different scenarios.
        :param str text: Default text for the QPlainTextEdit.
        :param QtGui.QWidget|None parent: Optional Qt parent widget.
        """
        super(TemplatePreviewWidget, self).__init__(text, parent)
        self.setReadOnly(True)
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
