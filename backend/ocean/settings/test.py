import tempfile
from pathlib import Path

from ocean.settings import TEST
from ocean.settings.dev import *  # noqa: F403

ENV = TEST
MEDIA_ROOT = Path(tempfile.gettempdir())


API_DOMAIN_PREFIX = "http://test.example.com"
