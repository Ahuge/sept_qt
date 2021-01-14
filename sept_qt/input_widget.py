from sept import errors

from PySide import QtGui, QtCore


class TemplateInputWidget(QtGui.QWidget):
    """
    TemplateInputWidget can be used to interactively create `sept.Template`
        objects and check their validity.

    All that TemplateInputWidget needs is a valid `sept.PathTemplateParser`
        instance, however for styling in your GUI application, you can
        optionally pass an `error_colour` that will drive the highlighting
        colour when errors occur.

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

    ERROR_BG_COLOUR = QtGui.QColor(255, 192, 192)
    template_changed = QtCore.Signal(object)
    _TIMER_TIMEOUT = 1250

    def __init__(self, parser, error_colour=None, timeout=None, parent=None):
        """
        TemplateInputWidget is instantiated with a `sept.PathTemplateParser`
            instance and optionally a QColor and/or integer for highlighting
            colour and error timeouts respectively.

        The `error_colour` defaults to rgb(255, 192, 192) which is a pale red.
        The `timeout` default to 1250ms, you should be careful when lowering
            this value because it is incredibly jolting to be typing the your
            Sept Template Expression and have highlighting and errors start
            popping up.

        :param sept.PathTemplateParser parser: Parser object driving the
            template generation.
        :param QtGui.QColor|None error_colour: Optional colour override for
            the error highlighting.
        :param int|None timeout: Optional timeout in ms that will be waited
            before displaying an error.
        :param QtGui.QWidget|None parent: Optional Qt parent widget.
        """
        super(TemplateInputWidget, self).__init__(parent)
        self.parser = parser
        self.error_colour = error_colour or self.ERROR_BG_COLOUR
        self.template = None
        self._error_timeout = timeout or self._TIMER_TIMEOUT
        self._error_timer = QtCore.QTimer(self)
        self._line_widget = None
        self._error_widget = None
        self._has_error = False
        self._build_ui()

    def _build_ui(self):
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self._line_widget = QtGui.QTextEdit(self)
        self._line_widget.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self._line_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._line_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._line_widget.setFixedHeight(23)
        self._line_widget.setMinimumWidth(365)
        self._line_widget.setSizePolicy(
            QtGui.QSizePolicy.Policy.Expanding,
            QtGui.QSizePolicy.Policy.Fixed,
        )

        self._error_widget = QtGui.QLabel(self)
        self._error_widget.setWordWrap(True)
        self._error_widget.hide()

        self.layout().addWidget(self._line_widget)
        self.layout().addWidget(self._error_widget)

        self._line_widget.textChanged.connect(self._handle_text_edited)

    def _stop_error_timer(self):
        """
        _stop_error_timer is an internal helper to cancel any queued errors
            waiting to be displayed.
        """
        if self._error_timer and self._error_timer.isActive():
            self._error_timer.stop()
            self._error_timer = QtCore.QTimer(self)

    def _hide_error(self):
        """
        _hide_error is an internal handler that will stop any queued errors on
            the timer, reset the text formatting and hide the error label.
        """
        self._stop_error_timer()
        if self._has_error:
            cursor = self._line_widget.textCursor()
            position = cursor.position()
            self._line_widget.textChanged.disconnect(self._handle_text_edited)
            self._line_widget.setHtml(self._line_widget.toPlainText())
            self._line_widget.textChanged.connect(self._handle_text_edited)
            self._has_error = False
            cursor.setPosition(position)
            self._line_widget.setTextCursor(cursor)
        self._error_widget.hide()
        self._error_widget.setText("")

    def _display_error_factory(self, error):
        """
        _display_error_factory returns a wrapped python function that will
            display the `error` when called.

        Displaying the `error` consists of a few steps, first off we attempt
            to find the `location` and `length` of the error that needs to be
            highlighted.
        If `location` or `length` are not found on the error class, the start
            or end of the template string will be used instead.

        After generating the highlighted range it will wrap that text in a
            bold html tag with a background colour set to
            `TemplateInputWidget.error_colour` and updates the text box.

        The message from the passed error gets displayed in a hidden error
            label and then stops any queued errors on the timer.

        :param Exception error: Python Exception instance to be displayed.
        :return: A python function with the `error` wrapped.
        :rtype: callable
        """

        def __display_error():
            text = self._line_widget.toPlainText()
            cursor = self._line_widget.textCursor()
            position = cursor.position()

            start = 0
            if isinstance(error, errors.LocationAwareSeptError) or hasattr(
                error, "location"
            ):
                start = error.location

            length = len(text) - start
            if isinstance(error, errors.LocationAwareSeptError) or hasattr(
                error, "length"
            ):
                length = error.length + 1

            before, target, after = (
                text[:start],
                text[start : start + length - 1],
                text[start + length - 1 :],
            )
            colour_start = (
                '<b style="background-color:rgb({red},{green},{blue});">'.format(
                    red=self.error_colour.red(),
                    green=self.error_colour.green(),
                    blue=self.error_colour.blue(),
                )
            )
            resulting_string = before + colour_start + target + "</b>" + after
            self._line_widget.textChanged.disconnect(self._handle_text_edited)
            self._line_widget.setHtml(resulting_string)
            self._line_widget.textChanged.connect(self._handle_text_edited)
            self._has_error = True
            cursor.setPosition(position)
            self._line_widget.setTextCursor(cursor)

            self._error_widget.setText(str(error))
            self._error_widget.show()
            self._stop_error_timer()

        return __display_error

    @QtCore.Slot(object)
    def recieve_error(self, error):
        """
        recieve_error will take an Exception class and attempt to highlight
            and display it.

        Take care when sending non SeptError classes because this class is
            ideally looking for `location` and `length` attributes on the
            passed error instance.

        If you don't have the required attributes, your highlighting will
            cover the entire text.

        :param Exception error: Python Exception instance to be displayed.
        """
        self._display_error_factory(error)()

    @QtCore.Slot()
    def _handle_text_edited(self):
        """
        _handle_text_edited is an internal handler that deals with validating
            the template string and queueing up errors if needed.

        If the template string typed in creates a valid `sept.Template`
            object, it will emit the `template_changed` signal passing the
            newly created Template as the only value.
        """
        text = self._line_widget.toPlainText()
        try:
            template = self.parser.validate_template(text)
        except errors.MultipleBalancingError as errs:
            self._stop_error_timer()
            for error in errs.errors:
                self._error_timer.timeout.connect(self._display_error_factory(error))
                self._error_timer.start(self._error_timeout)
            return
        except errors.OperatorNotFoundError as err:
            self._stop_error_timer()
            self._error_timer.timeout.connect(self._display_error_factory(err))
            self._error_timer.start(self._error_timeout)
            return
        except Exception as err:
            print("Error: {}".format(str(err)))
            import traceback

            traceback.print_exc()
            return
        else:
            self._hide_error()

        self.template = template
        self.template_changed.emit(template)
