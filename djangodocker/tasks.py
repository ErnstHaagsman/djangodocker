from .celery import app

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from djangodocker.models import TodoUser


@app.task
def send_confirmation_email(email):
    new_user = TodoUser.objects.get(email=email)

    email_context = {
        'url': settings.URL,
        'user': new_user
    }

    message = EmailMultiAlternatives(
        'Thank you for registering for Todo',
        render_to_string('djangodocker/confirm_email.txt', email_context),
        'noreply@todo.ernsthaagsman.com',
        [new_user.email]
    )
    message.attach_alternative(
        render_to_string('djangodocker/confirm_email.html', email_context),
        'text/html'
    )
    message.send()
