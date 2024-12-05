from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True, null=True)  # Ссылка на изображение
    video_url = models.URLField(blank=True, null=True)  # Ссылка на видео

    def __str__(self):
        return self.name
