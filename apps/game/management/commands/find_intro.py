"""
Busca a introdução real do livro no Weaviate.
"""

from django.core.management.base import BaseCommand
from apps.adventures.models import Adventure
from apps.game.services.weaviate_client import get_weaviate_client
import weaviate.classes.query as wq


class Command(BaseCommand):
    help = 'Busca a introdução real dos livros no Weaviate'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("🔍 Buscando introdução real no Weaviate")
        self.stdout.write("=" * 80)

        adventures = Adventure.objects.all()

        for adv in adventures:
            self.stdout.write(f"\n{'=' * 80}")
            self.stdout.write(f"📖 {adv.title}")

            if not hasattr(adv, 'processed_book') or not adv.processed_book:
                self.stdout.write(self.style.WARNING("   ⚠️  Livro não processado"))
                continue

            class_name = adv.processed_book.weaviate_class_name
            self.stdout.write(f"   Weaviate class: {class_name}")

            try:
                client = get_weaviate_client()
                collection = client.collections.get(class_name)

                # Buscar seções com menor número de página (primeiras páginas)
                self.stdout.write("\n   🔍 Buscando seções das primeiras páginas...")

                response = collection.query.fetch_objects(
                    limit=10,
                    return_properties=["content", "section", "page"],
                )

                # Ordenar por página
                sections = sorted(
                    [(obj.properties.get('page', 999), obj.properties.get('section', 0), obj.properties.get('content', ''))
                     for obj in response.objects],
                    key=lambda x: (x[0], x[1])  # page, then section
                )

                self.stdout.write("\n   📋 Primeiras seções encontradas:")
                for page, section, content in sections[:5]:
                    preview = content[:150].replace('\n', ' ')
                    self.stdout.write(f"\n   Page {page}, Section {section}:")
                    self.stdout.write(f"   {preview}...")

                    # Verificar se parece introdução
                    intro_keywords = ['bem-vindo', 'aventura', 'história', 'começa', 'você é']
                    if any(kw in content.lower() for kw in intro_keywords):
                        self.stdout.write(self.style.SUCCESS("   ✅ Parece ser introdução!"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Erro: {e}"))

        self.stdout.write(f"\n{'=' * 80}\n")
