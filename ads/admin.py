from django.contrib import admin

from .models import (Ad, AdPhoto, Building, Category, Location, Match,
                     Message, ModerationAction, Notification, ReturnRequest, Review)

for model in (Ad, AdPhoto, Building, Category, Location, Match, Message,
              ModerationAction, Notification, ReturnRequest, Review):
    admin.site.register(model)
