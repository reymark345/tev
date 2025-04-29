def get_finance_db_alias(dp_year: str) -> str:
    if dp_year == "2023":
        return 'finance'
    elif dp_year == "2024":
        return 'finance_2024'
    elif dp_year == "2025":
        return 'finance_2025'
    else:
        return 'finance_2025'