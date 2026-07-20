from __future__ import annotations

import logging
import re
from urllib.parse import urlparse, urlunparse

from onvif import ONVIFClient

from monitoramento_idoso.models import CameraInfo

logger = logging.getLogger(__name__)


def mask_url(url: str) -> str:
    """Mask credentials in URL for safe logging: rtsp://user:***@host/path"""
    parsed = urlparse(url)
    if parsed.password:
        masked = parsed._replace(
            netloc=parsed.netloc.replace(f":{parsed.password}@", ":***@")
        )
        return urlunparse(masked)
    return url


def extract_rtsp_urls(
    camera: CameraInfo,
    username: str = "admin",
    password: str = "admin",
) -> CameraInfo:
    """Connect to a camera via ONVIF and populate its rtsp_urls dict.

    Modifies the CameraInfo in-place and returns it.
    Keys in rtsp_urls are profile names; values are RTSP URIs.
    """
    logger.info("Connecting to %s:%d for RTSP extraction...", camera.ip, camera.port)

    try:
        client = ONVIFClient(camera.ip, camera.port, username, password)
    except Exception:
        logger.exception("Failed to connect to %s:%d", camera.ip, camera.port)
        return camera

    try:
        media = client.media()
        profiles = media.GetProfiles()
    except Exception:
        logger.exception("Failed to get media profiles from %s", camera.ip)
        return camera

    for profile in profiles:
        profile_name = profile.Name or f"profile-{profile.token}"
        try:
            uri_response = media.GetStreamUri(
                StreamSetup={
                    "Stream": "RTP-Unicast",
                    "Transport": {"Protocol": "RTSP"},
                },
                ProfileToken=profile.token,
            )
            rtsp_uri = uri_response.Uri
            if rtsp_uri:
                rtsp_uri = _fix_localhost(rtsp_uri, camera.ip)
                rtsp_uri = _inject_credentials(rtsp_uri, username, password)
                camera.rtsp_urls[profile_name] = rtsp_uri
                logger.info("  %s → %s", profile_name, mask_url(rtsp_uri))
        except Exception:
            logger.warning("Failed to get stream URI for profile %s", profile_name)

    return camera


def _fix_localhost(uri: str, real_ip: str) -> str:
    """Replace localhost/127.0.0.1 placeholders with the actual camera IP."""
    return re.sub(r"//([^/:@]+)", f"//{real_ip}", uri, count=1)


def _inject_credentials(uri: str, username: str, password: str) -> str:
    """Inject credentials into RTSP URI: rtsp://user:pass@host/..."""
    if not username:
        return uri
    return re.sub(r"//([^/]+)", f"//{username}:{password}@\\1", uri, count=1)
