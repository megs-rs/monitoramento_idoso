from __future__ import annotations

import argparse
import logging
import sys

import time

from monitoramento_idoso.config import load_config
from monitoramento_idoso.discovery import discover_cameras, extract_rtsp_urls
from monitoramento_idoso.discovery.rtsp_extractor import mask_url
from monitoramento_idoso.models import CameraInfo
from monitoramento_idoso.processing import CameraProcessor, PersonDetector


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


def _get_cameras(config: dict, username: str, password: str) -> list[CameraInfo]:
    disc_cfg = config["discovery"]
    timeout = disc_cfg.get("timeout", 5)

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

    for cam in cameras:
        extract_rtsp_urls(cam, username=username, password=password)

    return cameras


def monitor_main() -> None:
    parser = argparse.ArgumentParser(
        prog="mo-monitor",
        description="Start person detection on cameras",
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
    onvif_cfg = config["onvif"]
    proc_cfg = config["processing"]

    username = args.username or onvif_cfg.get("username", "admin")
    password = args.password or onvif_cfg.get("password", "admin")

    cameras = _get_cameras(config, username, password)

    cameras_with_rtsp = [cam for cam in cameras if cam.rtsp_urls]
    if not cameras_with_rtsp:
        print("No cameras with RTSP streams found.")
        sys.exit(0)

    print(f"Starting monitoring on {len(cameras_with_rtsp)} camera(s)...")
    for cam in cameras_with_rtsp:
        print(f"  - {cam.ip} ({cam.model or 'unknown'})")
    print()

    detector = PersonDetector(
        model_name=proc_cfg.get("model", "yolo11n.pt"),
        confidence=proc_cfg.get("confidence", 0.5),
    )

    processors = []
    for cam in cameras_with_rtsp:
        proc = CameraProcessor(
            camera=cam,
            detector=detector,
            reconnect_delay=proc_cfg.get("reconnect_delay", 2),
        )
        proc.start()
        processors.append(proc)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        for proc in processors:
            proc.stop()
        print("Done.")
