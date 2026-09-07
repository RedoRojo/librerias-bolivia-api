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

                    # Extraer ISBN del SKU o barcode
                    isbn = raw_sku if raw_sku and len(str(raw_sku).replace('-', '')) in (10, 13) else None
                    if not isbn:
                        isbn_re = re.compile(r'(97[89]\d{10})')
                        for img in images:
                            m = isbn_re.search(img.get("src", ""))
                            if m:
                                isbn = m.group(1)
                                break
                        if not isbn and raw_body:
                            m = isbn_re.search(raw_body)
                            if m:
                                isbn = m.group(1)

                    # En Shopify, vendor suele ser la editorial
                    vendor = p.get("vendor")
                    publisher = vendor if vendor and vendor.lower() not in (self.store_name.lower(), "generico", "default") else None

                    # Limpieza de título y autor (manejo de formatos como 'TITULO | AUTOR')
                    raw_title = html.unescape(p.get("title", "")).strip()
                    title = raw_title
                    author = None

                    if "|" in raw_title:
                        parts = raw_title.split("|", 1)
                        title = parts[0].strip()
                        author_part = parts[1].strip()
                        if author_part and author_part.lower() not in ("varios", "varios autores", "diversos", "n/a"):
                            author = author_part.title()

                    # Limpiar sufijos promocionales de título (ej: '. REBAJA 40 BS')
                    title = re.sub(r'\s*\.?\s*REBAJA\s*\d+\s*BS\.?', '', title, flags=re.IGNORECASE).strip()

                    # Si el autor o editorial están en body_html con formato estructurado
                    if raw_body and (not author or not publisher):
                        if not author:
                            m_auth = re.search(r'AUTOR:\s*([^-\n<]+)', raw_body, re.IGNORECASE)
                            if m_auth:
                                auth_text = m_auth.group(1).strip()
                                if auth_text.lower() not in ("varios", "varios autores"):
                                    author = auth_text.title()
                        if not publisher:
                            m_pub = re.search(r'EDITORIAL:\s*([^-\n<]+)', raw_body, re.IGNORECASE)
                            if m_pub:
                                publisher = m_pub.group(1).strip().title()

                    item = {
                        "title": title,
                        "author": author,
                        "publisher": publisher,
                        "price": price,
                        "is_in_stock": is_in_stock,
                        "stock_label": "En stock" if is_in_stock else "Agotado",
                        "product_url": f"{self.base_url}/products/{p.get('handle')}",
                        "cover_image_url": cover_image_url,
                        "synopsis": synopsis,
                        "isbn": str(isbn) if isbn else None,
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
