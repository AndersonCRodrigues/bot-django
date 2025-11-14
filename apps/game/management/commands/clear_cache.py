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
            cache = get_cache()

            # Limpar todas as entradas
            cache.cursor.execute("DELETE FROM retrieval_cache")
            cache.conn.commit()

            count = cache.cursor.rowcount

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
