# AGENTS.md — Monitoramento Idoso

## Visão Geral

Sistema de monitoramento de idosos com câmeras IP. Detecta pessoas e alertas (braços levantados) via IA, salva clipes, registra eventos e notifica via Telegram.

## Stack

- **Python 3.11+**
- **YOLOv11n** (ultralytics) — detecção de pessoa
- **MediaPipe** — estimativa de pose (braços levantados)
- **OpenCV** — captura de frames RTSP
- **Streamlit** — dashboard web
- **SQLite** — registro de eventos
- **python-telegram-bot** — notificações
- **ONVIF** — descoberta de câmeras

## Comandos

```bash
mo-discover     # Descobre câmeras na rede
mo-monitor      # Inicia monitoramento (terminal)
mo-dashboard    # Abre dashboard web (porta 8501)
```

## Estrutura

```
src/monitoramento_idoso/
├── cli.py                    # Entry points dos 3 comandos
├── config.py                 # load_config() - YAML + .env com deep merge
├── models/camera.py          # CameraInfo dataclass
├── discovery/
│   ├── onvif_discovery.py    # WS-Discovery via ONVIF
│   └── rtsp_extractor.py     # Extração de URLs RTSP
├── processing/
│   ├── detector.py           # PersonDetector (YOLO)
│   ├── pose_estimator.py     # PoseEstimator (MediaPipe)
│   └── camera_processor.py   # CameraProcessor (thread por câmera)
├── events/
│   ├── models.py             # Event dataclass
│   ├── database.py           # EventDatabase (SQLite)
│   ├── clip_recorder.py      # ClipRecorder (buffer circular 30s)
│   └── notifier.py           # TelegramNotifier
└── ui/
    └── dashboard.py          # Dashboard Streamlit
```

## Configuração

- `config.yaml` — parâmetros gerais
- `.env` — credenciais (ONVIF, Telegram)
- `pyproject.toml` — dependências e entry points

## Fluxo Principal

```
Câmera RTSP → OpenCV (frame) → YOLO (pessoa) → MediaPipe (pose)
                                                      │
                                              Braços levantados?
                                                      │
                                          Sim → Clip + SQLite + Telegram
```

## Convenções

- Threads daemon para processamento por câmera
- Debounce de 5 frames (detecção) e 10 frames (pose) para evitar flickering
- Config: defaults em `_DEFAULT_CONFIG`, merge com YAML, override por env vars
- Eventos: buffer circular em memória, salva .mp4 sob demanda

## Pendências

- Overlay de pose sobre o vídeo (Streamlit)
- Detecção de queda (heurísticas avançadas)
- Classificação de comportamentos anômalos
- Modelos leves (keypoints + LSTM)

## Comandos Úteis

```bash
pip install -e ".[dev]"      # Instalar em modo desenvolvimento
mo-discover -v               # Descoberta com debug
mo-monitor -v                # Monitoramento com debug
mo-dashboard                 # Dashboard web
```
