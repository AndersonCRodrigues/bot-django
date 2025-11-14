"""
Comando para limpar o cache de retrieval.
"""

from django.core.management.base import BaseCommand
from apps.game.services.retrieval_cache import get_cache
import os


class Command(BaseCommand):
    help = 'Limpa o cache de retrieval do Weaviate'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a limpeza do cache',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  ATENÇÃO: Este comando vai deletar TODOS os dados do cache!\n"
                    "Execute com --confirm para confirmar:\n"
                    "  python manage.py clear_cache --confirm\n"
                )
            )
            return

        self.stdout.write("🗑️  Limpando cache de retrieval...")

        try:
            import sqlite3
            from django.conf import settings

            # Conectar diretamente ao banco SQLite do cache
            cache_dir = os.path.join(settings.BASE_DIR, 'cache')
            db_path = os.path.join(cache_dir, 'retrieval_cache.db')

            if not os.path.exists(db_path):
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  Arquivo de cache não encontrado: {db_path}"
                    )
                )
                return

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Limpar todas as entradas
            cursor.execute("DELETE FROM retrieval_cache")
            count = cursor.rowcount
            conn.commit()
            conn.close()

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Cache limpo com sucesso!"
                    f"\n   {count} entradas removidas"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Erro ao limpar cache: {e}")
            )
