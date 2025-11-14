"""
Mostra o schema das classes no Weaviate.
"""

from django.core.management.base import BaseCommand
from apps.adventures.models import Adventure
from apps.game.services.weaviate_service import get_weaviate_client


class Command(BaseCommand):
    help = 'Mostra o schema das classes no Weaviate'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("📋 Schema das classes no Weaviate")
        self.stdout.write("=" * 80)

        try:
            client = get_weaviate_client()

            # Listar todas as classes
            adventures = Adventure.objects.all()

            for adv in adventures:
                if not hasattr(adv, 'processed_book') or not adv.processed_book:
                    continue

                class_name = adv.processed_book.weaviate_class_name
                self.stdout.write(f"\n{'=' * 80}")
                self.stdout.write(f"📖 {adv.title}")
                self.stdout.write(f"   Classe: {class_name}")

                try:
                    collection = client.collections.get(class_name)
                    config = collection.config.get()

                    self.stdout.write("\n   📋 Propriedades:")
                    for prop in config.properties:
                        self.stdout.write(f"      - {prop.name} ({prop.data_type})")

                    # Pegar um objeto de exemplo
                    self.stdout.write("\n   📄 Exemplo de objeto:")
                    response = collection.query.fetch_objects(limit=1)

                    if response.objects:
                        obj = response.objects[0]
                        self.stdout.write(f"      Propriedades do objeto:")
                        for key, value in obj.properties.items():
                            value_preview = str(value)[:100] if value else "None"
                            self.stdout.write(f"         {key}: {value_preview}")
                    else:
                        self.stdout.write("      Nenhum objeto encontrado")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ❌ Erro: {e}"))

            self.stdout.write(f"\n{'=' * 80}\n")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao acessar Weaviate: {e}"))
