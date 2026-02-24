import logging
import os
import tempfile
import random
import time
import string
import piexif
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ChatAction

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Функция для генерации случайной строки (для метаданных)
def get_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def safe_unlink(path: str, attempts: int = 30, delay_seconds: float = 0.25) -> None:
    for i in range(attempts):
        try:
            os.unlink(path)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            if i == attempts - 1:
                return
            time.sleep(delay_seconds)

# Уникализация фото через метаданные
def unique_photo_metadata(input_path, output_path):
    # Очистка и замена EXIF
    zeroth_ifd = {piexif.ImageIFD.Make: get_random_string(8),
                  piexif.ImageIFD.Software: "Mobile Editor v1.2",
                  piexif.ImageIFD.DateTime: "2023:10:12 10:20:30"}
    exif_dict = {"0th": zeroth_ifd}
    exif_bytes = piexif.dump(exif_dict)
    
    # Сохраняем файл с новыми метаданными
    from PIL import Image
    img = Image.open(input_path)
    img.save(output_path, exif=exif_bytes)
    img.close()

# Обработка фото (отправка файлом/архивом)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)
    photo_file = await update.message.photo[-1].get_file()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tf_in:
        await photo_file.download_to_drive(tf_in.name)
        tf_out_path = tf_in.name.replace('.jpg', '_unique.jpg')
        
        try:
            unique_photo_metadata(tf_in.name, tf_out_path)
            with open(tf_out_path, 'rb') as doc:
                # Отправляем именно как документ (архивный вид)
                await update.message.reply_document(document=doc, filename=f"unique_{get_random_string(5)}.jpg")
        except Exception as e:
            logging.error(f"Ошибка обработки фото: {e}")
            await update.message.reply_text("Фото не удалось обработать.")
        finally:
            safe_unlink(tf_in.name)
            safe_unlink(tf_out_path)

# Обработка видео (уникализация через пересборку)
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action=ChatAction.UPLOAD_VIDEO)
    video = update.message.video or update.message.document
    video_file = await video.get_file()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tf_in:
        await video_file.download_to_drive(tf_in.name)
        tf_out = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tf_out.close()
        try:
            import ffmpeg
            ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
            ffprobe_path = os.getenv('FFPROBE_PATH', 'ffprobe')
            
            # Получаем длительность видео
            probe = ffmpeg.probe(tf_in.name, cmd=ffprobe_path)
            duration = float(probe['format']['duration'])
            end_time = max(duration - 0.2, 0.1)
            (
                ffmpeg
                .input(tf_in.name)
                .output(tf_out.name, ss=0, t=end_time, codec='copy')
                .run(overwrite_output=True, quiet=True, cmd=ffmpeg_path)
            )
            with open(tf_out.name, 'rb') as out_vid:
                input_file = InputFile(
                    out_vid,
                    filename=f"unique_{get_random_string(5)}.mp4",
                )
                await update.message.reply_document(
                    document=input_file,
                    caption="Видео уникализировано (обрезано на 0.2 сек)",
                    disable_content_type_detection=True
                )
        except Exception as file_err:
            logging.error(f"Ошибка обработки/отправки видео: {file_err}")
            await update.message.reply_text("Видео не удалось обработать или отправить.")
        finally:
            safe_unlink(tf_in.name)
            safe_unlink(tf_out.name)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Бот готов! Пришли фото (отправлю файлом) или видео.')

def main():
    # ЗАМЕНИ ТОКЕН НА СВОЙ (лучше использовать переменные окружения)
    TOKEN = None
    try:
        import config  # type: ignore
        TOKEN = getattr(config, '8695733465:AAFgZN9SLasbfxzYbzobF9ldKgOaEVYIxvg', None)
    except Exception:
        TOKEN = None
    if not TOKEN:
        TOKEN = os.getenv('8695733465:AAFgZN9SLasbfxzYbzobF9ldKgOaEVYIxvg')
    if not TOKEN:
        raise RuntimeError('8695733465:AAFgZN9SLasbfxzYbzobF9ldKgOaEVYIxvg')
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()