# -*- coding: utf-8 -*-
"""数据导入导出：表清单与 manifest 校验（不连真实库）。"""
import io
import zipfile

import pytest

from apps.vadmin.system.data_migration import TABLES_ORDER, _read_manifest
from core.exception import CustomException


def test_tables_order_unique_and_nonempty():
    assert len(TABLES_ORDER) >= 1
    assert len(TABLES_ORDER) == len(set(TABLES_ORDER))


def test_read_manifest_requires_manifest_json():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("data/vadmin_auth_dept.json", "[]")
    buf.seek(0)
    with zipfile.ZipFile(buf, "r") as zf:
        with pytest.raises(CustomException) as ei:
            _read_manifest(zf)
    assert "manifest" in ei.value.msg
