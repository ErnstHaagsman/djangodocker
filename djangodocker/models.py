from django.db import models
from django.conf import settings
from django.db.models import CASCADE


class Todo(models.Model):
    todo_text = models.CharField(max_length=400)
    created_at = models.DateTimeField(auto_now=True)
    done = models.BooleanField(default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE)
