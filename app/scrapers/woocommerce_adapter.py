import re
import html
from decimal import Decimal
from typing import Generator, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, logger

class WooCommerceAdapter(BaseScraper):
    """Adaptador para tiendas WooCommerce (Plural, Encantalibros, Lectura, Baúl del Libro, Kipus, etc.)."""

    def scrape(self, max_items: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        # Intentar primero la Store API moderna (/wp-json/wc/store/v1/products)
        success = False
        try:
            test_resp = self.client.get(f"{self.base_url}/wp-json/wc/store/v1/products?per_page=1")
            if test_resp.status_code == 200:
                success = True
                yield from self._scrape_store_api(max_items)
        except Exception as e:
            logger.debug(f"[{self.store_name}] Store API no disponible: {e}")

        # Si la Store API no está disponible, usar el raspador de catálogo HTML estándar de WooCommerce
        if not success:
            logger.info(f"[{self.store_name}] Usando extractor de catálogo HTML de WooCommerce...")
            yield from self._scrape_html_catalog(max_items)

    def _scrape_store_api(self, max_items: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        page = 1
        yielded_count = 0

        while True:
            url = f"{self.base_url}/wp-json/wc/store/v1/products?per_page=50&page={page}"
            logger.info(f"[{self.store_name}] Consultando Store API página {page}")
            
            try:
                resp = self.client.get(url)
                if resp.status_code != 200:
                    break

                products = resp.json()
                if not products or not isinstance(products, list):
                    break

                for p in products:
                    # En WooCommerce Store API, los precios vienen en centavos (ej: 4000 = 40.00 Bs)
                    prices = p.get("prices", {})
                    raw_price = prices.get("price") or p.get("price")
                    if raw_price and str(raw_price).isdigit():
                        price = str(Decimal(int(raw_price)) / Decimal(100))
                    else:
                        price = str(raw_price or "0.00")

                    is_in_stock = bool(p.get("is_in_stock", True))
                    
                    # Extraer imágenes
                    images = p.get("images", [])
                    cover_image_url = images[0].get("src") if images else None
                    
                    # Extraer sinopsis limpia
                    raw_desc = p.get("description") or p.get("short_description") or ""
                    soup = BeautifulSoup(raw_desc, "html.parser")
                    synopsis = soup.get_text(separator=" ", strip=True)[:1500]

                    # Revisar atributos para editorial o autor
                    editorial = None
                    author = None
                    for attr in p.get("attributes", []):
                        attr_name = attr.get("name", "").lower()
                        terms = attr.get("terms", [])
                        term_names = [t.get("name") for t in terms if t.get("name")]
                        val = ", ".join(term_names)
                        if "editorial" in attr_name or "sello" in attr_name:
                            editorial = val
                        elif "autor" in attr_name or "escritor" in attr_name:
                            author = val

                    # Revisar tags
                    for tag in p.get("tags", []):
                        tag_name = tag.get("name", "")
                        if "editorial" in tag_name.lower():
                            editorial = tag_name.replace("Editorial:", "").strip()

                    sku = p.get("sku")
                    isbn = sku if sku and len(str(sku).replace('-', '')) in (10, 13) else None

                    item = {
                        "title": html.unescape(p.get("name", "")),
                        "author": author,
                        "editorial": editorial,
                        "price": price,
                        "is_in_stock": is_in_stock,
                        "stock_label": "En stock" if is_in_stock else "Agotado",
                        "product_url": p.get("permalink", ""),
                        "cover_image_url": cover_image_url,
                        "synopsis": synopsis,
                        "isbn": isbn,
                        "raw_sku": sku
                    }

                    yield item
                    yielded_count += 1
                    if max_items and yielded_count >= max_items:
                        return

                page += 1
                self.sleep()

            except Exception as e:
                logger.error(f"[{self.store_name}] Error en Store API página {page}: {e}")
                break

    def _scrape_html_catalog(self, max_items: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        page = 1
        yielded_count = 0
        base_paths = ["/tienda/page/", "/catalogo/page/", "/shop/page/"]
        
        # Probar cuál ruta responde
        active_path = None
        for bp in base_paths:
            test_url = f"{self.base_url}{bp}1/"
            try:
                r = self.client.get(test_url)
                if r.status_code == 200 and ("product" in r.text.lower() or "woocommerce" in r.text.lower()):
                    active_path = bp
                    break
            except Exception:
                continue
                
        if not active_path:
            active_path = "/tienda/page/"

        while True:
            url = f"{self.base_url}{active_path}{page}/"
            logger.info(f"[{self.store_name}] Consultando catálogo HTML página {page}: {url}")

            try:
                resp = self.client.get(url)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                product_cards = soup.select("li.product, div.product-small, .woocommerce-loop-product")
                if not product_cards:
                    break

                for card in product_cards:
                    # Título y enlace
                    title_elem = card.select_one(".woocommerce-loop-product__title, h2, h3, .product-title a")
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)

                    link_elem = card.select_one("a.woocommerce-LoopProduct-link, a")
                    product_url = link_elem.get("href") if link_elem else self.base_url

                    # Precio
                    price_elem = card.select_one(".price .amount, .price ins .amount, .price")
                    price = price_elem.get_text(strip=True) if price_elem else "0.00"

                    # Imagen
                    img_elem = card.select_one("img")
                    img_url = img_elem.get("src") or img_elem.get("data-src") if img_elem else None

                    # Stock
                    is_in_stock = "outofstock" not in card.get("class", [])

                    item = {
                        "title": html.unescape(title),
                        "author": None,
                        "editorial": None,
                        "price": price,
                        "is_in_stock": is_in_stock,
                        "stock_label": "En stock" if is_in_stock else "Agotado",
                        "product_url": product_url,
                        "cover_image_url": img_url,
                        "synopsis": "",
                        "isbn": None,
                        "raw_sku": None
                    }

                    yield item
                    yielded_count += 1
                    if max_items and yielded_count >= max_items:
                        return

                page += 1
                self.sleep()

            except Exception as e:
                logger.error(f"[{self.store_name}] Error en catálogo HTML página {page}: {e}")
                break
