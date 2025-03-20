import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.postgres.fields import ArrayField


from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, login, password=None, **extra_fields):
        if not login:
            raise ValueError('User must have a login')
        user = self.model(login=login, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(login, password, **extra_fields)

class UserAccounts(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    patronymic_name = models.CharField(max_length=255, blank=True, null=True)
    login = models.CharField(max_length=30, unique=True)
    avatar = models.CharField(max_length=255, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)

    objects = UserManager()

    is_active = models.BooleanField(blank=True, default=False)
    is_confirmed = models.BooleanField(default=False)
    in_consideration = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = []

    groups = models.ManyToManyField(
        'auth.Group', 
        related_name='useraccounts_set',  # Unique related name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', 
        related_name='useraccounts_permissions',  # Unique related name
        blank=True,
    )

    def __str__(self):
        return self.login



class TelegramBotSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class NotificationType(models.TextChoices):
        SYSTEM = 'SYSTEM'
        TRADER = 'TRADER'
        SUPPORT = 'SUPPORT'
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices)
    bot_token = models.CharField(max_length=255, verbose_name='Токен телеграм бота')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность токенов телеграм бота"
        verbose_name_plural = "Сущность токенов телеграм бота"