"""djangodocker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.urls import include, path, re_path
from django.contrib import admin

from djangodocker import views

urlpatterns = [
    path('', views.index),
    path('signup/', views.signup, name='signup'),
    path('todos/add', views.add_todo),
    path('todos/<int:todo_id>/toggle', views.toggle_todo),
    path('admin/', admin.site.urls),
    path('', include('django.contrib.auth.urls'))
]
