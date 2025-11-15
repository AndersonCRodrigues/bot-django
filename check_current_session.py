#!/usr/bin/env python
"""
Verifica qual seção está sendo usada na última sessão criada.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.game.models import GameSession
from bson import ObjectId

# Pegar ID da sessão (você pode passar como argumento se quiser)
import sys

if len(sys.argv) > 1:
    session_id = sys.argv[1]
else:
    # Pegar a última sessão criada
    collection = GameSession.get_collection()
    last_session = collection.find_one(sort=[("created_at", -1)])
    if not last_session:
        print("Nenhuma sessão encontrada!")
        exit(1)
    session_id = str(last_session['_id'])

print(f"Verificando sessão: {session_id}")
print("=" * 80)

session = GameSession.find_by_id(session_id, last_session['user_id'])

if session:
    print(f"Sessão encontrada!")
    print(f"User ID: {session.user_id}")
    print(f"Character ID: {session.character_id}")
    print(f"Adventure ID: {session.adventure_id}")
    print(f"Current Section: {session.current_section}")
    print(f"Visited Sections: {session.visited_sections}")
    print(f"Status: {session.status}")
    print(f"History entries: {len(session.history)}")

    if session.history:
        print(f"\nÚltima entrada do histórico:")
        last_entry = session.history[-1]
        print(f"  Section: {last_entry.get('section', 'N/A')}")
        print(f"  Player action: {last_entry.get('player_action', 'N/A')[:100]}")
        print(f"  Narrative: {last_entry.get('narrative', 'N/A')[:200]}...")
else:
    print("Sessão não encontrada!")
