# Monitoramento Idoso

Sistema de monitoramento de idosos com câmeras IP e detecção de quedas via IA.

## Requisitos

- Python 3.11+
- Câmera IP com suporte ONVIF/RTSP

## Instalação

```bash
git clone <repo>
cd monitoramento_idoso
pip install -e .
```

## Configuração

### 1. Credenciais

Crie o arquivo `.env` na raiz do projeto:

```
MO_ONVIF_USER=admin
MO_ONVIF_PASS=sua_senha
```

### 2. Câmeras

Edite `config.yaml` para adicionar câmeras manuais (quando a descoberta automática não encontra):

```yaml
manual_cameras:
  - ip: 192.168.31.117
    port: 10080
    name: "Sala"
```

## Uso

### Descobrir câmeras

```bash
mo-discover              # Descoberta automática + manual
mo-discover -v           # Modo verbose (debug)
mo-discover --no-rtsp    # Só listar, sem conectar ONVIF
```

### Via Python

```python
from monitoramento_idoso.discovery import discover_cameras, extract_rtsp_urls

cameras = discover_cameras(timeout=5)
for cam in cameras:
    extract_rtsp_urls(cam, username="admin", password="senha")
    print(cam.rtsp_urls)
```

### Visualizar stream

```bash
ffplay rtsp://admin:sua_senha@192.168.31.117:10554/tcp/av0_0
```

## Estrutura

```
src/monitoramento_idoso/
├── config.py                  # Leitura de config.yaml + .env
├── cli.py                     # CLI mo-discover
├── models/
│   └── camera.py              # Dataclass CameraInfo
└── discovery/
    ├── onvif_discovery.py     # WS-Discovery (multicast)
    └── rtsp_extractor.py      # Extração de URLs RTSP via ONVIF
```

## Segurança

- Credenciais ficam em `.env` (nunca no código)
- Senhas são mascaradas em logs e saída do terminal
- `.env` está no `.gitignore`
- Todo processamento é local (sem envio para nuvem)
