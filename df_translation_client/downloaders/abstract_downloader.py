from abc import abstractmethod, ABC


class AbstractDownloader(ABC):
    @abstractmethod
    async def check_connection(self):
        ...

    @abstractmethod
    async def async_downloader(self, language: str, resources, file_path_pattern: str):
        ...

    @abstractmethod
    async def list_resources(self):
        ...

    @abstractmethod
    async def list_languages(self, resource_slug: str):
        ...
