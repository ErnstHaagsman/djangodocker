from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from djangodocker.forms import TaskForm, TodoUserCreationForm, ConfirmedEmailAuthenticationForm
from .models import Todo
from .tasks import send_confirmation_email


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


class Login(LoginView):
    """
    A combined login and signup form
    """

    authentication_form = ConfirmedEmailAuthenticationForm

    def get_context_data(self, **kwargs):
        form = None
        if 'form' in kwargs:
            form = kwargs['form']

        if form and isinstance(form, ConfirmedEmailAuthenticationForm):
            loginform = form
        else:
            loginform = ConfirmedEmailAuthenticationForm()

        if form and isinstance(form, TodoUserCreationForm):
            signupform = form
        else:
            signupform = TodoUserCreationForm()

        return {
            'loginform': loginform,
            'signupform': signupform
        }

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        if request.POST['form'] == 'loginform':
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
        elif request.POST['form'] == 'signupform':
            form = TodoUserCreationForm(request.POST)
            if form.is_valid():
                return self.register_user(request, form)
        else:
            raise SuspiciousOperation('Invalid form')

        if not form.is_valid():
            return self.form_invalid(form)

    def register_user(self, request, form):
        new_user = get_user_model().objects.create_user(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1'],
            display_name=form.cleaned_data['display_name']
        )

        send_confirmation_email.delay(new_user.email)

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
