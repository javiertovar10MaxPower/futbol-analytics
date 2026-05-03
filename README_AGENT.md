# AI News Agent — Resumen semanal de IA al Outlook

Agente Python que cada lunes investiga las novedades más relevantes en IA en cuatro frentes (centros académicos, labs de big tech, papers, medios) y envía un resumen HTML a tu correo Outlook.

> El proyecto convive con `index.html` (Futbol Analytics). El agente vive bajo `ai_news_agent/` y no toca el SPA de fútbol.

## Cómo funciona

1. `researcher.py` llama a `claude-sonnet-4-6` con las herramientas server-side `web_search_20260209` y `web_fetch_20260209` y un schema JSON estricto. Claude busca en las fuentes prioritarias, abre los artículos relevantes y devuelve 12-18 items estructurados.
2. `renderer.py` agrupa por categoría y arma un email HTML con estilos email-client friendly.
3. `emailer.py` lo envía vía SMTP `smtp.office365.com:587` (STARTTLS) con tu app password.
4. `.github/workflows/weekly-ai-news.yml` lo programa los lunes 08:00 UTC.

## Setup local

```bash
# 1. Instalar dependencias
pip install -e .

# 2. Variables de entorno
cp .env.example .env
# Edita .env y llena ANTHROPIC_API_KEY (mínimo) y, para envío real, OUTLOOK_*.

# 3. Dry-run (no envía email; deja preview en out/preview.html)
python -m ai_news_agent --dry-run
open out/preview.html

# 4. Envío real
python -m ai_news_agent
```

### Generar el `OUTLOOK_APP_PASSWORD`

1. Activa autenticación en dos pasos en [account.microsoft.com/security](https://account.microsoft.com/security).
2. En *Opciones avanzadas de seguridad → Contraseñas de aplicación* genera una nueva.
3. Copia la cadena y guárdala como `OUTLOOK_APP_PASSWORD` en `.env` (local) o en GitHub Secrets (CI).

## Programación en GitHub Actions

1. En el repo: **Settings → Secrets and variables → Actions → New repository secret** y crea:
   - `ANTHROPIC_API_KEY`
   - `OUTLOOK_EMAIL` (la cuenta que envía)
   - `OUTLOOK_APP_PASSWORD` (la app password generada arriba)
   - `RECIPIENT_EMAIL` (puede ser la misma)
2. Push la rama. El workflow corre automáticamente cada lunes 08:00 UTC.
3. Para ejecutarlo manualmente: **Actions → Weekly AI news brief → Run workflow** (puedes elegir `dry_run`).

## Ajustes comunes

- **Cambiar fuentes:** edita `ai_news_agent/sources.py`. La lista se inyecta en el system prompt.
- **Cambiar idioma:** ajusta los textos de `ai_news_agent/prompts.py` y la plantilla `templates/email.html.j2`.
- **Cambiar frecuencia:** modifica el `cron` en `.github/workflows/weekly-ai-news.yml`.
- **Cambiar modelo:** flag `--model claude-opus-4-7` (más capaz, más caro) o ajusta el default en `agent.py`.
- **Más/menos items:** flags `--min-items` y `--max-items`.
- **Ventana temporal:** flag `--lookback-days`.

## Costo

- API Claude (Sonnet 4.6 con `effort: high` + adaptive thinking + web tools): ~$0.10–0.40 por ejecución semanal. El system prompt está cacheado, así que las re-ejecuciones cercanas son más baratas.
- GitHub Actions: gratis dentro del cuota de cuentas personales.
- Outlook SMTP: gratis.

## Troubleshooting

- **`535 5.7.139 Authentication unsuccessful`**: la app password está mal o no tienes 2FA activado. Regenera la app password.
- **`smtplib.SMTPNotSupportedError: STARTTLS extension not supported`**: el host bloquea SMTP saliente. En local prueba desde otra red; en GitHub Actions no debería pasar.
- **JSON parse error tras el research**: revisa `out/preview.html` no se creó y mira el log; suele ser que el modelo no terminó (subir `--max-items` a 18 o re-correr).
- **Pocos items u omisiones**: amplía `--lookback-days` a 10–14, o sube a `--model claude-opus-4-7`.
