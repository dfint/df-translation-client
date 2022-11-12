import asyncio
import traceback
from typing import AsyncIterable, List

from transifex.api import TransifexAPI

from df_translation_client.downloaders.abstract_downloader import AbstractDownloader
from df_translation_client.downloaders.common import StatusEnum, DownloadStage

try:
    from asyncio import to_thread  # added in Python 3.9
except ImportError:

    async def to_thread(func, *args):
        return await asyncio.get_running_loop().run_in_executor(None, func, *args)


class TransifexApiDownloader(AbstractDownloader):
    transifex_api: TransifexAPI
    project_slug: str

    def __init__(self, username: str, password: str, project_slug: str):
        self.transifex_api = TransifexAPI(username, password, "https://www.transifex.com")
        self.project_slug = project_slug

    async def connect(self):
        assert await to_thread(self.transifex_api.ping), "No connection to the server"
        assert await to_thread(
            self.transifex_api.project_exists, self.project_slug
        ), f"Project {self.project_slug} does not exist"

    async def async_downloader(
        self,
        language: str,
        resources: List[str],
        file_path_pattern: str,
    ) -> AsyncIterable[DownloadStage]:
        for resource in resources:
            yield DownloadStage(resource, StatusEnum.DOWNLOADING, None)
            exception_info = None
            for j in range(10, 0, -1):
                try:
                    file_name = file_path_pattern.format(resource=resource, language=language)
                    await to_thread(
                        self.transifex_api.get_translation, self.project_slug, resource, language, file_name
                    )
                    break
                except Exception:
                    yield DownloadStage(resource, StatusEnum.RETRY, None)
                    exception_info = traceback.format_exc()
            else:
                yield DownloadStage(resource, StatusEnum.FAILED, exception_info)
                return
            yield DownloadStage(resource, StatusEnum.OK, None)

    async def list_resources(self) -> List[str]:
        resources = await to_thread(self.transifex_api.list_resources, self.project_slug)
        resource_slugs = [res["slug"] for res in resources]
        return resource_slugs

    async def list_languages(self, resource_slug: str) -> List[str]:
        return await to_thread(self.transifex_api.list_languages, self.project_slug, resource_slug)
