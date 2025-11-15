"""
Debug: Mostra resposta RAW da LLM e opções estruturadas extraídas.
"""

from django.core.management.base import BaseCommand
from apps.game.models import GameSession
from apps.characters.models import Character


class Command(BaseCommand):
    help = 'Mostra última resposta LLM e opções estruturadas de uma sessão'

    def add_arguments(self, parser):
        parser.add_argument(
            'session_id',
            type=str,
            help='ID da sessão para debugar'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            default=1,
            help='ID do usuário (default: 1)'
        )

    def handle(self, *args, **options):
        session_id = options['session_id']
        user_id = options['user_id']

        self.stdout.write("=" * 80)
        self.stdout.write(f"🔍 DEBUG: Última resposta LLM da sessão {session_id}")
        self.stdout.write("=" * 80)

        try:
            session = GameSession.find_by_id(session_id, user_id)
            if not session:
                self.stdout.write(
                    self.style.ERROR(f"\n❌ Sessão {session_id} não encontrada\n")
                )
                return

            if not session.history:
                self.stdout.write(
                    self.style.WARNING("\n⚠️ Sessão sem histórico\n")
                )
                return

            # Pegar último turno
            last_turn = session.history[-1]

            self.stdout.write("\n📊 INFORMAÇÕES DO TURNO:")
            self.stdout.write(f"   Turno: {last_turn.get('turn', '?')}")
            self.stdout.write(f"   Ação: {last_turn.get('player_action', 'N/A')[:60]}...")
            self.stdout.write(f"   Tipo: {last_turn.get('action_type', 'N/A')}")
            self.stdout.write(f"   Seção: {last_turn.get('section', '?')}")

            # Narrativa
            narrative = last_turn.get('narrative', '')
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write("📖 NARRATIVA RETORNADA:")
            self.stdout.write("=" * 80)
            self.stdout.write(narrative[:500] + "..." if len(narrative) > 500 else narrative)

            # Opções estruturadas
            structured_options = last_turn.get('structured_options', [])

            self.stdout.write("\n" + "=" * 80)
            self.stdout.write("🎯 OPÇÕES ESTRUTURADAS:")
            self.stdout.write("=" * 80)

            if structured_options:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ {len(structured_options)} opções estruturadas encontradas:\n"
                    )
                )
                for i, opt in enumerate(structured_options, 1):
                    self.stdout.write(f"\n   {i}. Tipo: {opt.get('type', 'N/A')}")
                    self.stdout.write(f"      Texto: {opt.get('text', 'N/A')}")
                    if 'target' in opt:
                        self.stdout.write(f"      Alvo: {opt['target']}")
                    if 'stat' in opt:
                        self.stdout.write(f"      Stat: {opt['stat']}")
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "\n❌ NENHUMA opção estruturada encontrada!"
                        "\n\nPossíveis causas:"
                        "\n  1. LLM não retornou JSON (ignorou instrução)"
                        "\n  2. JSON retornado estava malformado"
                        "\n  3. Parser não encontrou o padrão esperado"
                        "\n"
                    )
                )

            # Verificar se há JSON na narrativa (erro comum)
            if '```json' in narrative:
                self.stdout.write(
                    self.style.WARNING(
                        "\n⚠️ JSON ENCONTRADO NA NARRATIVA!"
                        "\nIsso significa que o parser NÃO extraiu o JSON corretamente."
                        "\nO JSON deveria estar em 'structured_options', não na narrativa."
                    )
                )
            elif '{' in narrative and '"options"' in narrative:
                self.stdout.write(
                    self.style.WARNING(
                        "\n⚠️ Possível JSON sem markdown encontrado na narrativa!"
                        "\nParser pode ter falhado ao extrair."
                    )
                )

            self.stdout.write("\n" + "=" * 80 + "\n")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Erro: {e}\n")
            )
            import traceback
            traceback.print_exc()
