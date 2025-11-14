from django import forms
from apps.adventures.models import Adventure


class BookUploadForm(forms.ModelForm):
    pdf_file = forms.FileField(
        label="Arquivo PDF",
        help_text="Arquivo PDF do livro Fighting Fantasy (máx. 50MB)",
        widget=forms.FileInput(attrs={"accept": ".pdf", "class": "hidden"}),
    )

    weaviate_class_name = forms.CharField(
        label="Nome Técnico (Weaviate)",
        max_length=255,
        help_text="Nome único sem espaços (ex: Ovilarejoamaldicoado)",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ex: Ovilarejoamaldicoado",
                "class": "w-full px-4 py-3 bg-[#1A1A1A] border border-[#27272A] rounded-lg text-white placeholder-[#71717A] focus:outline-none focus:border-[#6366F1] transition-colors",
            }
        ),
    )

    class Meta:
        model = Adventure
        fields = [
            "title",
            "description",
            "cover_image",
            "genre",
            "difficulty",
            "estimated_duration",
            "is_published",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Ex: O Vilarejo Amaldiçoado",
                    "class": "w-full px-4 py-3 bg-[#1A1A1A] border border-[#27272A] rounded-lg text-white placeholder-[#71717A] focus:outline-none focus:border-[#6366F1] transition-colors",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Descreva a aventura...",
                    "class": "w-full px-4 py-3 bg-[#1A1A1A] border border-[#27272A] rounded-lg text-white placeholder-[#71717A] focus:outline-none focus:border-[#6366F1] transition-colors",
                }
            ),
            "cover_image": forms.FileInput(
                attrs={"accept": "image/*", "class": "hidden"}
            ),
            "genre": forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 bg-[#1A1A1A] border border-[#27272A] rounded-lg text-white focus:outline-none focus:border-[#6366F1] transition-colors"
                }
            ),
            "difficulty": forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 bg-[#1A1A1A] border border-[#27272A] rounded-lg text-white focus:outline-none focus:border-[#6366F1] transition-colors"
                }
            ),
            "estimated_duration": forms.NumberInput(
                attrs={
                    "min": 1,
                    "placeholder": "120",
                    "class": "w-full px-4 py-3 bg-[#1A1A1A] border border-[#27272A] rounded-lg text-white placeholder-[#71717A] focus:outline-none focus:border-[#6366F1] transition-colors",
                }
            ),
        }

        labels = {
            "title": "Título da Aventura",
            "description": "Descrição",
            "cover_image": "Imagem de Capa",
            "genre": "Gênero",
            "difficulty": "Dificuldade",
            "estimated_duration": "Duração Estimada (minutos)",
            "is_published": "Publicar imediatamente?",
        }

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get("pdf_file")

        if pdf_file:
            if pdf_file.size > 50 * 1024 * 1024:
                raise forms.ValidationError("Arquivo muito grande. Máximo: 50MB")

            if not pdf_file.name.lower().endswith(".pdf"):
                raise forms.ValidationError("Apenas arquivos PDF são aceitos")

        return pdf_file

    def clean_cover_image(self):
        cover_image = self.cleaned_data.get("cover_image")

        if cover_image:
            if cover_image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Imagem muito grande. Máximo: 5MB")

            allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
            if not any(
                cover_image.name.lower().endswith(ext) for ext in allowed_extensions
            ):
                raise forms.ValidationError(
                    "Formato não suportado. Use: JPG, PNG, GIF ou WEBP"
                )

        return cover_image

    def clean_weaviate_class_name(self):
        name = self.cleaned_data.get("weaviate_class_name")

        if name:
            name = name.replace(" ", "").replace("-", "").replace("_", "")

            if not name.isalnum():
                raise forms.ValidationError("Apenas letras e números são permitidos")

            name = name.capitalize()

        return name
