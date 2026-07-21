# Especificação: Sistema de Monitoramento de Idosos com Câmeras IP e Detecção de Quedas via IA

## Stack Recomendado

**Linguagem:** Python 3.11+

**Bibliotecas principais:**
- `opencv-python` — captura de streams RTSP de qualquer câmera IP
- `mediapipe` + `ultralytics` (YOLOv11) — detecção de pessoa + estimativa de pose
- `onvif` (onvif-python) — descoberta automática de câmeras
- `streamlit` — dashboard web simples (live view + histórico)
- `python-telegram-bot` — notificações de alerta
- `sqlite3` — log de eventos e armazenamento de clipes

## Hardware Mínimo (PC Local)

- **CPU:** 4 núcleos (Intel i5 / AMD Ryzen 5 ou equivalente)
- **RAM:** 8 GB (16 GB recomendado)
- **GPU:** Opcional — NVIDIA com CUDA (acelera inferência YOLO); MediaPipe roda bem em CPU
- **Armazenamento:** SSD 256 GB + espaço para vídeos curtos
- Compatível com hardware modesto (ex.: Ryzen 3 3200G ou similar)

## Arquitetura Atual

1. **Conexão com Câmeras**
   - Adição manual de URL RTSP ou descoberta via ONVIF
   - Funciona com qualquer câmera IP que suporte RTSP

2. **Processamento (por câmera em thread separada)**
   - Captura de frames com OpenCV
   - Detecção de pessoa com YOLO (YOLOv11n)
   - Estimativa de pose com MediaPipe (landmarks: ombros, quadris, joelhos, punhos)
   - Detecção de alerta: braços levantados (punho acima do ombro)
   - Debounce de 10 frames para evitar falsos positivos

3. **Módulo de Eventos**
   - Alerta detectado → grava clipe de 30 segundos (buffer circular)
   - Registra no SQLite (timestamp, câmera, tipo de evento)
   - Envia notificação via Telegram (com vídeo)

4. **Interface de Usuário (UI)**
   - Dashboard Streamlit:
     - Iniciar/parar monitoramento
     - Lista de alertas e histórico
     - Configuração de parâmetros

## Expansão Futura (Comportamentos Anômalos)

- **Detecção de queda** (heurísticas avançadas):
  - Alta velocidade nos keypoints do quadril/torso
  - Posição horizontal sustentada (torso abaixo dos joelhos por tempo mínimo)
- Classificação de sequências de pose para detectar:
  - Agitação / pânico
  - Sonambulismo
  - Outros padrões anômalos
- Modelos leves: sequência de keypoints + LSTM / classificador simples ou YOLO pose + regras avançadas
- Overlay de pose sobre o vídeo no dashboard
- Tudo processado localmente (sem envio para nuvem)

## Observações Importantes

- Todo processamento é local (privacidade máxima)
- Foco inicial em detecção de braços levantados para validar o software antes de implementar heurísticas de queda mais complexas
- Fácil escalar para múltiplas câmeras
- Recomendado começar com 1 câmera para validar a lógica de detecção
