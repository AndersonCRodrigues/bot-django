"""
Comando Django para verificar o conteúdo da seção 1 no Weaviate.
"""

from django.core.management.base import BaseCommand
from apps.adventures.models import Adventure
from apps.game.services.retriever_service import get_section_by_number_direct


class Command(BaseCommand):
    help = 'Verifica o conteúdo da seção 1 de todas as aventuras no Weaviate'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("🔍 Verificando seção 1 no Weaviate")
        self.stdout.write("=" * 80)

        adventures = Adventure.objects.all()
        self.stdout.write(f"\n📚 Aventuras encontradas: {adventures.count()}\n")

        for adv in adventures:
            self.stdout.write(f"\n{'=' * 80}")
            self.stdout.write(f"📖 Adventure: {adv.title}")
            self.stdout.write(f"   ID: {adv.id}")

            if hasattr(adv, 'processed_book') and adv.processed_book:
                class_name = adv.processed_book.weaviate_class_name
                self.stdout.write(f"   Weaviate class: {class_name}")

                # Buscar seção 1
                self.stdout.write(f"\n   🔍 Buscando seção 1...")
                section_data = get_section_by_number_direct(class_name, 1)

                if section_data:
                    self.stdout.write(self.style.SUCCESS("\n   ✅ Seção 1 encontrada!"))

                    metadata = section_data.get('metadata', {})
                    self.stdout.write(f"\n   📋 Metadados:")
                    for key, value in metadata.items():
                        self.stdout.write(f"      {key}: {value}")

                    content = section_data.get('content', '')
                    self.stdout.write(f"\n   📄 Conteúdo (primeiros 500 caracteres):")
                    self.stdout.write(f"   {'-' * 76}")
                    self.stdout.write(f"   {content[:500]}")
                    self.stdout.write(f"   {'-' * 76}")
                    self.stdout.write(f"   ... (total: {len(content)} caracteres)")

                    # Verificar se parece ser uma introdução
                    intro_keywords = ['bem-vindo', 'aventura começa', 'você é', 'início']
                    has_intro_keywords = any(keyword in content.lower() for keyword in intro_keywords)

                    if has_intro_keywords:
                        self.stdout.write(self.style.SUCCESS("\n   ✅ Parece ser uma introdução!"))
                    else:
                        self.stdout.write(self.style.WARNING("\n   ⚠️  Não parece ser uma introdução (sem palavras-chave típicas)"))

                else:
                    self.stdout.write(self.style.ERROR("\n   ❌ Seção 1 NÃO encontrada!"))
            else:
                self.stdout.write(self.style.WARNING("\n   ⚠️  Livro não processado"))

        self.stdout.write(f"\n{'=' * 80}\n")
