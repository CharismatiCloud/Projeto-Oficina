from datetime import datetime
from typing import Union

def format_brl_price(value: float):
    #Formata valores monetários para o padrão brasileiro (1.500,00).
    if value is None:
        return ""
    formatted = f"{value:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def format_brl_date(value: datetime):
    #Formata datas para o padrão brasileiro (DD/MM/YYYY HH:MM).
    if not value:
        return ""
    return value.strftime("%d/%m/%Y %H:%M")


def parse_brl_price(value: Union[str, float, int]) -> float:
    """
    Converte um valor vindo de planilha (string '1.500,75', 1500.75, 1500)
    para float Python usando a convenção BR:
    - remove pontos de milhar
    - troca vírgula decimal por ponto
    - valida número não negativo

    Levanta ValueError para entradas inválidas.
    """
    if value is None:
        raise ValueError("Preço vazio")
    # Se já vier como número, só valida
    if isinstance(value, (int, float)):
        v = float(value)
        if v < 0:
            raise ValueError("Preço negativo")
        return v

    s = str(value).strip()
    if not s:
        raise ValueError("Preço vazio")

    # Remove separadores de milhar e converte decimal
    s = s.replace(".", "").replace(",", ".")
    v = float(s)  # pode levantar ValueError
    if v < 0:
        raise ValueError("Preço negativo")
    return v