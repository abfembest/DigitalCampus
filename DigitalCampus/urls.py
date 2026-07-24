"""
URL configuration for DigitalCampus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from django.views.static import serve as serve_static_file

from django.views.static import serve as serve_static


handler404 = 'eduweb.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('eduweb.urls')),
    path('management/', include('management.urls')),
    path('student/', include('student.urls')),
    # path('parent/', include('parent.urls')),
    path('instructor/', include('instructor.urls')),
    path('finance/', include('finance.urls')),
    path('payment/', include('payment.urls')),
    path('chatbot/', include('chatbot.urls')),

    # path('melbac/', include('melbac.urls')),
    path('library/', include('library.urls')),

    path('support/', include('support.urls', namespace='support')),

]


# Serve media files (user uploads — hero images, gallery photos/videos, dean
# photos, etc.) via Django unconditionally, in both dev and production.
#
# django.conf.urls.static.static() looks like the standard way to do this,
# but it silently returns an EMPTY urlpatterns list whenever settings.DEBUG
# is False — regardless of any `if settings.DEBUG:` wrapper around it. On
# this project's cPanel/Passenger hosting there's no separate web-server
# alias serving /media/ directly, so with DEBUG=False (the normal production
# setting) every /media/... request was falling through to the 404 handler
# even though the file existed on disk. Registering django.views.static.serve
# directly (bypassing that built-in DEBUG gate) fixes that. This is not the
# most efficient way to serve media at scale, but it's the right tradeoff for
# this site's size given no separate media-serving infrastructure exists.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve_static_file, {'document_root': settings.MEDIA_ROOT}),
]

# Static files (CSS/JS/images bundled with the app) are already served via
# WhiteNoise in production regardless of DEBUG — this extra dev-only route
# is just a harmless fallback for local `runserver` use.

# User-uploaded media (avatars, etc.) has no dedicated web server in front of it in this
# deployment (WhiteNoise only serves STATIC_ROOT), so it's served regardless of DEBUG.
# static() itself no-ops when DEBUG is off, so this hits django.views.static.serve directly.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve_static, {'document_root': settings.MEDIA_ROOT}),
]

# Static files are served by WhiteNoise in production; only add the dev route here.

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


