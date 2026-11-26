from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField('Название', max_length=80)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Building(models.Model):
    name = models.CharField('Название', max_length=120)
    address = models.CharField('Адрес', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Корпус'
        verbose_name_plural = 'Корпуса'

    def __str__(self):
        return self.name


class Location(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField('Место', max_length=120)  # «Аудитория Р-215», «Гардероб»

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        return f'{self.building}: {self.name}'


class Ad(models.Model):
    class Type(models.TextChoices):
        LOST = 'lost', 'Потеряно'
        FOUND = 'found', 'Найдено'

    class Status(models.TextChoices):
        PENDING = 'pending', 'На модерации'
        ACTIVE = 'active', 'Активно'
        IN_RETURN = 'in_return', 'В процессе возврата'
        RETURNED = 'returned', 'Возвращено'
        REMOVED = 'removed', 'Снято модератором'

    type = models.CharField(max_length=10, choices=Type.choices)
    title = models.CharField('Заголовок', max_length=150)
    description = models.TextField('Описание', blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    building = models.ForeignKey(Building, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    event_date = models.DateField('Дата потери / находки')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ads')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'

    def __str__(self):
        return f'[{self.get_type_display()}] {self.title}'


class AdPhoto(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='photos/')


class Match(models.Model):
    class Status(models.TextChoices):
        SUGGESTED = 'suggested', 'Предложено'
        DISMISSED = 'dismissed', 'Отклонено'
        CONFIRMED = 'confirmed', 'Подтверждено'

    lost_ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='matches_as_lost')
    found_ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='matches_as_found')
    score = models.PositiveSmallIntegerField()  # 0..100
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUGGESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lost_ad', 'found_ad')


class ReturnRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Запрошен'
        CONTACT = 'contact', 'Контакт установлен'
        COMPLETED = 'completed', 'Завершён'
        CANCELLED = 'cancelled', 'Отменён'

    lost_ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='returns_as_lost')
    found_ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='returns_as_found')
    initiator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='initiated_returns')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    finder_confirmed = models.BooleanField(default=False)
    owner_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class Message(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class Review(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='reviews_written')
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='reviews_received')
    rating = models.PositiveSmallIntegerField()  # 1..5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='notifications')
    text = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ModerationAction(models.Model):
    class Action(models.TextChoices):
        APPROVED = 'approved', 'Одобрено'
        REMOVED = 'removed', 'Снято'

    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='moderation_actions')
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=Action.choices)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)