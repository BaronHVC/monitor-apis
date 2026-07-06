# ============================================================
# MONITOR DE APIs - Proyecto de aprendizaje
# ============================================================
# Qué hace:
#   1. Revisa cada cierto tiempo si una lista de APIs responde
#   2. Mide cuánto tarda cada una en responder
#   3. Guarda todo en un archivo de log (monitor.log)
#   4. Guarda el historial en Supabase (tabla historial_monitoreo)
#   5. Si una API falla, reintenta y envía una ALERTA por Telegram
#
# Cómo usarlo:
#   python monitor.py            -> repeticiones infinitas (Ctrl+C para parar)
#   python monitor.py --una-vez  -> hace una sola ronda (para probar)
#
# Archivo .env requerido 
# ============================================================

import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()  

# ---------- CONFIGURACIÓN ----------

URLS = [
    "https://api.github.com",              # API pública de GitHub
    "https://pokeapi.co/api/v2/pokemon/1", # API pública de Pokémon
    "https://api-que-no-existe-123.com"
]

INTERVALO_SEGUNDOS = 300   # cada cuánto revisar (s)
TIMEOUT_SEGUNDOS = 5       # cuánto esperar antes de considerar que no responde
REINTENTOS = 2             # cuántas veces reintentar antes de alertar

# Credenciales 
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ---------- CONFIGURACIÓN DE LOGS ----------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("monitor.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# ---------- CONEXIÓN A SUPABASE ----------
# Se conecta una sola vez al inicio.
# el monitor funciona igual pero sin guardar historial.

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Conectado a Supabase: historial activado")
    except Exception as error:
        logging.error(f"No se pudo conectar a Supabase: {error}")
else:
    logging.warning("Supabase no configurado (falta .env); historial solo en log")


def guardar_historial(url: str, exito: bool, status_code=None,
                      tiempo=None, detalle=None) -> None:
    """Guarda el resultado de una revisión en la tabla historial_monitoreo.

    Si Supabase no está disponible, no rompe el monitor.
    """
    if supabase is None:
        return
    try:
        supabase.table("historial_monitoreo").insert({
            "url": url,
            "exito": exito,
            "status_code": status_code,
            "tiempo_segundos": tiempo,
            "detalle": detalle,
        }).execute()
    except Exception as error:
        logging.error(f"No se pudo guardar en Supabase: {error}")


def enviar_alerta_telegram(mensaje: str) -> None:
    """Envía un mensaje a tu Telegram usando tu bot."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram no configurado (falta .env); alerta solo en log")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        respuesta = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje},
            timeout=10,
        )
        if respuesta.status_code == 200:
            logging.info("Alerta enviada por Telegram")
        else:
            logging.error(f"Telegram respondió status={respuesta.status_code}")
    except requests.exceptions.RequestException as error:
        logging.error(f"No se pudo enviar la alerta por Telegram: {error}")


def revisar_api(url: str) -> bool:
    """Hace una petición GET, registra el resultado en log y Supabase.

    Devuelve True si la API respondió bien, False si falló.
    """
    try:
        inicio = time.time()
        respuesta = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
        duracion = round(time.time() - inicio, 3)

        if respuesta.status_code == 200:
            logging.info(f"OK {url} status={respuesta.status_code} tiempo={duracion}s")
            guardar_historial(url, True, respuesta.status_code, duracion)
            return True
        else:
            logging.warning(f"RESPUESTA RARA {url} status={respuesta.status_code}")
            guardar_historial(url, False, respuesta.status_code, duracion,
                              "status code inesperado")
            return False

    except requests.exceptions.Timeout:
        logging.error(f"TIMEOUT {url} no respondió en {TIMEOUT_SEGUNDOS}s")
        guardar_historial(url, False, None, None, f"timeout de {TIMEOUT_SEGUNDOS}s")
        return False
    except requests.exceptions.RequestException as error:
        logging.error(f"NO RESPONDE {url} error={error}")
        guardar_historial(url, False, None, None, str(error)[:200])
        return False


def revisar_con_reintentos(url: str) -> None:
    """Revisa una API y, si falla, reintenta antes de alertar."""
    for intento in range(1, REINTENTOS + 2):
        if revisar_api(url):
            return
        if intento <= REINTENTOS:
            logging.info(f"Reintentando {url} (intento {intento + 1})...")
            time.sleep(2)

    alerta = f"🚨 ALERTA: {url} sigue fallando después de {REINTENTOS + 1} intentos"
    logging.critical(alerta)
    enviar_alerta_telegram(alerta)


def ronda_de_monitoreo() -> None:
    """Revisa todas las APIs de la lista una vez."""
    logging.info(f"--- Iniciando ronda de monitoreo ({len(URLS)} APIs) ---")
    for url in URLS:
        revisar_con_reintentos(url)
    logging.info("--- Ronda terminada ---")


if __name__ == "__main__":
    if "--una-vez" in sys.argv:
        ronda_de_monitoreo()
    else:
        print(f"Monitor iniciado. Revisando cada {INTERVALO_SEGUNDOS}s. Ctrl+C para detener.")
        while True:
            ronda_de_monitoreo()
            time.sleep(INTERVALO_SEGUNDOS)
