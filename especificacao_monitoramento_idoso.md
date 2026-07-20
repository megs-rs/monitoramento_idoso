# Especificação: Sistema de Monitoramento de Idosos com Câmeras IP e Detecção de Quedas via IA

## Stack Recomendado

**Linguagem:** Python 3.11+

**Bibliotecas principais:**
- `opencv-python` — captura de streams RTSP de qualquer câmera IP
- `mediapipe` + `ultralytics` (YOLOv8 / YOLOv11) — detecção de pessoa + estimativa de pose
- `onvif` (python-onvif-zeep ou onvif-python) — descoberta automática de câmeras
- `streamlit` — dashboard web simples (live view + histórico)
- `python-telegram-bot` — notificações de alerta
- `sqlite3` — log de eventos e armazenamento de clipes

## Hardware Mínimo (PC Local)

- **CPU:** 4 núcleos (Intel i5 / AMD Ryzen 5 ou equivalente)
- **RAM:** 8 GB (16 GB recomendado)
- **GPU:** Opcional — NVIDIA com CUDA (acelera inferência YOLO); MediaPipe roda bem em CPU
- **Armazenamento:** SSD 256 GB + espaço para vídeos curtos
- Compatível com hardware modesto (ex.: Ryzen 3 3200G ou similar)

## Arquitetura Básica (Foco Inicial: Detecção de Quedas)

1. **Conexão com Câmeras**
   - Adição manual de URL RTSP ou descoberta via ONVIF
   - Funciona com qualquer câmera IP que suporte RTSP

2. **Processamento (por câmera em thread separada)**
   - Captura de frames com OpenCV
   - Detecção de pessoa com YOLO
   - Estimativa de pose com MediaPipe
   - Lógica de queda (heurística):
     - Alta velocidade nos keypoints do quadril/torso
     - Posição horizontal sustentada (torso abaixo dos joelhos por tempo mínimo)

3. **Módulo de Eventos**
   - Queda detectada → grava clipe de 15-30 segundos
   - Registra no SQLite (timestamp, câmera, tipo de evento)
   - Envia notificação via Telegram (ou email)

4. **Interface de Usuário (UI)**
   - Dashboard Streamlit:
     - Visualização ao vivo das câmeras com overlay de pose
     - Lista de alertas e histórico
     - Configuração de câmeras e thresholds

## Expansão Futura (Comportamentos Anômalos)

- Classificação de sequências de pose para detectar:
  - Agitação / pânico
  - Sonambulismo
  - Outros padrões anômalos
- Modelos leves: sequência de keypoints + LSTM / classificador simples ou YOLO pose + regras avançadas
- Tudo processado localmente (sem envio para nuvem)

## Observações Importantes

- Todo processamento é local (privacidade máxima)
- Foco inicial apenas em quedas (implementação rápida com heurística)
- Fácil escalar para múltiplas câmeras
- Recomendado começar com 1 câmera para validar a lógica de detecção
