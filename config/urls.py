from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path(
        "",
        lambda request: (
            redirect("adventures:list")
            if request.user.is_authenticated
            else redirect("accounts:login")
        ),
    ),
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("adventures/", include("apps.adventures.urls")),
    path("characters/", include("apps.characters.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
