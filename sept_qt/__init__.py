from .documentation_widget import DocumentationWidget
from .input_widget import TemplateInputWidget
from .preview_widget import TemplatePreviewWidget

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
