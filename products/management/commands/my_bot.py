from django.core.management.base import BaseCommand
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, LabeledPrice, PreCheckoutQuery, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, PreCheckoutQueryHandler
from products.models import Product
from asgiref.sync import sync_to_async
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Telegram бот для работы с товарами'

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start."""
        await update.message.reply_text(
            'Привет! Это бот для работы с товарами. Используй /products для просмотра товаров.'
        )

    @sync_to_async
    def get_products(self):
        """Асинхронное получение товаров из базы данных."""
        return Product.objects.all()

    async def products(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /products."""
        try:
            products = await self.get_products()

            if products.exists():
                # Создание кнопок для продуктов
                keyboard = [
                    [InlineKeyboardButton(f"{product.name} - {product.price} ТГ", callback_data=f"product_{product.id}")]
                    for product in products
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Список товаров:", reply_markup=reply_markup)
            else:
                await update.message.reply_text("Нет доступных товаров.")
        except Exception as e:
            logger.error(f"Ошибка при получении продуктов: {e}")
            await update.message.reply_text("Произошла ошибка при загрузке товаров.")

    @sync_to_async
    def get_product_by_id(self, product_id):
        """Асинхронное получение конкретного товара по ID."""
        return Product.objects.get(id=product_id)

    async def product_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик для деталей товара."""
        query = update.callback_query
        await query.answer()

        product_id = query.data.split("_")[1]

        try:
            product = await self.get_product_by_id(product_id)

            # Отправка деталей продукта с видео и изображениями
            text = f"Название: {product.name}\nЦена: {product.price} ТГ"
            if hasattr(product, "video_url") and product.video_url:  # Если в модели есть поле video_url
                await query.message.reply_video(product.video_url, caption=text)
            elif hasattr(product, "image_url") and product.image_url:  # Если в модели есть поле image_url
                await query.message.reply_photo(product.image_url, caption=text)
            else:
                await query.edit_message_text(text=text)
        except Product.DoesNotExist:
            await query.edit_message_text(text="Товар не найден.")

    async def all_products_with_video_and_images(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик для отправки всех товаров с видео и изображениями."""
        try:
            products = await self.get_products()

            if products.exists():
                media_group = []
                for product in products:
                    if hasattr(product, "video_url") and product.video_url:
                        media_group.append(InputMediaVideo(product.video_url, caption=f"{product.name} - {product.price} ТГ"))
                    elif hasattr(product, "image_url") and product.image_url:
                        media_group.append(InputMediaPhoto(product.image_url, caption=f"{product.name} - {product.price} ТГ"))

                if media_group:
                    await update.message.reply_media_group(media_group)
                else:
                    await update.message.reply_text("Нет доступных видео или изображений для продуктов.")
            else:
                await update.message.reply_text("Нет доступных товаров.")
        except Exception as e:
            logger.error(f"Ошибка при отправке видео или изображений: {e}")
            await update.message.reply_text("Произошла ошибка при загрузке данных.")

    async def initiate_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик для инициализации оплаты товара."""
        query = update.callback_query
        await query.answer()

        product_id = query.data.split("_")[1]

        try:
            product = await self.get_product_by_id(product_id)

            # Создание счета для товара
            title = product.name
            description = f"Описание товара: {product.name}"
            payload = f"product_{product.id}"
            provider_token = 'YOUR_PROVIDER_TOKEN'  # Токен для обработки платежей
            start_parameter = 'start_parameter'
            currency = 'KZT'
            prices = [LabeledPrice(product.name, product.price * 100)]  # Цена в теньге, умноженная на 100 для копеек

            await update.message.reply_invoice(
                title=title,
                description=description,
                payload=payload,
                provider_token=provider_token,
                start_parameter=start_parameter,
                currency=currency,
                prices=prices,
                is_flexible=False  # Не гибкий платеж
            )
        except Product.DoesNotExist:
            await query.edit_message_text(text="Товар не найден.")

    async def pre_checkout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик для подтверждения предварительной оплаты."""
        query = update.pre_checkout_query
        if query.invoice_payload != "product":
            await query.answer(ok=False)
        else:
            await query.answer(ok=True)

    def handle(self, *args, **kwargs):
        """Запуск Telegram-бота."""
        application = ApplicationBuilder().token('7864276086:AAG4HSa9MfHQBAgzTlhKRK6nJt-Wb0J9SgE').build()

        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.product_detail))
        application.add_handler(CommandHandler("products", self.products))
        application.add_handler(CommandHandler("all_videos", self.all_products_with_video_and_images))  # Команда для всех видео и изображений
        application.add_handler(CommandHandler("pay", self.initiate_payment))  # Команда для инициализации платежа
        application.add_handler(PreCheckoutQueryHandler(self.pre_checkout_callback))  # Используем только PreCheckoutQueryHandler

        # Запускаем бота
        logger.info("Бот запущен!")
        application.run_polling()
