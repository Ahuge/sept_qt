from Qt import QtGui, QtWidgets
import Qt

if Qt.__binding__ == "PySide2":
    try:
        from PySide2 import QtWebEngineWidgets

        QWebView = QtWebEngineWidgets.QWebEngineView
    except ImportError:
        from PySide2 import QtWebkitWidgets

        QWebView = QtWebkitWidgets.QWebView

elif Qt.__binding__ == "PySide":
    from PySide import QtWebKit

    QWebView = QtWebKit.QWebView


class DocumentationWidget(QtWidgets.QTabWidget):
    """
    DocumentationWidget is designed to give a fast and easy way to display the
        Token and Operator documentation to your users.

    **Warning** This takes the html text from the sept.Operator and sept.Token
        docstrings and directly loads it into a QWebView.
    This is a known security risk if you are loading Tokens or Operators
        from an untrusted source.
    """

    def __init__(self, parser, parent=None):
        """
        DocumentationWidget only requires a `sept.PathTemplateParser` object
            to operate.

        This should be a fully instantiated Parser object that we can generate
            documentation from.

        :param sept.PathTemplateParser parser: Parser object driving the docs.
        :param QtWidgets.QWidget|None parent: Optional Qt parent widget.
        """
        super(DocumentationWidget, self).__init__(parent)

        self.parser = parser
        self._token_webview = QWebView()
        self._operator_webview = QWebView()

        self.addTab(self._token_webview, "Tokens")
        self.addTab(self._operator_webview, "Operators")

    def html_prefix(self):
        return (
            "<head><style>body {"
            "background-color: "
            + self._get_background_colour()
            + "color: "
            + self._get_foreground_colour()
            + "}</style></head>"
        )

    def _get_background_colour(self):
        bg_colour = self.palette().color(QtGui.QPalette.Base)
        r, g, b = bg_colour.red(), bg_colour.green(), bg_colour.blue()
        return "rgb({r}, {g}, {b});".format(r=r, g=g, b=b)

    def _get_foreground_colour(self):
        fg_colour = self.palette().color(QtGui.QPalette.Text)
        r, g, b = fg_colour.red(), fg_colour.green(), fg_colour.blue()
        return "rgb({r}, {g}, {b});".format(r=r, g=g, b=b)

    def refreshDocumentation(self):
        """
        refreshDocumentation will query the parser again for any updated
            documentation for either Tokens or Operators and then update the
            corresponding web views.

        """
        token_html = self.parser.token_documentation()
        self._token_webview.setHtml(self.html_prefix() + token_html)

        operator_html = self.parser.operator_documentation()
        self._operator_webview.setHtml(self.html_prefix() + operator_html)

    def showEvent(self, event):
        self.refreshDocumentation()
        return super(DocumentationWidget, self).showEvent(event)
