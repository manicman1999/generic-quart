def formatAmount(amount: float) -> str:
    if amount.is_integer():
        return f"{int(amount)}"
    return f"{amount}".rstrip('0').rstrip('.')