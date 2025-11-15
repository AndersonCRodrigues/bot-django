#!/usr/bin/env python
"""
Script de debug para verificar o conteúdo da seção 1 no Weaviate.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.game.services.retriever_service import get_section_by_number_direct
from apps.adventures.models import Adventure

print("=" * 80)
print("DEBUG: Verificando seção 1 no Weaviate")
print("=" * 80)

# Buscar todas as adventures
adventures = Adventure.objects.all()

print(f"\nAventuras encontradas: {adventures.count()}")

for adv in adventures:
    print(f"\n{'=' * 80}")
    print(f"Adventure: {adv.title}")
    print(f"ID: {adv.id}")

    if hasattr(adv, 'processed_book') and adv.processed_book:
        class_name = adv.processed_book.weaviate_class_name
        print(f"Weaviate class: {class_name}")

        # Buscar seção 1
        print(f"\nBuscando seção 1...")
        section_data = get_section_by_number_direct(class_name, 1)

        if section_data:
            print(f"\n✅ Seção 1 encontrada!")
            print(f"\nMetadados:")
            print(section_data.get('metadata', {}))
            print(f"\nConteúdo (primeiros 500 caracteres):")
            content = section_data.get('content', '')
            print(content[:500])
            print(f"\n... (total: {len(content)} caracteres)")
        else:
            print(f"\n❌ Seção 1 NÃO encontrada!")
    else:
        print(f"⚠️ Livro não processado")

print(f"\n{'=' * 80}")
