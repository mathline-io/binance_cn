from django.contrib import admin
from django.contrib.staticfiles.views import serve as static_serve
from django.urls import path, re_path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('appSender.urls', namespace='appSender')),
    re_path(r'^static/(?P<path>.*)$', static_serve, {'insecure': True}, name='static'),
]
