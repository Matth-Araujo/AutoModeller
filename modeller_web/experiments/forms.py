import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Experiment

class ExperimentCreateForm(forms.ModelForm):
    title = forms.CharField(
        required=False,
        label="Experiment Title",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Lactate Dehydrogenase Modeling (optional)'
        })
    )
    sequence_file = forms.FileField(
        required=False,
        label="Sequence File (.pir, .fasta, .txt)",
        help_text="Select a file or paste sequence text below."
    )

    class Meta:
        model = Experiment
        fields = [
            'title',
            'description',
            'sequence_type',
            'sequence_text',
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notes or objectives of the experiment (optional)'
            }),
            'sequence_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'sequence_text': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 6,
                'placeholder': '>P1;TvLDH\nsequence:TvLDH:::::::0.00: 0.00\nMSEAAHVLITGAAGQIGYILSHWIASGELYGDRQVYLHLLDIPPAMN...\n*'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        seq_text = cleaned_data.get('sequence_text', '')
        seq_file = cleaned_data.get('sequence_file')

        file_prefix = None
        if seq_file:
            try:
                content = seq_file.read().decode('utf-8', errors='ignore')
                cleaned_data['sequence_text'] = content
                seq_text = content
                file_prefix = seq_file.name.split('.')[0]
            except Exception as e:
                raise forms.ValidationError(f"Could not read the uploaded file: {e}")
        elif not seq_text or not seq_text.strip():
            raise forms.ValidationError("Please provide the protein sequence by pasting text or uploading a file.")

        # Detecção automática do nome/código da sequência
        seq_name = None
        lines = [line.strip() for line in seq_text.strip().splitlines() if line.strip()]

        if lines:
            first_line = lines[0]
            if first_line.startswith('>P1;'):
                pir_code = first_line.replace('>P1;', '').strip().split()[0]
                if pir_code:
                    seq_name = pir_code
                    cleaned_data['sequence_type'] = 'PIR'
            elif first_line.startswith('>'):
                fasta_header = first_line[1:].strip()
                tokens = [t for t in re.split(r'[\s|]+', fasta_header) if t and t.lower() not in ('sp', 'tr', 'pdb')]
                seq_name = tokens[0] if tokens else fasta_header[:12]
                cleaned_data['sequence_type'] = 'FASTA'

        if not seq_name and file_prefix:
            seq_name = file_prefix

        if not seq_name:
            title = cleaned_data.get('title', '').strip()
            if title:
                seq_name = re.sub(r'[^A-Za-z0-9_]', '', title.replace(' ', '_'))[:15]
            else:
                seq_name = 'TargetProt'

        seq_name = re.sub(r'[^A-Za-z0-9_]', '_', seq_name).strip('_') or 'TargetProt'
        cleaned_data['sequence_name'] = seq_name

        # Título padrão automático em inglês se não fornecido
        title = cleaned_data.get('title', '').strip()
        if not title:
            cleaned_data['title'] = f"Modeling {seq_name}"

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.sequence_name = self.cleaned_data.get('sequence_name', 'TargetProt')
        instance.title = self.cleaned_data.get('title') or f"Modeling {instance.sequence_name}"
        instance.enable_loop_refinement = False
        if commit:
            instance.save()
        return instance


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@example.com'})
    )
    first_name = forms.CharField(
        required=True,
        label="Full Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'})
    )
    last_name = forms.CharField(
        required=False,
        label="Last Name (optional)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Last Name'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError("Email address is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email'].strip().lower()
        user.email = email
        user.username = email
        if commit:
            user.save()
        return user
