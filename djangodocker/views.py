from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404

from djangodocker.forms import TaskForm
from .models import Todo


def index(request):
    todos = Todo.objects.all()
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
