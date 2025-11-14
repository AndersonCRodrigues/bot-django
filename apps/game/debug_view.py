from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from apps.game.models import GameSession
from apps.characters.models import Character
import json

@login_required
def debug_session(request, session_id):
    """Debug page to check session data"""
    session = GameSession.find_by_id(session_id, request.user.id)

    if not session:
        return HttpResponse("Session not found", status=404)

    character = Character.find_by_id(session.character_id, request.user.id)

    debug_info = {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "character_id": session.character_id,
        "adventure_id": session.adventure_id,
        "current_section": session.current_section,
        "status": session.status,
        "inventory": session.inventory,
        "history_count": len(session.history),
        "history": session.history[:3],  # Primeiras 3 entradas
        "character": {
            "name": character.name if character else None,
            "stamina": character.stamina if character else None,
            "luck": character.luck if character else None,
            "equipment": character.equipment if character else None,
        } if character else None
    }

    return HttpResponse(f"<pre>{json.dumps(debug_info, indent=2, default=str)}</pre>")
