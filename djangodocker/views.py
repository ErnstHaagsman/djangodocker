from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404

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

            context = {
                'email': new_user.email
            }

            return render(request,
                          'djangodocker/registration_thanks.html',
                          context)
