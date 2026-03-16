from django.urls import path
from . import views

app_name = 'melbac'

urlpatterns = [
    path('',            views.index,      name='index'),
    path('about/',      views.about,      name='about'),
    path('academics/',  views.academics,  name='academics'),
    path('activities/', views.activities, name='activities'),
    path('contact/',    views.contact,    name='contact'),
    path('blog/',       views.blog_list,  name='blog'),
]