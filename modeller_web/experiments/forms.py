from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Experiment

class ExperimentCreateForm(forms.ModelForm):
    sequence_file = forms.FileField(
        required=False,
        label="Arquivo de Sequência (.pir, .fasta, .txt)",
        help_text="Selecione um arquivo ou cole o texto da sequência abaixo."
    )

    class Meta:
        model = Experiment
        fields = [
            'title',
            'description',
            'sequence_name',
            'sequence_type',
            'sequence_text',
            'enable_loop_refinement',
            'loop_start',
            'loop_end',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Modelagem da Enzima Lactato Desidrogenase'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observações ou objetivos do experimento (opcional)'
            }),
            'sequence_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: TvLDH'
            }),
            'sequence_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'sequence_text': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 6,
                'placeholder': '>P1;TvLDH\nsequence:TvLDH:::::::0.00: 0.00\nMSEAAHVLITGAAGQIGYILSHWIASGELYGDRQVYLHLLDIPPAMN...\n*'
            }),
            'enable_loop_refinement': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'enable_loop_check'
            }),
            'loop_start': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 1'
            }),
            'loop_end': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 5'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        seq_text = cleaned_data.get('sequence_text', '')
        seq_file = cleaned_data.get('sequence_file')

        if seq_file:
            try:
                content = seq_file.read().decode('utf-8', errors='ignore')
                cleaned_data['sequence_text'] = content
                if not cleaned_data.get('sequence_name'):
                    cleaned_data['sequence_name'] = seq_file.name.split('.')[0]
            except Exception as e:
                raise forms.ValidationError(f"Não foi possível ler o arquivo enviado: {e}")
        elif not seq_text.strip():
            raise forms.ValidationError("Informe a sequência colando o texto ou enviando um arquivo.")

        # Validação do loop refinement
        enable_loop = cleaned_data.get('enable_loop_refinement')
        l_start = cleaned_data.get('loop_start')
        l_end = cleaned_data.get('loop_end')
        if enable_loop:
            if l_start is None or l_end is None:
                raise forms.ValidationError("Para refinamento de loop, especifique o resíduo inicial e final.")
            if l_start >= l_end:
                raise forms.ValidationError("O resíduo inicial do loop deve ser menor que o resíduo final.")

        return cleaned_data


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
