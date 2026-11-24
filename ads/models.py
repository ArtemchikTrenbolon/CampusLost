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