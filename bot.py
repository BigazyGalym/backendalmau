import os
import django
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Django настройки
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from products.models import Product

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Это бот для работы с товарами.')

async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    products = Product.objects.all()
    if products.exists():
        text = '\n'.join([f"{p.name} - {p.price} тг" for p in products])
    else:
        text = "Нет товаров."
    await update.message.reply_text(text)

def main():
    # Создаем объект приложения с токеном
    application = ApplicationBuilder().token("7864276086:AAG4HSa9MfHQBAgzTlhKRK6nJt-Wb0J9SgE").build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_products))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
