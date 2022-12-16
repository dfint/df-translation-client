import io
import traceback
from typing import AsyncIterable, List, Mapping

import httpx

from df_translation_client.downloaders.abstract_downloader import AbstractDownloader
from df_translation_client.downloaders.common import DownloadStage, StatusEnum


class GithubDownloader(AbstractDownloader):
    BASE_URL = "https://raw.githubusercontent.com/dfint/translations-backup/main/"

    metadata: Mapping[str, Mapping[str, Mapping[str, str]]]
    projects: List[str]

    async def connect(self) -> None:
        url = GithubDownloader.BASE_URL + "metadata-v2.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            self.metadata = response.json()
            self.projects = list(self.metadata)

    async def async_downloader(
        self,
        language: str,
        resources: List[str],
        file_path_pattern: str,
    ) -> AsyncIterable[DownloadStage]:
        async with httpx.AsyncClient() as client:
            for resource in resources:
                yield DownloadStage(resource, StatusEnum.DOWNLOADING, None)
                file_name = self.metadata[resource][language]
                url = GithubDownloader.BASE_URL + "translations/" + file_name
                try:
                    async with client.stream("GET", url) as response:
                        response.raise_for_status()
                        file_name = file_path_pattern.format(resource=resource, language=language)
                        with open(file_name, "wb") as file:
                            async for chunk in response.aiter_bytes(io.DEFAULT_BUFFER_SIZE):
                                file.write(chunk)
                except Exception:
                    yield DownloadStage(resource, StatusEnum.FAILED, traceback.format_exc())
                else:
                    yield DownloadStage(resource, StatusEnum.OK, None)

    async def list_projects(self) -> List[str]:
        return list(self.projects)

    async def list_resources(self, project: str) -> List[str]:
        return list(self.metadata[project])

    async def list_languages(self, project: str, resource_slug: str) -> List[str]:
        return list(self.metadata[project][resource_slug])
