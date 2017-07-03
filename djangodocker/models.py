from django.db import models


class Todo(models.Model):
    todo_text = models.CharField(max_length=400)
    created_at = models.DateTimeField(auto_now=True)
    done = models.BooleanField(default=False)