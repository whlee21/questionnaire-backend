from enum import Enum

from pydantic import BaseModel


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogLevelIn(BaseModel):
    level: LogLevel


class LogLevelOut(BaseModel):
    level: str
