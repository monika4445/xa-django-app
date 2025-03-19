from django.contrib import admin

from .models import UserAccounts, TelegramBotSettings


admin.site.register(UserAccounts)
admin.site.register(TelegramBotSettings)
