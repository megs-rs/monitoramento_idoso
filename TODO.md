# TODO — Monitoramento Idoso

## 1. Conexão com Câmeras

- [x] Descoberta automática via WS-Discovery (ONVIF)
- [x] Adição manual de câmeras via config.yaml
- [x] Extração automática de URLs RTSP via ONVIF
- [x] Suporte a múltiplos roteadores (câmeras manuais)
- [x] Credenciais seguras via .env
- [x] Mascaramento de senhas em logs e saída
- [x] CLI `mo-discover`

## 2. Processamento (por câmera)

- [x] Captura de frames com OpenCV (thread por câmera)
- [x] Detecção de pessoa com YOLO (ultralytics)
- [x] CLI `mo-monitor`
- [x] Debounce de detecção (5 frames) para evitar flickering
- [x] Estimativa de pose com MediaPipe (braços levantados)
- [x] Detecção de braços levantados como alerta
- [x] Fix: debounce de pose não reseta mais quando MediaPipe perde detecção (flicker)
- [ ] **PROBLEMA:** MediaPipe lite tem taxa de detecção muito baixa (~10%) e inconsistente
  - Modelos alternativos: `pose_landmarker_full` (maior, mais estável)
  - Ou trocar para abordagem diferente (ex: detecção de braços com YOLO pose)
- [ ] Testar com modelo full para validar se resolve a instabilidade
- [ ] Considerar fallback: se MediaPipe não detecta, usar apenas detecção de pessoa
- [x] **Testar com webcam direto (V4L2):**
  - [x] Suporte a `/dev/videoN` como fonte direta no `camera_processor.py`
  - [x] Conversão automática de `/dev/videoN` → índice V4L2 + warmup de 30 frames
  - [x] Webcam adicionada em `config.yaml` (rtsp_url: "/dev/video0")
  - [x] `mo-monitor -v` funciona com webcam (19 FPS, detecção OK)
- [ ] **Avaliar câmera/webcam antes de testar:** resolução mínima 640x480, 15fps+, boa iluminação

## 3. Módulo de Eventos

- [x] Gravação de clipe de 30 segundos ao detectar evento
  - Buffer circular de frames em memória
  - Salva como `.mp4` em `clips/`
- [x] Registro no SQLite (timestamp, câmera, tipo de evento)
  - Schema: `events(id, timestamp, camera_ip, event_type, clip_path)`
  - Banco: `data/events.db`
- [x] Notificação via Telegram (python-telegram-bot)
  - Config: `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no `.env`
  - Envia texto com timestamp + câmera + clip em vídeo

## 4. Interface de Usuário (Streamlit)

- [x] Dashboard com visualização ao vivo das câmeras
- [x] Lista de alertas e histórico de eventos
- [x] Configuração de câmeras e thresholds pela UI
- [ ] Overlay de pose sobre o vídeo

## 5. Expansão Futura

- [ ] Detecção de queda (heurísticas avançadas)
- [ ] Classificação de comportamentos anômalos (agitação, sonambulismo)
- [ ] Modelos leves: keypoints + LSTM ou YOLO pose + regras avançadas

---

## Arquitetura Atual

```
src/monitoramento_idoso/
├── cli.py                    # mo-discover, mo-monitor, mo-dashboard
├── config.py                 # load_config() com deep merge
├── models/camera.py          # CameraInfo dataclass
├── discovery/
│   ├── onvif_discovery.py    # WS-Discovery
│   └── rtsp_extractor.py     # Extração RTSP via ONVIF
├── processing/
│   ├── detector.py           # PersonDetector (YOLOv11n)
│   ├── pose_estimator.py     # PoseEstimator (MediaPipe)
│   └── camera_processor.py   # CameraProcessor (thread por câmera)
├── events/
│   ├── models.py             # Event dataclass
│   ├── database.py           # EventDatabase (SQLite)
│   ├── clip_recorder.py      # ClipRecorder (buffer circular)
│   └── notifier.py           # TelegramNotifier
└── ui/
    └── dashboard.py          # Dashboard Streamlit
```
