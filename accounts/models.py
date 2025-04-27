from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password


class BirthCitySecret(models.Model):
    """
    Stores the answer to the single security question:
    ‘In what city were you born?’
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    answer_hashed = models.CharField(max_length=128)

    # helper methods
    def set_answer(self, raw_answer: str) -> None:
        self.answer_hashed = make_password(raw_answer.strip())

    def check_answer(self, raw_answer: str) -> bool:
        return check_password(raw_answer.strip(), self.answer_hashed)

    def __str__(self) -> str:
        return f'{self.user.username} – birth-city secret'
