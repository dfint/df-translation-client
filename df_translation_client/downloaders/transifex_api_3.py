from typing import List, AsyncIterable

import httpx

from df_translation_client.downloaders.abstract_downloader import AbstractDownloader
from df_translation_client.downloaders.common import DownloadStage


class TransifexApiV3Downloader(AbstractDownloader):
    BASE_URL = "https://rest.api.transifex.com/"

    project_id: str

    def __init__(self, token: str, organization_slug: str, project_slug: str):
        self.token = token
        self.project_id = f"o:{organization_slug}:p:{project_slug}"

    async def connect(self) -> None:
        ...

    async def async_downloader(
        self,
        language: str,
        resources: List[str],
        file_path_pattern: str,
    ) -> AsyncIterable[DownloadStage]:
        # Create a translation file download action
        # https://transifex.github.io/openapi/index.html#tag/Resource-Translations/paths/~1resource_translations_async_downloads/post
        ...

    async def list_resources(self) -> List[str]:
        url = TransifexApiV3Downloader.BASE_URL + "resources"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"filter[project]": self.project_id},
                headers=dict(Authorization=f"Bearer {self.token}"),
            )
            response.raise_for_status()
            data = response.json()["data"]
            return [item["attributes"]["name"] for item in data]

    async def list_languages(self, resource_slug: str) -> List[str]:
        url = TransifexApiV3Downloader.BASE_URL + f"projects/{self.project_id}/languages"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=dict(Authorization=f"Bearer {self.token}"),
            )
            response.raise_for_status()
            data = response.json()["data"]
            return [item["attributes"]["id"].partition(":")[2] for item in data]
