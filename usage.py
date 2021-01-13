import json
import os

from PySide import QtGui

from sept import PathTemplateParser, Token
from sept_qt import TemplateInputWidget, TemplatePreviewWidget, DocumentationWidget


def get_tokens():
    """
    Setting up Tokens you want to expose to the user.
    """
    class StatusToken(Token):
        """
        The <code>status</code> Token will return the "sg_status_list" value from the the Shotgun Version.
        """
        name = "status"
        def getValue(self, data):
            return data.get("sg_status_list")
    class LastNameToken(Token):
        """
        The <code>lastname</code> Token will return the "lastname" value of the Artist for the Version.
        """
        name = "lastname"
        def getValue(self, data):
            return data.get("user.HumanUser.lastname", "")
    class FirstNameToken(Token):
        """
        The <code>firstname</code> Token will return the "firstname" value of the Artist for the Version.
        """
        name = "firstname"
        def getValue(self, data):
            return data.get("user.HumanUser.firstname", "")
    class UserToken(Token):
        """
        The <code>user</code> Token will return the "name" value of the Artist for the Version.
        """
        name = "user"
        def getValue(self, data):
            return data.get("user.HumanUser.name", "")
    class ShotToken(Token):
        """
        The <code>shot</code> Token will return the "code" value of the Shot linked to the Version.
        """
        name = "shot"
        def getValue(self, data):
            return data.get("entity.Shot.code", "")
    class SequenceToken(Token):
        """
        The <code>shot</code> Token will return the "code" value of the Sequence linked to the Version.
        """
        name = "sequence"
        def getValue(self, data):
            value = data.get("entity.Sequence.code", "")
            if value:
                return value
            return data.get("entity.Shot.sg_sequence.Sequence.code", "")
    class ProjectToken(Token):
        """
        The <code>project</code> Token will return the "tank_name" value or the "code" value of the Project linked to the Version.
        """
        name = "project"
        def getValue(self, data):
            value = data.get("project.Project.tank_name", "")
            return value or data.get("project.Project.code", "") or ""
    class NameToken(Token):
        """
        The <code>name</code> Token will return the "code" value of the Version.
        """
        name = "name"
        def getValue(self, data):
            return data.get("code", "")
    class VersionToken(Token):
        """
        The <code>version</code> Token will return the "version_number" value of the PublishedFile linked to the Version.
        """
        name = "version"
        def getValue(self, data):
            published_files = data.get("published_files", [])
            version_number = None
            for published_file in published_files:
                if published_file.get("version_number"):
                    version_number = published_file.get("version_number")
                    break
            if version_number is None:
                return version_number
            return str(version_number)
    class ExtensionToken(Token):
        """
        The <code>extension</code> Token will return the path extension value of the PublishedFile linked to the Version.
        """
        name = "extension"
        def getValue(self, data):
            published_files = data.get("published_files", [])
            extension = None
            for published_file in published_files:
                if published_file.get("path"):
                    path = published_file.get("path")
                    if path.get("link_type") == "local":
                        local_path = path.get("local_path") or path.get("local_path_linux")
                    elif path.get("link_type") == "web":
                        local_path = path.get("url")[len("file://"):]
                    else:
                        return None
                    base, ext = os.path.splitext(local_path)
                    extension = ext.lstrip(".")
                    break
            return extension
    return [
        StatusToken,
        FirstNameToken,
        LastNameToken,
        NameToken,
        UserToken,
        ShotToken,
        SequenceToken,
        ProjectToken,
        VersionToken,
        ExtensionToken,
    ]


def live_version_data():
    # Setting up input data
    from shotgun_api3 import Shotgun
    sg = Shotgun("https://mysite.shotgunstudio.com", login="mylogin", password="mypassword")
    fields = [
        "code", "description",
        "user.HumanUser.firstname", "user.HumanUser.lastname",
        "user.HumanUser.name", "sg_status_list", "project.Project.tank_name",
        "project.Project.code",
        "entity.Shot.code", "entity.Shot.sg_sequence.Sequence.code",
        "entity.Sequence.code",
        "published_files",

    ]
    versions = sg.find(
        entity_type="Version",
        filters=[["project.Project.id", "is", 128]],
        fields=fields,
        limit=5
    )

    # Fill out published file data
    published_files_ids = []
    for version in versions:
        published_files = version.get("published_files")
        for published_file in published_files:
            if not published_file.get("version_number") or not published_file.get("path"):
                published_files_ids.append(published_file.get("id"))
    if published_files_ids:
        results = sg.find(
            entity_type="PublishedFile",
            filters=[["id", "in", published_files_ids]],
            fields=["version_number", "path"]
        )
        for result in results:
            for version in versions:
                published_files = version.get("published_files")
                for published_file in published_files:
                    if result.get("id") == published_file.get("id"):
                        published_file["version_number"] = result.get("version_number")
                        published_file["path"] = result.get("path")
    return versions


def get_version_data():
    with open(os.path.join(os.path.dirname(__file__), "usage_data.json"), "r") as fh:
        version_data = json.loads(fh.read())
    return version_data


class Dialog(QtGui.QDialog):
    def __init__(self):
        super(Dialog, self).__init__()
        self.parser = PathTemplateParser(additional_tokens=get_tokens())
        self.version_data = get_version_data()

        self._build_ui()

    def _build_ui(self):
        self.setLayout(QtGui.QVBoxLayout())

        self.splitter = QtGui.QSplitter()
        # self.splitter.setHandleWidth(70)

        self.main_page = QtGui.QWidget()
        self.main_page.setLayout(QtGui.QVBoxLayout())

        self.template_input_widget = TemplateInputWidget(self.parser)
        self.template_preview_widget = TemplatePreviewWidget(self.version_data)
        self.template_input_widget.template_changed.connect(self.template_preview_widget.preview_template)
        self.template_preview_widget.resolve_error.connect(self.template_input_widget.recieve_error)

        self.main_page.layout().addWidget(self.template_input_widget)
        self.main_page.layout().addWidget(self.template_preview_widget)

        self.documentation_widget = DocumentationWidget(self.parser, parent=self)

        self.splitter.addWidget(self.main_page)
        self.splitter.addWidget(self.documentation_widget)

        self.layout().addWidget(self.splitter)




if __name__ == "__main__":
    app = QtGui.QApplication([])

    QtGui.QApplication.setStyle("plastique")
    # QtGui.QApplication.setStyle("fusion")
    #
    # palette_file = r"D:\Users\Alex\Downloads\dark_palette.qpalette"
    # fh = QtCore.QFile(palette_file)
    # fh.open(QtCore.QIODevice.ReadOnly)
    # file_in = QtCore.QDataStream(fh)
    #
    # # deserialize the palette
    # # (store it for GC purposes)
    # _dark_palette = QtGui.QPalette()
    # file_in.__rshift__(_dark_palette)
    # fh.close()
    # QtGui.QApplication.setPalette(_dark_palette)
    #
    # css_file = r"D:\Users\Alex\Downloads\dark_palette.css"
    # f = open(css_file)
    # css_data = f.read()
    # f.close()
    # app.setStyleSheet(css_data)

    dialog = Dialog()
    dialog.show()

    app.exec_()
