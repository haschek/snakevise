from typing import Any, Dict

from . import chaos, lofi, subtle, urban, vintage

PRESETS: Dict[str, Dict[str, Any]] = {
    "subtle": subtle.CONFIG,
    "vintage": vintage.CONFIG,
    "lofi": lofi.CONFIG,
    "urban": urban.CONFIG,
    "chaos": chaos.CONFIG,
}
