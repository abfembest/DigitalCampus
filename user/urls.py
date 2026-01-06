from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('course/', views.course, name='course'),
]