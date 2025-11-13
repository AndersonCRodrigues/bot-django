from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def superuser_required(view_func):
    """Decorator que requer superusuário."""

    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "⛔ Acesso negado. Apenas administradores.")
            return redirect("adventures:list")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
