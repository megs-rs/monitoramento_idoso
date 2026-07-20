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

### 2.1 Estimativa de pose com MediaPipe

- [ ] Nova dependência: `mediapipe` no `pyproject.toml`
- [ ] Nova classe `PoseEstimator` em `processing/pose_estimator.py`
- [ ] Integrar no `CameraProcessor._loop()` após detecção YOLO
- [ ] Retornar landmarks relevantes (ver abaixo)

**Landmarks MediaPipe (33 pontos):**
```
Ponto 11/12 = ombro esquerdo/direito
Ponto 23/24 = quadril esquerdo/direito
Ponto 25/26 = joelho esquerdo/direito
Ponto 27/28 = tornozelo esquerdo/direito
```

**Dados de saída por frame:**
```python
@dataclass
class PoseData:
    left_hip: tuple[float, float]    # (x, y) normalizado 0-1
    right_hip: tuple[float, float]
    left_shoulder: tuple[float, float]
    right_shoulder: tuple[float, float]
    left_knee: tuple[float, float]
    right_knee: tuple[float, float]
    visible: bool                     # se todos os pontos estão visíveis
```

### 2.2 Heurística de queda

- [ ] Nova classe `FallDetector` em `processing/fall_detector.py`
- [ ] Integrar no `CameraProcessor._loop()` após pose
- [ ] Estado: buffer de posições dos últimos N frames

**Heurística 1 — Velocidade do quadril:**
- Calcular velocidade vertical do ponto médio dos quadris (hip_y)
- Se `velocidade > THRESHOLD_VELOCIDADE` → queda em andamento
- Threshold inicial: `0.15` (unidades normalizadas/frame)
- Janela de cálculo: 3 frames

**Heurística 2 — Posição horizontal sustentada:**
- Verificar se torso (ponto médio dos ombros) está abaixo dos joelhos
- Critério: `shoulder_y > knee_y` (y cresce para baixo no MediaPipe)
- Duração mínima: 10 frames (~0.3s a 30fps)
- Se sustentado → queda confirmada

**Combinação:** OR (qualquer uma das duas detecta → queda)

**Estado do FallDetector:**
```python
class FallDetector:
    def __init__(self, velocity_threshold=0.15, hold_frames=10):
        self.velocity_threshold = velocity_threshold
        self.hold_frames = hold_frames
        self._position_buffer: deque[PoseData] = deque(maxlen=15)
        self._horizontal_count = 0
        self._fall_detected = False

    def update(self, pose: PoseData) -> bool:
        """Retorna True se queda detectada neste frame."""
```

### 2.3 Integração no CameraProcessor

Fluxo atualizado do `_loop()`:
```
frame → YOLO.detect() → PoseEstimator.estimate() → FallDetector.update()
                                                        │
                                                   Se queda → log + (Fase 3: clipe + notificação)
```

**Arquivos a modificar:**
- `processing/camera_processor.py` — adicionar pose e heurística no loop
- `config.py` — defaults para `velocity_threshold`, `hold_frames`
- `config.yaml` — seção `fall_detection`

## 3. Módulo de Eventos

- [ ] Gravação de clipe de 15-30 segundos ao detectar queda
  - Buffer circular de frames (últimos 30s) em memória
  - Ao detectar queda → salvar buffer como `.mp4`
  - Diretório: `clips/` com nome `{timestamp}_{camera_ip}.mp4`
- [ ] Registro no SQLite (timestamp, câmera, tipo de evento)
  - Schema: `events(id, timestamp, camera_ip, event_type, clip_path)`
  - Banco: `data/events.db`
- [ ] Notificação via Telegram (python-telegram-bot)
  - Nova dependência: `python-telegram-bot` no `pyproject.toml`
  - Config: `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no `.env`
  - Enviar: texto com timestamp + câmera + clip em vídeo

## 4. Interface de Usuário (Streamlit)

- [ ] Dashboard com visualização ao vivo das câmeras
- [ ] Overlay de pose sobre o vídeo
- [ ] Lista de alertas e histórico de eventos
- [ ] Configuração de câmeras e thresholds pela UI

## 5. Expansão Futura

- [ ] Classificação de comportamentos anômalos (agitação, sonambulismo)
- [ ] Modelos leves: keypoints + LSTM ou YOLO pose + regras avançadas

---

## Arquitetura Atual

```
src/monitoramento_idoso/
├── cli.py                    # mo-discover, mo-monitor
├── config.py                 # load_config() com deep merge
├── models/camera.py          # CameraInfo dataclass
├── discovery/
│   ├── onvif_discovery.py    # WS-Discovery
│   └── rtsp_extractor.py     # Extração RTSP via ONVIF
└── processing/
    ├── detector.py           # PersonDetector (YOLOv11n)
    └── camera_processor.py   # CameraProcessor (thread por câmera)
```
