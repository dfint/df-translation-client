from abc import abstractmethod, ABC
from typing import List, AsyncIterable, Optional, NamedTuple


class DownloadStage(NamedTuple):
    resource: str
    message: str
    error_text: Optional[str]


class AbstractDownloader(ABC):
    @abstractmethod
    async def check_connection(self):
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
