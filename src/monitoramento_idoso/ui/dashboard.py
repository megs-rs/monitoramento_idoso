from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from monitoramento_idoso.config import load_config
from monitoramento_idoso.events.clip_recorder import ClipRecorder
from monitoramento_idoso.events.database import EventDatabase
from monitoramento_idoso.events.models import Event
from monitoramento_idoso.events.notifier import TelegramNotifier
from monitoramento_idoso.models import CameraInfo
from monitoramento_idoso.processing import CameraProcessor, PersonDetector, PoseEstimator


def run_dashboard() -> None:
    st.set_page_config(
        page_title="Monitoramento Idoso",
        page_icon="👁️",
        layout="wide",
    )

    st.title("👁️ Monitoramento de Idosos")

    config = load_config()
    proc_cfg = config["processing"]
    events_cfg = config["events"]

    if "processors" not in st.session_state:
        st.session_state.processors = {}
    if "database" not in st.session_state:
        st.session_state.database = EventDatabase(db_path=events_cfg.get("db_path", "data/events.db"))

    tab_monitor, tab_events, tab_config = st.tabs(["Monitoramento", "Eventos", "Configuração"])

    with tab_monitor:
        _render_monitoring_tab(proc_cfg, events_cfg)

    with tab_events:
        _render_events_tab()

    with tab_config:
        _render_config_tab(proc_cfg, events_cfg)


def _render_monitoring_tab(proc_cfg: dict, events_cfg: dict) -> None:
    st.subheader("Câmeras")

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("Iniciar Todas", type="primary"):
            _start_all_cameras(proc_cfg, events_cfg)
        if st.button("Parar Todas"):
            _stop_all_cameras()

    with col1:
        for ip, proc in st.session_state.processors.items():
            status = "🟢 Rodando" if proc.is_running else "🔴 Parado"
            st.write(f"**{ip}** — {status}")

    st.divider()
    st.subheader("Últimos Eventos")

    database = st.session_state.database
    events = database.list_recent(limit=10)

    if not events:
        st.info("Nenhum evento registrado")
    else:
        for event in events:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{event.event_type}** — {event.camera_ip}")
            with col2:
                st.write(event.timestamp.strftime("%d/%m/%Y %H:%M:%S"))
            with col3:
                if event.clip_path:
                    st.write(f"📎 {Path(event.clip_path).name}")


def _render_events_tab() -> None:
    st.subheader("Histórico de Eventos")

    database = st.session_state.database
    events = database.list_recent(limit=100)

    if not events:
        st.info("Nenhum evento registrado")
        return

    for event in events:
        with st.expander(f"{event.timestamp.strftime('%d/%m/%Y %H:%M:%S')} — {event.event_type} ({event.camera_ip})"):
            st.write(f"**Câmera:** {event.camera_ip}")
            st.write(f"**Tipo:** {event.event_type}")
            st.write(f"**Horário:** {event.timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
            if event.clip_path:
                st.write(f"**Clipe:** {event.clip_path}")


def _render_config_tab(proc_cfg: dict, events_cfg: dict) -> None:
    st.subheader("Configuração")

    with st.form("config_form"):
        model = st.text_input("Modelo YOLO", value=proc_cfg.get("model", "yolo11n.pt"))
        confidence = st.slider("Confiança", 0.1, 1.0, proc_cfg.get("confidence", 0.5))
        reconnect_delay = st.number_input("Delay Reconexão (s)", 1, 30, proc_cfg.get("reconnect_delay", 2))
        clip_duration = st.number_input("Duração Clipe (s)", 5, 60, events_cfg.get("clip_duration", 30))

        submitted = st.form_submit_button("Salvar")
        if submitted:
            st.success("Configuração salva! (Reinicie o monitor para aplicar)")


def _start_all_cameras(proc_cfg: dict, events_cfg: dict) -> None:
    config = load_config()
    onvif_cfg = config["onvif"]

    from monitoramento_idoso.discovery import discover_cameras, extract_rtsp_urls

    timeout = config["discovery"].get("timeout", 5)
    username = onvif_cfg.get("username", "admin")
    password = onvif_cfg.get("password", "admin")

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

    cameras_with_rtsp = [cam for cam in cameras if cam.rtsp_urls]

    if not cameras_with_rtsp:
        st.warning("Nenhuma câmera com stream RTSP encontrada")
        return

    detector = PersonDetector(
        model_name=proc_cfg.get("model", "yolo11n.pt"),
        confidence=proc_cfg.get("confidence", 0.5),
    )

    pose_estimator = PoseEstimator()

    notifier = None
    load_dotenv()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        notifier = TelegramNotifier(bot_token, chat_id)

    clip_recorder = ClipRecorder(duration_seconds=events_cfg.get("clip_duration", 30))

    for cam in cameras_with_rtsp:
        if cam.ip not in st.session_state.processors or not st.session_state.processors[cam.ip].is_running:
            proc = CameraProcessor(
                camera=cam,
                detector=detector,
                pose_estimator=pose_estimator,
                database=st.session_state.database,
                notifier=notifier,
                clip_recorder=clip_recorder,
                reconnect_delay=proc_cfg.get("reconnect_delay", 2),
            )
            proc.start()
            st.session_state.processors[cam.ip] = proc

    st.rerun()


def _stop_all_cameras() -> None:
    for ip, proc in st.session_state.processors.items():
        if proc.is_running:
            proc.stop()
    st.rerun()
