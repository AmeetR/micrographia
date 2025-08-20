"""Common enums and runtime constants."""

from __future__ import annotations

from enum import Enum


class LoaderType(str, Enum):
    """Supported model loader implementations."""

    PEFT_LORA = "peft-lora"


class Quantization(str, Enum):
    """Quantization options for model loading."""

    BITS4 = "4bit"
    BITS8 = "8bit"


class DeviceHint(str, Enum):
    """Device placement hints."""

    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"


class AdapterScheme(str, Enum):
    """Supported adapter URI schemes."""

    HF = "hf://"
    S3 = "s3://"
    GS = "gs://"
    FILE = "file://"


ADAPTER_URI_SCHEMES = tuple(s.value for s in AdapterScheme)


STUB_BASE_ID = "stub"


STOP_REASON_PREFLIGHT = "error:Preflight"
