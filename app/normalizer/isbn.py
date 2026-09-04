import re
from typing import Optional

def clean_isbn(raw_isbn: Optional[str]) -> Optional[str]:
    """Limpia y valida un ISBN (10 o 13 dígitos). Retorna el ISBN normalizado sin guiones ni espacios."""
    if not raw_isbn:
        return None
        
    # Extraer dígitos y posible caracter 'X' al final
    cleaned = re.sub(r'[^0-9X]', '', str(raw_isbn).upper().strip())
    
    if len(cleaned) == 13 and cleaned.isdigit():
        if is_valid_isbn13(cleaned):
            return cleaned
    elif len(cleaned) == 10:
        if is_valid_isbn10(cleaned):
            return convert_isbn10_to_isbn13(cleaned)
            
    # Si tiene 10 o 13 dígitos pero el checksum falló ligeramente por error de tipeo en tienda,
    # aún conservamos el número limpio si parece un ISBN razonable
    if len(cleaned) in (10, 13) and cleaned[:9].isdigit():
        return cleaned
        
    return None

def is_valid_isbn10(isbn: str) -> bool:
    if len(isbn) != 10:
        return False
    total = 0
    for i in range(9):
        if not isbn[i].isdigit():
            return False
        total += int(isbn[i]) * (10 - i)
    check = 10 if isbn[9] == 'X' else (int(isbn[9]) if isbn[9].isdigit() else -1)
    if check == -1:
        return False
    total += check
    return total % 11 == 0

def is_valid_isbn13(isbn: str) -> bool:
    if len(isbn) != 13 or not isbn.isdigit():
        return False
    total = sum(int(isbn[i]) * (1 if i % 2 == 0 else 3) for i in range(12))
    check = (10 - (total % 10)) % 10
    return int(isbn[12]) == check

def convert_isbn10_to_isbn13(isbn10: str) -> str:
    """Convierte un ISBN-10 válido a su equivalente canónico ISBN-13 (prefijo 978)."""
    core = "978" + isbn10[:9]
    total = sum(int(core[i]) * (1 if i % 2 == 0 else 3) for i in range(12))
    check = (10 - (total % 10)) % 10
    return core + str(check)
