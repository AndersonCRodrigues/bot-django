from django import forms
from apps.adventures.models import Adventure


class BookUploadForm(forms.ModelForm):
    """Form profissional para upload de livros."""

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
            attrs={"placeholder": "Ex: Ovilarejoamaldicoado", "class": "form-input"}
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
                    "class": "form-input",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Descreva a aventura...",
                    "class": "form-input",
                }
            ),
            "cover_image": forms.FileInput(
                attrs={"accept": "image/*", "class": "hidden"}
            ),
            "genre": forms.Select(attrs={"class": "form-input"}),
            "difficulty": forms.Select(attrs={"class": "form-input"}),
            "estimated_duration": forms.NumberInput(
                attrs={"min": 1, "placeholder": "120", "class": "form-input"}
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
        """Valida arquivo PDF."""
        pdf_file = self.cleaned_data.get("pdf_file")

        if pdf_file:
            # Valida tamanho (50MB)
            if pdf_file.size > 50 * 1024 * 1024:
                raise forms.ValidationError("Arquivo muito grande. Máximo: 50MB")

            # Valida extensão
            if not pdf_file.name.lower().endswith(".pdf"):
                raise forms.ValidationError("Apenas arquivos PDF são aceitos")

        return pdf_file

    def clean_weaviate_class_name(self):
        """Valida nome da classe Weaviate."""
        name = self.cleaned_data.get("weaviate_class_name")

        if name:
            # Remove espaços e caracteres especiais
            name = name.replace(" ", "").replace("-", "").replace("_", "")

            # Valida formato (apenas letras e números)
            if not name.isalnum():
                raise forms.ValidationError("Apenas letras e números são permitidos")

            # Primeira letra maiúscula
            name = name.capitalize()

        return name
