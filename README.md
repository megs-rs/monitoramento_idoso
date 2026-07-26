# Monitoramento Idoso

Sistema de monitoramento de idosos com câmeras IP e detecção de alertas via IA.

## Requisitos

- Python 3.11+
- Câmera IP com suporte ONVIF/RTSP ou webcam (V4L2)

## Instalação

```bash
git clone <repo>
cd monitoramento_idoso
pip install -e ".[dev]"
```

## Configuração

### 1. Credenciais ONVIF

Crie o arquivo `.env` na raiz do projeto:

```
MO_ONVIF_USER=admin
MO_ONVIF_PASS=sua_senha
```

### 2. Telegram (opcional)

Para receber notificações no Telegram, adicione no `.env`:

```
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
```

Para obter o token: converse com [@BotFather](https://t.me/BotFather) no Telegram e use `/newbot`.

Para obter o chat_id: mande uma mensagem para seu bot e acesse `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`.

### 3. Câmeras

Edite `config.yaml` para adicionar câmeras manuais (quando a descoberta automática não encontra):

```yaml
manual_cameras:
  - ip: 192.168.31.117
    port: 10080
    name: "Sala"
  # Webcam direta (V4L2):
  # - ip: 127.0.0.1
  #   port: 0
  #   name: "Webcam"
  #   rtsp_url: "/dev/video0"
```

### 4. Configuração completa

```yaml
discovery:
  timeout: 5

manual_cameras:
  - ip: 192.168.31.117
    port: 10080
    name: "Câmera Principal"

processing:
  model: "yolo11n.pt"
  confidence: 0.5
  reconnect_delay: 2

events:
  db_path: "data/events.db"
  clip_dir: "clips"
  clip_pre_seconds: 15
  clip_post_seconds: 15
```

## Uso

### Descobrir câmeras

```bash
mo-discover              # Descoberta automática + manual
mo-discover -v           # Modo verbose (debug)
mo-discover --no-rtsp    # Só listar, sem conectar ONVIF
```

### Monitorar (modo terminal)

```bash
mo-monitor              # Inicia detecção de pessoas
mo-monitor -v           # Modo verbose (debug)
```

Funcionamento:
- Conecta nas câmeras via RTSP
- Detecta pessoas com YOLO (1 thread por câmera)
- Detecta braços levantados com MediaPipe
- Salva clipes de 30s (15s antes + 15s depois do alerta)
- Registra eventos no SQLite
- Envia notificação no Telegram (se configurado)

### Dashboard (modo web)

```bash
mo-dashboard            # Abre navegador em http://localhost:8501
```

Acesse de outra máquina: `http://IP_DESTA_MAQUINA:8501`

Funcionalidades:
- Iniciar/parar monitoramento
- Histórico de eventos
- Configuração de parâmetros

### Visualizar stream

```bash
ffplay rtsp://admin:sua_senha@192.168.31.117:10554/tcp/av0_0
```

## Estrutura

```
src/monitoramento_idoso/
├── cli.py                    # mo-discover, mo-monitor, mo-dashboard
├── config.py                 # Leitura de config.yaml + .env
├── models/
│   └── camera.py             # Dataclass CameraInfo
├── discovery/
│   ├── onvif_discovery.py    # WS-Discovery (multicast)
│   └── rtsp_extractor.py     # Extração de URLs RTSP via ONVIF
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

## Segurança

- Credenciais ficam em `.env` (nunca no código)
- Senhas são mascaradas em logs e saída do terminal
- `.env` está no `.gitignore`
- Todo processamento é local (sem envio para nuvem)
