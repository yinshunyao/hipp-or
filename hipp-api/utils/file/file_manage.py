# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2021/12/5 8:45
# @File           : file_manage.py
# @IDE            : PyCharm
# @desc           : 保存图片到本地

import asyncio
import io
import os
import zipfile
from pathlib import Path

import aiofiles
import aioshutil
from application.settings import STATIC_ROOT, BASE_DIR, STATIC_URL, STATIC_DIR
from fastapi import UploadFile
import sys
from core.exception import CustomException
from utils.file.file_base import FileBase


class FileManage(FileBase):
    """
    上传文件管理
    """

    def __init__(self, file: UploadFile, path: str):
        self.path = self.generate_static_file_path(path, file.filename)
        self.file = file

    async def save_image_local(self, accept: list = None) -> dict:
        """
        保存图片文件到本地
        :param accept:
        :return:
        """
        if accept is None:
            accept = self.IMAGE_ACCEPT
        await self.validate_file(self.file, max_size=5, mime_types=accept)
        return await self.async_save_local()

    async def save_audio_local(self, accept: list = None) -> dict:
        """
        保存音频文件到本地
        :param accept:
        :return:
        """
        if accept is None:
            accept = self.AUDIO_ACCEPT
        await self.validate_file(self.file, max_size=50, mime_types=accept)
        return await self.async_save_local()

    async def save_video_local(self, accept: list = None) -> dict:
        """
        保存视频文件到本地
        :param accept:
        :return:
        """
        if accept is None:
            accept = self.VIDEO_ACCEPT
        await self.validate_file(self.file, max_size=100, mime_types=accept)
        return await self.async_save_local()

    async def async_save_local(self) -> dict:
        """
        保存文件到本地
        :return: 示例：
        {
            'local_path': 'D:\\project\\hipp_dev\\hipp-api\\static\\system\\20240301\\1709303205HuYB3mrC.png',
            'remote_path': '/media/system/20240301/1709303205HuYB3mrC.png'
        }
        """
        path = Path(self.path)
        if sys.platform == "win32":
            path = Path(self.path.replace("/", "\\"))
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        content = await self.file.read()
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)
        return {
            "local_path": str(path),
            "remote_path": STATIC_URL + str(path).replace(STATIC_ROOT, '').replace("\\", '/')
        }

    @classmethod
    async def async_save_temp_file(cls, file: UploadFile) -> str:
        """
        保存临时文件
        :param file:
        :return:
        """
        temp_file_path = await cls.async_generate_temp_file_path(file.filename)
        async with aiofiles.open(temp_file_path, "wb") as f:
            await f.write(await file.read())
        return temp_file_path

    @classmethod
    async def unzip(cls, file: UploadFile, dir_path: str) -> str:
        """
        解压 zip 压缩包
        :param file:
        :param dir_path: 解压路径
        :return:
        """
        if file.content_type != "application/x-zip-compressed":
            raise CustomException("上传文件类型错误，必须是 zip 压缩包格式！")
        # 读取上传的文件内容
        contents = await file.read()
        # 将文件内容转换为字节流
        zip_stream = io.BytesIO(contents)
        # 使用zipfile库解压字节流
        with zipfile.ZipFile(zip_stream, "r") as zip_ref:
            zip_ref.extractall(dir_path)
        return dir_path

    @staticmethod
    async def async_copy_file(src: str, dst: str) -> None:
        """
        异步复制文件
        兼容绝对路径、本地相对路径与 /media/ 前缀路径
        :param src: 原始文件
        :param dst: 目标路径。绝对路径
        """
        src_path = Path(src)
        if not src_path.is_absolute():
            normalized = src.lstrip("/")
            if normalized.startswith(f"{STATIC_DIR}/"):
                src_path = Path(BASE_DIR) / normalized
            elif normalized.startswith(f"{STATIC_URL.lstrip('/')}/"):
                relative = normalized[len(STATIC_URL.lstrip("/")):].lstrip("/")
                src_path = Path(STATIC_ROOT) / relative
            else:
                src_path = Path(BASE_DIR) / normalized
        if not await asyncio.to_thread(src_path.exists):
            raise CustomException(f"{src_path} 源文件不存在！")
        dst = Path(dst)
        await asyncio.to_thread(dst.parent.mkdir, parents=True, exist_ok=True)
        await aioshutil.copyfile(src_path, dst)

    @staticmethod
    async def async_copy_dir(src: str, dst: str, dirs_exist_ok: bool = True) -> None:
        """
        复制目录
        :param src: 源目录
        :param dst: 目标目录
        :param dirs_exist_ok: 是否覆盖
        """
        if not os.path.exists(dst):
            raise CustomException("目标目录不存在！")
        await aioshutil.copytree(src, dst, dirs_exist_ok=dirs_exist_ok)
