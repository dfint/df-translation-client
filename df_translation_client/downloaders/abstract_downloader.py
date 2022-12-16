from abc import ABC, abstractmethod
from typing import AsyncIterable, List

from df_translation_client.downloaders.common import DownloadStage


class AbstractDownloader(ABC):
    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def async_downloader(
        self, language: str, resources: List[str], file_path_pattern: str
    ) -> AsyncIterable[DownloadStage]:
        raise NotImplementedError

    @abstractmethod
    async def list_projects(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def list_resources(self, project: str) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def list_languages(self, project: str, resource_slug: str) -> List[str]:
        raise NotImplementedError
