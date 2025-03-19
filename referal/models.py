import uuid

from django.db import models


class ReferalUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_account = models.ForeignKey(
        "accounts.UserAccounts",
        on_delete=models.CASCADE,
        related_name="referal_user",
        verbose_name="Аккаунт пользователя"
    )

    # TODO: дописать поля у сущности