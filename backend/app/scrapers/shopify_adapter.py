import re
import html
from typing import Generator, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, logger

class ShopifyAdapter(BaseScraper):
    """Adaptador de alta velocidad para tiendas que usan Shopify (Kronos, El Bagallero Ilustrado)."""

    def scrape(self, max_items: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        page = 1
        yielded_count = 0

        while True:
            url = f"{self.base_url}/products.json?limit=250&page={page}"
            logger.info(f"[{self.store_name}] Consultando página {page}: {url}")
            
            try:
                resp = self.client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"[{self.store_name}] Código {resp.status_code} al consultar {url}")
                    break

                data = resp.json()
                products = data.get("products", [])
                if not products:
                    logger.info(f"[{self.store_name}] No hay más productos en la página {page}.")
                    break

                for p in products:
                    variants = p.get("variants", [{}])
                    first_variant = variants[0] if variants else {}
                    
                    # Extraer precio y disponibilidad
                    price = first_variant.get("price", "0.00")
                    is_in_stock = bool(first_variant.get("available", True))
                    raw_sku = first_variant.get("sku") or first_variant.get("barcode")
                    
                    # Extraer imagen
                    images = p.get("images", [])
                    cover_image_url = images[0].get("src") if images else None
                    
                    # Extraer descripción limpia
                    raw_body = p.get("body_html") or ""
                    synopsis = ""
                    if raw_body:
                        soup = BeautifulSoup(raw_body, "html.parser")
                        synopsis = soup.get_text(separator=" ", strip=True)[:1500]

                    # En Shopify, vendor suele ser la editorial o el autor
                    vendor = p.get("vendor")
                    product_type = p.get("product_type")

                    item = {
                        "title": html.unescape(p.get("title", "")),
                        "author": None,  # Se resolverá por normalizer o vendor
                        "publisher": vendor if vendor and vendor.lower() not in (self.store_name.lower(), "generico") else None,
                        "price": price,
                        "is_in_stock": is_in_stock,
                        "stock_label": "En stock" if is_in_stock else "Agotado",
                        "product_url": f"{self.base_url}/products/{p.get('handle')}",
                        "cover_image_url": cover_image_url,
                        "synopsis": synopsis,
                        "isbn": raw_sku if raw_sku and len(str(raw_sku).replace('-', '')) in (10, 13) else None,
                        "raw_sku": str(raw_sku) if raw_sku else None
                    }

                    yield item
                    yielded_count += 1
                    if max_items and yielded_count >= max_items:
                        return

                page += 1
                self.sleep()

            except Exception as e:
                logger.error(f"[{self.store_name}] Error en página {page}: {e}")
                break
