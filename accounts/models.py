from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор'

    email = models.EmailField('Почта', unique=True)
    group_name = models.CharField('Учебная группа', max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_moderator(self):
        return self.role in (self.Role.MODERATOR, self.Role.ADMIN) or self.is_superuser