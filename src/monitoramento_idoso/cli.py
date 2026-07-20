from __future__ import annotations

import argparse
import logging
import sys

from monitoramento_idoso.config import load_config
from monitoramento_idoso.discovery import discover_cameras, extract_rtsp_urls
from monitoramento_idoso.discovery.rtsp_extractor import mask_url
from monitoramento_idoso.models import CameraInfo


def discover_main() -> None:
    parser = argparse.ArgumentParser(
        prog="mo-discover",
        description="Discover ONVIF cameras on the local network",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=None,
        help="WS-Discovery timeout in seconds (default: from config)",
    )
    parser.add_argument(
        "-u", "--username",
        default=None,
        help="ONVIF username (default: from config)",
    )
    parser.add_argument(
        "-p", "--password",
        default=None,
        help="ONVIF password (default: from config)",
    )
    parser.add_argument(
        "--no-rtsp",
        action="store_true",
        help="Skip RTSP URL extraction (only list discovered devices)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_config()
    disc_cfg = config["discovery"]
    onvif_cfg = config["onvif"]

    timeout = args.timeout or disc_cfg.get("timeout", 5)
    username = args.username or onvif_cfg.get("username", "admin")
    password = args.password or onvif_cfg.get("password", "admin")

    cameras = discover_cameras(timeout=timeout)

    manual = config.get("manual_cameras") or []
    for entry in manual:
        cameras.append(
            CameraInfo(
                ip=entry["ip"],
                port=entry.get("port", 80),
                model=entry.get("name", ""),
            )
        )

    if not cameras:
        print("No cameras found on the network.")
        sys.exit(0)

    if not args.no_rtsp:
        for cam in cameras:
            extract_rtsp_urls(cam, username=username, password=password)

    print(f"\n{'='*60}")
    print(f" Found {len(cameras)} camera(s)")
    print(f"{'='*60}\n")

    for i, cam in enumerate(cameras, 1):
        print(f"[{i}] {cam.ip}:{cam.port}")
        if cam.manufacturer:
            print(f"    Manufacturer: {cam.manufacturer}")
        if cam.model:
            print(f"    Model:        {cam.model}")
        if cam.scopes:
            print(f"    Scopes:       {', '.join(cam.scopes)}")
        if cam.rtsp_urls:
            print(f"    RTSP Streams:")
            for name, url in cam.rtsp_urls.items():
                print(f"      {name}: {mask_url(url)}")
        print()
