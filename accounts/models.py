import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.core.exceptions import ValidationError
from django.db import models

from utils.password_validation import validator
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
  def create_user(self, login, password, first_name, last_name, role='MERCHANT', **extra_fields):
    if not login:
      raise ValueError(_('User must have a login.'))
    if not password:
      raise ValueError(_('User must have a password.'))
    if not first_name:
      raise ValueError(_('First name is required.'))
    if not last_name:
      raise ValueError(_('Last name is required.'))

    if self.model.objects.filter(login=login).exists():
      raise ValidationError(_('A user with this login already exists.'))

    extra_fields.setdefault('is_active', True)
    extra_fields.setdefault('is_confirmed', False)
    extra_fields.setdefault('in_consideration', True)

    try:
      validator.validate(password)
    except ValidationError as e:
      raise ValueError(f"Password validation failed: {', '.join(e.messages)}")

    user = self.model(login=login, first_name=first_name, last_name=last_name, role=role, **extra_fields)
    user.set_password(password)
    user.save(using=self._db)

    return user

  def create_superuser(self, login, password, first_name, last_name, **extra_fields):
    extra_fields.setdefault('is_superuser', True)
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('role', UserAccounts.Role.ADMIN)  # Assign ADMIN role

    return self.create_user(login, password, first_name, last_name, **extra_fields)

  # def create_superuser(self, login, password=None, **extra_fields):
  #   extra_fields.setdefault('is_superuser', True)
  #   extra_fields.setdefault('is_staff', True)
  #   extra_fields.setdefault('is_active', True)
  #   extra_fields.setdefault('role', UserAccounts.Role.ADMIN)  # Роль ADMIN
  #
  #   return self.create_user(login, password, **extra_fields)


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

  def deactivate_user(self):
    self.is_active = False
    self.save(update_fields=['is_active'])


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
