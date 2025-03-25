import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission

class UserManager(BaseUserManager):
    def create_user(self, login, password=None, role='MERCHANT', **extra_fields):
        if not login:
            raise ValueError('User must have a login')
        extra_fields.setdefault('is_active', True)  # Активируем пользователя по умолчанию
        user = self.model(login=login, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', UserAccounts.Role.ADMIN)  # Роль ADMIN
        return self.create_user(login, password, **extra_fields)

class UserAccounts(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        MERCHANT = 'MERCHANT', 'Merchant'
        TRADER = 'TRADER', 'Trader'
        SUPPORT = 'SUPPORT', 'Support'

    id = models.AutoField(primary_key=True)
    login = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    patronymic_name = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.CharField(max_length=255, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)

    groups = models.ManyToManyField(Group, related_name="user_accounts_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="user_accounts_permissions", blank=True)

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MERCHANT,  # По умолчанию Мерчант
    )

    is_active = models.BooleanField(default=True)  # По умолчанию пользователь активен
    is_confirmed = models.BooleanField(default=False)  # Подтвержден ли пользователь
    in_consideration = models.BooleanField(default=True)  # На рассмотрении?
    is_staff = models.BooleanField(default=False)  # Доступ к админке Django

    objects = UserManager()

    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.login} ({self.get_role_display()})"


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
