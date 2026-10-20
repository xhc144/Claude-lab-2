import os
import sys
import tempfile

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["FOLIO_NO_UPDATE"] = "1"  # 测试时不联网检查更新
# 测试时把设置写到临时目录，避免污染真实配置
_cfg = tempfile.mkdtemp(prefix="folio-test-cfg-")
os.environ["XDG_CONFIG_HOME"] = _cfg
os.environ["XDG_DATA_HOME"] = _cfg
os.environ["APPDATA"] = _cfg
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from folio.theme import theme

    theme.apply(app, "light")
    yield app
