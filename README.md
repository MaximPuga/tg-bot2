# Telegram Bot - Уникализация фото и видео

Бот принимает фото и видео, уникализирует их и отправляет как документы.

## Функции

- **Фото**: изменяет EXIF метаданные, отправляет как `.jpg` документ
- **Видео**: обрезает 0.2 сек через ffmpeg, отправляет как `.mp4` документ

## Установка

```bash
pip install -r requirements.txt
```

## Настройка токена

### Вариант 1: Через config.py (локально)
Создай файл `config.py` рядом с `main.py`:
```python
TELEGRAM_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"
```

### Вариант 2: Через переменные окружения (для хостинга)
```bash
export TELEGRAM_TOKEN="ВАШ_ТОКЕН_ЗДЕСЬ"
```

## Запуск

```bash
python main.py
```

## Деплой на хостинг

### Railway / Render
- Подключи GitHub репозиторий
- Добавь Environment Variable: `TELEGRAM_TOKEN`
- Build: `pip install -r requirements.txt`
- Start: `python main.py`

### Требования на сервере
- Python 3.10+
- FFmpeg (для обработки видео)

## Зависимости
- python-telegram-bot
- Pillow
- piexif
- ffmpeg-python
