import re
import unicodedata
from decimal import Decimal
from typing import Optional, Any

def clean_title(title: Optional[str]) -> str:
    """Limpia el título de un libro eliminando sufijos comerciales y artefactos."""
    if not title:
        return ""
        
    t = str(title).strip()
    # Eliminar etiquetas como [NOVEDAD], (EN STOCK), (OFERTA)
    t = re.sub(r'\[(NOVEDAD|OFERTA|AGOTADO|PREVENTA|REBAJA)\]', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\((OFERTA|PREVENTA|PROMOCION)\)', '', t, flags=re.IGNORECASE)
    # Normalizar espacios múltiples
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def clean_price(price_input: Any) -> Decimal:
    """Convierte cualquier formato de precio en Bolivianos a Decimal(10, 2)."""
    if price_input is None:
        return Decimal("0.00")
        
    if isinstance(price_input, (int, float, Decimal)):
        return Decimal(str(round(float(price_input), 2)))
        
    p_str = str(price_input).strip().upper()
    # Quitar símbolos de moneda como Bs, Bs., BOB, $, BOB., etc.
    p_str = re.sub(r'(BS\.?|BOB|BOB\.?|\$)', '', p_str)
    p_str = p_str.replace('.-', '')
    p_str = p_str.strip()
    
    # Manejar formatos 120,50 o 1.250,00 vs 120.50
    if ',' in p_str and '.' in p_str:
        if p_str.find('.') < p_str.find(','):
            # Formato europeo/latino: 1.250,00
            p_str = p_str.replace('.', '').replace(',', '.')
        else:
            # Formato anglosajón: 1,250.00
            p_str = p_str.replace(',', '')
    elif ',' in p_str:
        p_str = p_str.replace(',', '.')
        
    # Extraer primer número decimal
    match = re.search(r'([0-9]+(?:\.[0-9]+)?)', p_str)
    if match:
        try:
            return Decimal(match.group(1)).quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0.00")
            
    return Decimal("0.00")

def clean_author(author: Optional[str]) -> Optional[str]:
    """Limpia el nombre del autor eliminando prefijos habituales."""
    if not author:
        return None
    a = str(author).strip()
    a = re.sub(r'^(Autor|Por|Escrito por|Autores):\s*', '', a, flags=re.IGNORECASE)
    # Manejar formato "Apellido, Nombre"
    if ',' in a and len(a.split(',')) == 2:
        parts = a.split(',')
        if len(parts[0].strip().split()) <= 2 and len(parts[1].strip().split()) <= 2:
            a = f"{parts[1].strip()} {parts[0].strip()}"
    a = re.sub(r'\s+', ' ', a)
    return a.strip() if a.strip() else None

def normalize_for_search(text: str) -> str:
    """Normaliza para búsquedas insensibles a mayúsculas, tildes y signos."""
    if not text:
        return ""
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return re.sub(r'\s+', ' ', text).strip()
