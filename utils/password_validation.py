import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class CustomPasswordValidator:
  def validate(self, password: str, user=None):
    if not re.match(r"^(?=.*?[A-Z])(?=.*?[a-z])"
                    r"(?=.*?[0-9])(?=.*?[#?!@$%^&*-./]).{8,}$", password):
      raise ValidationError("Password must be at least 8 characters long and "
                            "contain at least one uppercase letter, one lowercase letter, "
                            "one number, and one special character.")

    if " " in password:
      raise ValidationError("Password can't contain spaces..")

  def get_help_text(self) -> str:
    return _(
      "Your password must contain at least 8 characters, "
      "one uppercase letter, one lowercase letter, one number, "
      "one special character, and no spaces."
    )


validator = CustomPasswordValidator()
