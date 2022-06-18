from abc import abstractmethod, ABC
from typing import AsyncIterable, List

from df_translation_client.downloaders.common import DownloadStage


class AbstractDownloader(ABC):
    @abstractmethod
    async def connect(self) -> None:
        ...

    @abstractmethod
    async def async_downloader(self, language: str, resources: List[str], file_path_pattern: str) \
            -> AsyncIterable[DownloadStage]:
        ...

    @abstractmethod
    async def list_resources(self) -> List[str]:
        ...

    @abstractmethod
    async def list_languages(self, resource_slug: str) -> List[str]:
        ...
