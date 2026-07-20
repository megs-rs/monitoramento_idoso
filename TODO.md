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
- [ ] Estimativa de pose com MediaPipe
- [ ] Lógica de queda (heurística):
  - [ ] Alta velocidade nos keypoints do quadril/torso
  - [ ] Posição horizontal sustentada (torso abaixo dos joelhos por tempo mínimo)

## 3. Módulo de Eventos

- [ ] Gravação de clipe de 15-30 segundos ao detectar queda
- [ ] Registro no SQLite (timestamp, câmera, tipo de evento)
- [ ] Notificação via Telegram (python-telegram-bot)

## 4. Interface de Usuário (Streamlit)

- [ ] Dashboard com visualização ao vivo das câmeras
- [ ] Overlay de pose sobre o vídeo
- [ ] Lista de alertas e histórico de eventos
- [ ] Configuração de câmeras e thresholds pela UI

## 5. Expansão Futura

- [ ] Classificação de comportamentos anômalos (agitação, sonambulismo)
- [ ] Modelos leves: keypoints + LSTM ou YOLO pose + regras avançadas
