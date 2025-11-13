from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Character
from .forms import CharacterForm
from apps.adventures.models import Adventure
import re


@login_required
def character_list(request):
    characters = Character.find_by_user(request.user.id)

    for character in characters:
        if character.adventure_id:
            try:
                adventure = Adventure.objects.get(pk=character.adventure_id)
                character.adventure_name = adventure.title
            except Adventure.DoesNotExist:
                character.adventure_name = None
        else:
            character.adventure_name = None

    context = {
        "characters": characters,
    }

    return render(request, "characters/list.html", context)


@login_required
def character_create(request):
    adventure_id = None
    adventure_name = None
    next_url = request.GET.get("next", "")
    if next_url:
        match = re.search(r"adventures/(\d+)", next_url)
        if match:
            adventure_id = int(match.group(1))
            try:
                adventure = Adventure.objects.get(pk=adventure_id)
                adventure_name = adventure.title
            except Adventure.DoesNotExist:
                pass

    if request.method == "POST":
        form = CharacterForm(request.POST)
        if form.is_valid():
            character = Character(
                name=form.cleaned_data["name"],
                adventure_id=adventure_id,
                protection=form.cleaned_data["protection"],
                potion1=form.cleaned_data["potion1"],
                potion2=form.cleaned_data["potion2"],
                notes=form.cleaned_data["notes"],
                user_id=request.user.id,
            )
            character.save()

            if adventure_id:
                messages.success(
                    request, f"🎉 {character.name} criado para esta aventura!"
                )
                return redirect(f"/characters/{character.id}/?adventure={adventure_id}")

            messages.success(
                request, f'Aventureiro "{character.name}" criado com sucesso!'
            )
            return redirect("characters:detail", character_id=str(character._id))
    else:
        form = CharacterForm()

    context = {
        "form": form,
        "adventure_id": adventure_id,
        "adventure_name": adventure_name,
    }

    return render(request, "characters/create.html", context)


@login_required
def character_detail(request, character_id):
    character = Character.find_by_id(character_id, request.user.id)

    if not character:
        messages.error(request, "Personagem não encontrado.")
        return redirect("characters:list")

    adventure_name = None
    if character.adventure_id:
        try:
            adventure = Adventure.objects.get(pk=character.adventure_id)
            adventure_name = adventure.title
        except Adventure.DoesNotExist:
            pass

    context = {
        "character": character,
        "adventure_name": adventure_name,
    }

    return render(request, "characters/detail.html", context)


@login_required
def character_delete(request, character_id):
    character = Character.find_by_id(character_id, request.user.id)

    if not character:
        messages.error(request, "Personagem não encontrado.")
        return redirect("characters:list")

    if request.method == "POST":
        name = character.name
        adventure_id = character.adventure_id
        character.delete()
        messages.success(request, f'Personagem "{name}" deletado.')

        if adventure_id:
            return redirect("adventures:select_character", pk=adventure_id)

        return redirect("characters:list")

    context = {
        "character": character,
    }

    return render(request, "characters/delete.html", context)
