import asyncio
import io
import traceback
from pathlib import PurePosixPath
from typing import AsyncIterable, List, Mapping

import aiohttp

from df_translation_client.downloaders.abstract_downloader import AbstractDownloader
from df_translation_client.downloaders.common import DownloadStage, StatusEnum


class GithubDownloader(AbstractDownloader):
    metadata: Mapping[str, Mapping[str, str]]
    resources: List[str]

    BASE_URL = PurePosixPath("https://raw.githubusercontent.com/dfint/translations-backup/main/")

    def __init__(self):
        pass

    async def connect(self) -> None:
        url = str(GithubDownloader.BASE_URL / "files_by_resource.json")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                self.metadata = await response.json()
                self.resources = list(self.metadata)

    async def async_downloader(self, language: str, resources: List[str], file_path_pattern: str) \
            -> AsyncIterable[DownloadStage]:
        async with aiohttp.ClientSession() as session:
            for resource in resources:
                yield DownloadStage(resource, StatusEnum.DOWNLOADING, None)
                url = str(GithubDownloader.BASE_URL / "translation" / self.metadata[resource][language])
                try:
                    async with session.get(url) as response:
                        file_name = file_path_pattern.format(resource=resource, language=language)
                        with open(file_name, "wb") as file:
                            while True:
                                block = await response.content.read(io.DEFAULT_BUFFER_SIZE)
                                if not block:
                                    break
                                file.write(block)
                                await asyncio.sleep(.05)  # let other parts of the program work
                except Exception:
                    yield DownloadStage(resource, StatusEnum.FAILED, traceback.format_exc())
                else:
                    yield DownloadStage(resource, StatusEnum.OK, None)

    async def list_resources(self) -> List[str]:
        return self.resources

    async def list_languages(self, resource_slug: str = None) -> List[str]:
        if resource_slug is None:
            resource_slug = self.resources[0]
        return list(self.metadata[resource_slug])
