import asyncio
import traceback

from transifex.api import TransifexAPI

try:
    from asyncio import to_thread
except ImportError:
    async def to_thread(func, *args):
        return await asyncio.get_running_loop().run_in_executor(None, func, *args)


class TransifexApiDownloader:
    transifex_api: TransifexAPI
    project_slug: str

    def __init__(self, username: str, password: str, project_slug: str):
        self.transifex_api = TransifexAPI(username, password, "https://www.transifex.com")
        self.project_slug = project_slug

    async def check_connection(self):
        assert await to_thread(self.transifex_api.ping), "No connection to the server"
        assert await to_thread(self.transifex_api.project_exists, self.project_slug),\
            f"Project {self.project_slug} does not exist"

    async def async_downloader(self, language: str, resources, file_path_pattern: str):
        for i, res in enumerate(resources):
            yield i, "downloading...", None
            exception_info = None
            for j in range(10, 0, -1):
                try:
                    await to_thread(
                        self.transifex_api.get_translation,
                        self.project_slug,
                        res["slug"],
                        language,
                        file_path_pattern.format(res["slug"])
                    )
                    break
                except Exception:
                    yield i, f"retry... ({j})", None
                    exception_info = traceback.format_exc()
            else:
                yield i, "failed", exception_info
                return
            yield i, "ok!", None

        yield None, "completed", None

    async def list_resources(self):
        return await to_thread(self.transifex_api.list_resources, self.project_slug)

    async def list_languages(self, resource_slug: str):
        return await to_thread(self.transifex_api.list_languages, self.project_slug, resource_slug)
