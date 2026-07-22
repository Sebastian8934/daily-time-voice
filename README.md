# DailyTime Voice API

Servicio en **Python (FastAPI)** que entiende comandos en español (texto o audio) y ejecuta acciones contra la API ASP.NET de DailyTime.

```
Usuario → Voice API (Python :8000) → DailyTime API (.NET :5265) → SQL Server
```

## Requisitos

- Python 3.11+
- API .NET de DailyTime en ejecución (`http://localhost:5265` por defecto)

## Arranque rápido

### Git Bash (MINGW / lo que usas en Cursor)

En Bash **no** uses `\`. Activa así:

```bash
cd daily-time-voice
source .venv/Scripts/activate
python -m app
```

Si `activate` falla, arranca directo con el Python del venv:

```bash
cd daily-time-voice
.venv/Scripts/python -m app
```

### PowerShell

```powershell
cd daily-time-voice
.\.venv\Scripts\Activate.ps1
python -m app
```

### Primera vez (crear venv e instalar)

```bash
cd daily-time-voice
python -m venv .venv
source .venv/Scripts/activate   # Git Bash
pip install -r requirements.txt
cp .env.example .env
python -m app
```

### Uso desde el frontend

1. Arranca la API .NET y esta Voice API (`python -m app`).
2. En Next.js, abre la app y usa el **botón de micrófono** flotante (esquina inferior derecha).
3. Habla o escribe un comando; el front llama a `POST /api/voice/command`.

Variable opcional en el front: `NEXT_PUBLIC_VOICE_API_URL` (default `http://localhost:8000`).


## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del servicio |
| `GET` | `/health/upstream` | ¿Responde la API .NET? |
| `GET` | `/api/voice/help` | Lista de comandos |
| `POST` | `/api/voice/parse` | Solo interpreta (sin ejecutar) |
| `POST` | `/api/voice/command` | Interpreta y ejecuta |
| `POST` | `/api/voice/transcribe` | Audio → texto (Whisper opcional) |
| `POST` | `/api/voice/command/audio` | Audio → interpreta → ejecuta |

### Ejemplo: crear tarea

```bash
curl -X POST http://localhost:8000/api/voice/command ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"crea una tarea llamada revisar informe para mañana\"}"
```

### Ejemplo: dry-run (no escribe en BD)

```json
{
  "text": "completa la tarea revisar informe",
  "dry_run": true
}
```

### Respuesta típica

```json
{
  "success": true,
  "transcript": "crea una tarea llamada revisar informe",
  "intent": "create_task",
  "confidence": 0.94,
  "message": "Tarea creada: «revisar informe» (#42).",
  "navigate_to": "/board",
  "data": { "...": "..." },
  "dry_run": false
}
```

`navigate_to` sirve para que el frontend (o una app de escritorio) cambie de pantalla.

## Comandos soportados (MVP)

- Crear tarea / nota
- Listar tareas / notas
- Completar tarea (por nombre)
- Registrar tiempo
- Navegar: tablero, calendario, informe, estados, categorías
- Ayuda

## Audio (opcional)

Por defecto solo hay texto. Para Whisper local:

1. `pip install openai-whisper` (y dependencias de torch)
2. En `.env`: `ENABLE_WHISPER=true`
3. Usa `POST /api/voice/command/audio` con `multipart/form-data` y campo `audio`

## Estructura

```
daily-time-voice/
  app/
    main.py                 # FastAPI
    config.py
    models/schemas.py
    routers/                # health + voice
    services/
      daily_time_client.py  # HTTP → API .NET
      intent_parser.py      # Español → intent
      action_executor.py    # Intent → acciones
      speech.py             # Whisper opcional
  requirements.txt
  .env.example
```

## Notas

- No hay OAuth: asume la misma API abierta local/de escritorio.
- El parser es por reglas (sin LLM). Más adelante se puede enchufar un modelo.
- Si usas HTTPS en .NET, ajusta `DAILY_TIME_API_URL` (p. ej. `https://localhost:7169`).
