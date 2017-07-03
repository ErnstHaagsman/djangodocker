from django import forms

class TaskForm(forms.Form):
    todo_text = forms.CharField(label='Add Task', label_suffix='', max_length=400)
