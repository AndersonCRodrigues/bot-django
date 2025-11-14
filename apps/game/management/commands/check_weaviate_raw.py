"""
Verifica dados no Weaviate SEM usar cache.
"""

from django.core.management.base import BaseCommand
from apps.adventures.models import Adventure
from apps.game.services.weaviate_service import get_weaviate_client
import weaviate.classes.query as wq


class Command(BaseCommand):
    help = 'Verifica dados no Weaviate diretamente (sem cache)'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("🔍 Verificando Weaviate (SEM CACHE)")
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

                # Buscar seção 1 diretamente por metadados
                self.stdout.write("\n   🔍 Buscando por metadata.section=1...")

                response = collection.query.fetch_objects(
                    filters=wq.Filter.by_property("section").equal(1),
                    limit=1,
                    return_properties=["content", "section", "page", "is_numbered_paragraph"],
                )

                if response.objects:
                    obj = response.objects[0]
                    props = obj.properties

                    self.stdout.write(self.style.SUCCESS("\n   ✅ Seção 1 encontrada!"))
                    self.stdout.write(f"\n   📋 Metadados:")
                    self.stdout.write(f"      section: {props.get('section')}")
                    self.stdout.write(f"      page: {props.get('page')}")
                    self.stdout.write(f"      is_numbered_paragraph: {props.get('is_numbered_paragraph')}")

                    content = props.get('content', '')
                    self.stdout.write(f"\n   📄 Conteúdo (primeiros 500 chars):")
                    self.stdout.write(f"   {'-' * 76}")
                    self.stdout.write(f"   {content[:500]}")
                    self.stdout.write(f"   {'-' * 76}")

                    # Verificar se parece introdução
                    intro_keywords = ['bem-vindo', 'aventura', 'port blacksand', 'você é', 'história']
                    if any(kw in content.lower() for kw in intro_keywords):
                        self.stdout.write(self.style.SUCCESS("\n   ✅ Parece ser introdução!"))
                    else:
                        self.stdout.write(self.style.WARNING("\n   ⚠️  NÃO parece ser introdução"))

                else:
                    self.stdout.write(self.style.ERROR("\n   ❌ Seção 1 NÃO encontrada com metadata.section=1"))

                    # Tentar buscar todas as seções numeradas
                    self.stdout.write("\n   🔍 Buscando seções numeradas...")
                    response_all = collection.query.fetch_objects(
                        filters=wq.Filter.by_property("is_numbered_paragraph").equal(True),
                        limit=10,
                        return_properties=["section", "page"],
                    )

                    if response_all.objects:
                        sections = [obj.properties.get('section') for obj in response_all.objects]
                        sections = sorted([s for s in sections if s is not None])
                        self.stdout.write(f"   📋 Seções numeradas encontradas: {sections[:10]}")
                    else:
                        self.stdout.write(self.style.ERROR("   ❌ Nenhuma seção numerada encontrada!"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Erro: {e}"))

        self.stdout.write(f"\n{'=' * 80}\n")
