from enum import Enum
from typing import NamedTuple, Optional


class StatusEnum(Enum):
    DOWNLOADING = "downloading..."
    RETRY = "retry..."
    FAILED = "failed"
    OK = "ok!"


class DownloadStage(NamedTuple):
    resource: str
    status: StatusEnum
    error_text: Optional[str]
