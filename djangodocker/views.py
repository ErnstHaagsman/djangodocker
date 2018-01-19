from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse

from djangodocker.forms import TaskForm, TodoUserCreationForm
from djangodocker.settings import AUTH_USER_MODEL
from .models import Todo


@login_required
def index(request):
    todos = Todo.objects.filter(author=request.user)
    task_form = TaskForm()
    context = {
        'todos': todos,
        'task_form': task_form
    }
    return render(request, 'djangodocker/index.html', context)


def add_todo(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            new_todo = Todo()
            new_todo.todo_text = form.cleaned_data['todo_text']
            new_todo.author = request.user
            new_todo.save()

    return HttpResponseRedirect('/')


def toggle_todo(request, todo_id):
    todo = get_object_or_404(Todo, pk=todo_id)
    todo.done = not todo.done
    todo.save()
    return JsonResponse({
        'id': todo.id,
        'done': todo.done
    })


def signup(request):
    if request.method == 'POST':
        form = TodoUserCreationForm(request.POST)
        if form.is_valid():
            new_user = get_user_model().objects.create_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                display_name=form.cleaned_data['display_name']
            )

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

            thanks_page_context = {
                'email': new_user.email
            }

            return render(request,
                          'djangodocker/registration_thanks.html',
                          thanks_page_context)


def confirm(request, confirmation_code):
    try:
        user = get_user_model().objects.get(confirmation_code=confirmation_code)
    except get_user_model().DoesNotExist:
        raise PermissionDenied()

    if user.is_confirmed:
        return HttpResponseRedirect(reverse('login'))

    user.is_confirmed = True
    user.save()

    login(request, user)

    return render (request,
                   'registration/confirm.html',
                   {})
