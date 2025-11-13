from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from apps.accounts.views import home

urlpatterns = [
    path("", home, name="home"),  # ← Adicionar
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
