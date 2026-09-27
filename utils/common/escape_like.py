def escape_like(value: str) -> str:
    if not value:
        return value
    value = value.replace('\\', '\\\\')
    value = value.replace('%', '\\%')
    value = value.replace('_', '\\_')
    return value
