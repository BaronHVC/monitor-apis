# Monitor de APIs 🛰️

Script en Python que vigila la disponibilidad de una lista de APIs: verifica que respondan, mide su tiempo de respuesta, registra todo en una bitácora (log) y genera alertas con reintentos automáticos cuando un servicio falla.

## ¿Qué problema resuelve?

En lugar de enterarte de que un servicio está caído porque alguien se queja, el monitor lo detecta primero: revisa cada API periódicamente y deja evidencia de cada revisión, igual que lo hacen herramientas profesionales como UptimeRobot o Datadog, pero construido desde cero.

## Características

- Verificación periódica de múltiples APIs (configurable)
- Medición de tiempo de respuesta de cada endpoint
- Bitácora en archivo `monitor.log` y en consola simultáneamente
- Reintentos automáticos antes de generar una alerta
- Detección de tres tipos de falla: status code inesperado, timeout y servicio inalcanzable
- Modo de prueba de una sola ronda (`--una-vez`)

## Tecnologías

Python 3 · requests · logging

## Instalación

```bash
git clone https://github.com/TU_USUARIO/monitor-apis.git
cd monitor-apis
pip install -r requirements.txt
```

## Uso

```bash
# Una sola ronda de verificación (para probar)
python monitor.py --una-vez

# Modo vigilante: revisa cada 5 minutos hasta detenerlo con Ctrl+C
python monitor.py
```

Las APIs a vigilar, el intervalo, el timeout y el número de reintentos se configuran editando las constantes al inicio de `monitor.py`.

## Ejemplo de bitácora

```
2026-07-05 10:30:01 INFO OK https://api.github.com status=200 tiempo=0.32s
2026-07-05 10:35:01 INFO OK https://api.github.com status=200 tiempo=0.29s
2026-07-05 10:40:03 ERROR TIMEOUT https://api.ejemplo.com no respondió en 5s
2026-07-05 10:40:05 INFO Reintentando https://api.ejemplo.com (intento 2)...
2026-07-05 10:40:12 CRITICAL 🚨 ALERTA: https://api.ejemplo.com sigue fallando después de 3 intentos
```

## Mejoras planeadas

- [ ] Enviar alertas por correo o Telegram
- [ ] Guardar el historial en una base de datos (Supabase)
- [ ] Ejecutarlo automáticamente en la nube con GitHub Actions
- [ ] Dashboard con estadísticas de disponibilidad

## Autor

Carlos Eduardo — proyecto de práctica de automatización y monitoreo con Python.
