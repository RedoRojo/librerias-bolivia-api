import time
import logging
from typing import List, Dict, Any, Generator, Optional
import httpx
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper")

class BaseScraper:
    """Clase base para todos los adaptadores de tiendas y librerías."""

    def __init__(self, store_name: str, base_url: str):
        self.store_name = store_name
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-BO,es;q=0.9,en;q=0.8"
        }
        self.client = httpx.Client(
            headers=self.headers,
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
            verify=False
        )

    def sleep(self):
        """Pausa cortés entre peticiones para respetar la infraestructura de la librería."""
        time.sleep(settings.RATE_LIMIT_DELAY)

    def scrape(self, max_items: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """Método generador que deben implementar las subclases."""
        raise NotImplementedError

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
