def split_text(text, max_length=4000):
    """Разбивает текст на части, чтобы не превысить лимит Telegram."""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    while len(text) > max_length:
        # Ищем ближайший перенос строки, чтобы не резать слова
        split_at = text.rfind('\n', 0, max_length)
        if split_at == -1: # Если нет переносов, режем жестко
            split_at = max_length
        
        parts.append(text[:split_at])
        text = text[split_at:].lstrip() # Убираем пробелы в начале куска
    
    if text:
        parts.append(text)
    return parts