from datetime import date, datetime
from typing import Union


def formatar_real(valor: Union[float, int]) -> str:
    """Formata valor numérico como moeda brasileira. Ex: 1234567.89 → R$ 1.234.567,89"""
    if valor is None:
        return "R$ 0,00"
    negativo = valor < 0
    valor = abs(float(valor))
    inteiro = int(valor)
    centavos = round((valor - inteiro) * 100)
    parte_inteira = f"{inteiro:,}".replace(",", ".")
    resultado = f"R$ {parte_inteira},{centavos:02d}"
    return f"-{resultado}" if negativo else resultado


def formatar_data(dt: Union[date, datetime, str, None]) -> str:
    """Formata data no padrão brasileiro DD/MM/AAAA."""
    if dt is None:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime("%d/%m/%Y")


def formatar_percentual(valor: float) -> str:
    """Formata valor como percentual. Ex: 0.8523 → 85,23%"""
    if valor is None:
        return "0,00%"
    return f"{valor * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
