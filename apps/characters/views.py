from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Character
from .forms import CharacterForm


@login_required
def character_list(request):
    characters = Character.find_by_user(request.user.id)

    context = {
        "characters": characters,
    }

    return render(request, "characters/list.html", context)


@login_required
def character_create(request):
    if request.method == "POST":
        form = CharacterForm(request.POST)
        if form.is_valid():
            character = Character(
                name=form.cleaned_data["name"],
                protection=form.cleaned_data["protection"],
                potion1=form.cleaned_data["potion1"],
                potion2=form.cleaned_data["potion2"],
                notes=form.cleaned_data["notes"],
                user_id=request.user.id,
            )
            character.save()
            messages.success(
                request, f'Aventureiro "{character.name}" criado com sucesso!'
            )

            # Se veio da seleção de personagem, volta pra lá
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect("characters:detail", character_id=str(character._id))
    else:
        form = CharacterForm()

    context = {
        "form": form,
    }

    return render(request, "characters/create.html", context)


@login_required
def character_detail(request, character_id):
    character = Character.find_by_id(character_id, request.user.id)

    if not character:
        messages.error(request, "Personagem não encontrado.")
        return redirect("characters:list")

    context = {
        "character": character,
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
        character.delete()
        messages.success(request, f'Personagem "{name}" deletado.')
        return redirect("characters:list")

    context = {
        "character": character,
    }

    return render(request, "characters/delete.html", context)
