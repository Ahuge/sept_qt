from PySide import QtGui, QtWebKit


class DocumentationWidget(QtGui.QTabWidget):
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
        :param QtGui.QWidget|None parent: Optional Qt parent widget.
        """
        super(DocumentationWidget, self).__init__(parent)

        self.parser = parser
        self._token_webview = QtWebKit.QWebView()
        self._operator_webview = QtWebKit.QWebView()

        self.addTab(self._token_webview, "Tokens")
        self.addTab(self._operator_webview, "Operators")

    def refreshDocumentation(self):
        """
        refreshDocumentation will query the parser again for any updated
            documentation for either Tokens or Operators and then update the
            corresponding web views.

        """
        token_html = self.parser.token_documentation()
        self._token_webview.setHtml(token_html)

        operator_html = self.parser.operator_documentation()
        self._operator_webview.setHtml(operator_html)

    def showEvent(self, event):
        self.refreshDocumentation()
        return super(DocumentationWidget, self).showEvent(event)
