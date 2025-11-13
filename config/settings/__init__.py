"""
Importa o settings correto baseado na variável de ambiente DJANGO_ENV
"""

import os

django_env = os.environ.get("DJANGO_ENV", "development")

if django_env == "production":
    from .production import *
else:
    from .development import *
