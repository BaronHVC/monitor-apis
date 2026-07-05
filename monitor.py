# ============================================================
# MONITOR DE APIs - Proyecto de aprendizaje
# ============================================================
# Qué hace:
#   1. Revisa cada cierto tiempo si una lista de APIs responde
#   2. Mide cuánto tarda cada una en responder
#   3. Guarda todo en un archivo de log (monitor.log)
#   4. Si una API falla, reintenta y muestra una ALERTA
#
# Cómo usarlo:
#   python monitor.py            -> vigila para siempre (Ctrl+C para parar)
#   python monitor.py --una-vez  -> hace una sola ronda (para probar)
# ============================================================

import logging
import sys
import time

import requests

# ---------- CONFIGURACIÓN (puedes editar esto) ----------

# Las APIs que quieres vigilar. Agrega o quita las que gustes.
URLS = [
    "https://api.github.com",              # API pública de GitHub
    "https://pokeapi.co/api/v2/pokemon/1", # API pública de Pokémon
]

INTERVALO_SEGUNDOS = 300   # cada cuánto revisar (300 = 5 minutos)
TIMEOUT_SEGUNDOS = 5       # cuánto esperar antes de considerar que no responde
REINTENTOS = 2             # cuántas veces reintentar antes de alertar

# ---------- CONFIGURACIÓN DE LOGS ----------
# Guarda los mensajes en monitor.log Y los muestra en pantalla.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("monitor.log", encoding="utf-8"),
        logging.StreamHandler(),  # también imprime en consola
    ],
)


def revisar_api(url: str) -> bool:
    """Hace una petición GET a la URL y registra el resultado.

    Devuelve True si la API respondió bien, False si falló.
    """
    try:
        inicio = time.time()
        respuesta = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
        duracion = time.time() - inicio

        if respuesta.status_code == 200:
            logging.info(f"OK {url} status={respuesta.status_code} tiempo={duracion:.2f}s")
            return True
        else:
            logging.warning(f"RESPUESTA RARA {url} status={respuesta.status_code}")
            return False

    except requests.exceptions.Timeout:
        logging.error(f"TIMEOUT {url} no respondió en {TIMEOUT_SEGUNDOS}s")
        return False
    except requests.exceptions.RequestException as error:
        logging.error(f"NO RESPONDE {url} error={error}")
        return False


def revisar_con_reintentos(url: str) -> None:
    """Revisa una API y, si falla, reintenta antes de alertar."""
    for intento in range(1, REINTENTOS + 2):  # intento inicial + reintentos
        if revisar_api(url):
            return  # todo bien, no hay nada más que hacer
        if intento <= REINTENTOS:
            logging.info(f"Reintentando {url} (intento {intento + 1})...")
            time.sleep(2)  # pequeña pausa antes de reintentar

    # Si llegamos aquí, falló todos los intentos -> ALERTA
    alerta = f"🚨 ALERTA: {url} sigue fallando después de {REINTENTOS + 1} intentos"
    logging.critical(alerta)
    # Más adelante puedes reemplazar esto por un correo o mensaje de Telegram


def ronda_de_monitoreo() -> None:
    """Revisa todas las APIs de la lista una vez."""
    logging.info(f"--- Iniciando ronda de monitoreo ({len(URLS)} APIs) ---")
    for url in URLS:
        revisar_con_reintentos(url)
    logging.info("--- Ronda terminada ---")


if __name__ == "__main__":
    if "--una-vez" in sys.argv:
        # Modo de prueba: una sola ronda y termina
        ronda_de_monitoreo()
    else:
        # Modo vigilante: rondas infinitas cada INTERVALO_SEGUNDOS
        print(f"Monitor iniciado. Revisando cada {INTERVALO_SEGUNDOS}s. Ctrl+C para detener.")
        while True:
            ronda_de_monitoreo()
            time.sleep(INTERVALO_SEGUNDOS)
