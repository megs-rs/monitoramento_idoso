from __future__ import annotations

import logging
from typing import Any

from onvif import ONVIFDiscovery

from monitoramento_idoso.models import CameraInfo

logger = logging.getLogger(__name__)


def discover_cameras(timeout: int = 5) -> list[CameraInfo]:
    """Discover ONVIF cameras on the local network via WS-Discovery.

    Returns a list of CameraInfo with network info populated.
    RTSP URLs are NOT extracted here — call extract_rtsp_urls() for that.
    """
    logger.info("Starting WS-Discovery (timeout=%ds)...", timeout)
    discovery = ONVIFDiscovery(timeout=timeout)
    devices = discovery.discover()
    logger.info("Found %d device(s)", len(devices))

    cameras: list[CameraInfo] = []
    for dev in devices:
        host: str = dev.get("host", "")
        port: int = int(dev.get("port", 80))
        xaddrs: list[str] = dev.get("xaddrs", [])
        scopes: list[str] = dev.get("scopes", [])

        manufacturer, model = _parse_scopes(scopes)

        cameras.append(
            CameraInfo(
                ip=host,
                port=port,
                manufacturer=manufacturer,
                model=model,
                scopes=scopes,
                xaddrs=xaddrs,
            )
        )
        logger.debug("  %s:%d — %s %s", host, port, manufacturer, model)

    return cameras


def _parse_scopes(scopes: list[str]) -> tuple[str, str]:
    manufacturer = ""
    model = ""
    for scope in scopes:
        scope_lower = scope.lower()
        if scope_lower.startswith("hardware/"):
            model = scope.split("/", 1)[1]
        elif scope_lower.startswith("name/"):
            manufacturer = scope.split("/", 1)[1]
    return manufacturer, model
