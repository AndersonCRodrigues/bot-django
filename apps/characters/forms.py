from django import forms


class CharacterForm(forms.Form):
    PROTECTION_CHOICES = [
        ("shield", "🛡️ Escudo - Proteção adicional em combate"),
        ("boots", "🥾 Botas - Maior agilidade para esquivar"),
    ]

    POTION_CHOICES = [
        ("luck", "🍀 Poção de Sorte"),
        ("skill", "💪 Poção de Habilidade"),
        ("stamina", "❤️ Poção de Energia"),
    ]

    name = forms.CharField(
        max_length=100,
        label="Nome do Aventureiro",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 bg-[#0A0A0A] border border-[#27272A] rounded-lg text-white text-sm placeholder-[#52525B] focus:outline-none focus:ring-1 focus:ring-[#6366F1] transition-all",
                "placeholder": "Digite o nome do personagem",
            }
        ),
    )

    protection = forms.ChoiceField(
        choices=PROTECTION_CHOICES,
        widget=forms.RadioSelect(
            attrs={"class": "text-[#6366F1] focus:ring-[#6366F1]"}
        ),
        label="Escolha sua Proteção",
        initial="shield",
    )

    potion1 = forms.ChoiceField(
        choices=POTION_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 bg-[#0A0A0A] border border-[#27272A] rounded-lg text-white text-sm focus:outline-none focus:ring-1 focus:ring-[#6366F1] transition-all"
            }
        ),
        label="Primeira Poção",
    )

    potion2 = forms.ChoiceField(
        choices=POTION_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 bg-[#0A0A0A] border border-[#27272A] rounded-lg text-white text-sm focus:outline-none focus:ring-1 focus:ring-[#6366F1] transition-all"
            }
        ),
        label="Segunda Poção",
    )

    notes = forms.CharField(
        required=False,
        label="História e Anotações (Opcional)",
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-3 py-2 bg-[#0A0A0A] border border-[#27272A] rounded-lg text-white text-sm placeholder-[#52525B] focus:outline-none focus:ring-1 focus:ring-[#6366F1] resize-none transition-all",
                "placeholder": "Escreva a história do seu aventureiro...",
                "rows": 4,
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        potion1 = cleaned_data.get("potion1")
        potion2 = cleaned_data.get("potion2")

        if potion1 and potion2 and potion1 == potion2:
            raise forms.ValidationError("Você deve escolher poções diferentes!")

        return cleaned_data
