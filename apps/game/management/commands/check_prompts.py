"""
Verifica se os prompts estão carregados corretamente com as proteções RAG.
"""

from django.core.management.base import BaseCommand
from apps.game.workflows.prompts import NARRATIVE_SYSTEM_PROMPT


class Command(BaseCommand):
    help = 'Verifica se prompts têm proteções contra alucinação'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("🔍 Verificando NARRATIVE_SYSTEM_PROMPT")
        self.stdout.write("=" * 80)

        # Verificar se contém as instruções críticas
        keywords = [
            "CONTEXTO RAG",
            "NÃO INVENTE",
            "FONTE DE VERDADE ABSOLUTA",
            "não estão no RAG",
        ]

        self.stdout.write("\n📋 Checando palavras-chave de proteção RAG:\n")

        all_found = True
        for keyword in keywords:
            if keyword in NARRATIVE_SYSTEM_PROMPT:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ '{keyword}' encontrado")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ '{keyword}' NÃO encontrado")
                )
                all_found = False

        self.stdout.write("\n" + "=" * 80)

        if all_found:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✅ Prompt está correto com todas as proteções RAG!\n"
                    "Se ainda houver alucinação:\n"
                    "  1. Reinicie o servidor Django\n"
                    "  2. Limpe o cache: python manage.py clear_cache --confirm\n"
                    "  3. Crie uma NOVA sessão de jogo\n"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    "\n❌ Prompt NÃO tem todas as proteções!\n"
                    "Execute: git pull origin claude/analyze-project-implementation-01VDqbSLRny55mzRgca4hpvi\n"
                )
            )

        # Mostrar trecho relevante
        self.stdout.write("\n📄 Trecho do prompt (linhas com 'RAG'):\n")
        for i, line in enumerate(NARRATIVE_SYSTEM_PROMPT.split("\n"), 1):
            if "RAG" in line.upper():
                self.stdout.write(f"   {i:3d}: {line[:70]}...")

        self.stdout.write("\n" + "=" * 80 + "\n")
