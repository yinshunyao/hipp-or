# -*- coding: utf-8 -*-
import asyncio
import io

import pytest
from starlette.datastructures import Headers, UploadFile

from core.exception import CustomException
from utils.file.file_base import FileBase


def test_validate_file_accepts_ico_vnd_microsoft_icon():
    body = io.BytesIO(b"x")
    uf = UploadFile(
        file=body,
        filename="favicon.ico",
        headers=Headers({"content-type": "image/vnd.microsoft.icon"}),
    )
    asyncio.run(FileBase.validate_file(uf, mime_types=FileBase.IMAGE_ACCEPT))


def test_validate_file_accepts_ico_case_insensitive_mime():
    body = io.BytesIO(b"x")
    uf = UploadFile(
        file=body,
        filename="favicon.ico",
        headers=Headers({"content-type": "Image/X-Icon"}),
    )
    asyncio.run(FileBase.validate_file(uf, mime_types=FileBase.IMAGE_ACCEPT))


def test_validate_file_accepts_ico_octet_stream_with_ico_name():
    body = io.BytesIO(b"x")
    uf = UploadFile(
        file=body,
        filename="site.ICO",
        headers=Headers({"content-type": "application/octet-stream"}),
    )
    asyncio.run(FileBase.validate_file(uf, mime_types=FileBase.IMAGE_ACCEPT))


def test_validate_file_rejects_octet_stream_non_ico():
    body = io.BytesIO(b"x")
    uf = UploadFile(
        file=body,
        filename="logo.png",
        headers=Headers({"content-type": "application/octet-stream"}),
    )
    with pytest.raises(CustomException, match="上传文件格式错误"):
        asyncio.run(FileBase.validate_file(uf, mime_types=FileBase.IMAGE_ACCEPT))
