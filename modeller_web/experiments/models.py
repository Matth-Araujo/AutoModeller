import uuid
import os
from django.db import models
from django.contrib.auth.models import User

class Experiment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('RUNNING', 'Em Execução'),
        ('COMPLETED', 'Concluído'),
        ('FAILED', 'Falhou'),
    ]

    SEQUENCE_TYPES = [
        ('PIR', 'PIR (Protein Information Resource)'),
        ('FASTA', 'FASTA'),
    ]

    PIPELINE_MODES = [
        ('AUTO', 'Automático (Executar Pipeline Completa)'),
        ('STEP', 'Passo a Passo (Interativo)'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='experiments')
    session_key = models.CharField(max_length=100, blank=True, default='')

    title = models.CharField(max_length=200, default='Novo Experimento Modeller')
    description = models.TextField(blank=True, default='')

    sequence_name = models.CharField(max_length=100, default='TargetProt')
    sequence_type = models.CharField(max_length=10, choices=SEQUENCE_TYPES, default='PIR')
    sequence_text = models.TextField(help_text="Conteúdo da sequência em formato PIR ou FASTA")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    current_step = models.CharField(max_length=150, default='Aguardando início')
    progress_percent = models.IntegerField(default=0)
    pipeline_mode = models.CharField(max_length=20, choices=PIPELINE_MODES, default='AUTO')

    # Selected template info
    selected_template = models.CharField(max_length=50, blank=True, default='')
    template_chain = models.CharField(max_length=10, default='A')

    # Modeling parameters
    num_models = models.IntegerField(default=5)
    enable_loop_refinement = models.BooleanField(default=False)
    loop_start = models.IntegerField(null=True, blank=True)
    loop_end = models.IntegerField(null=True, blank=True)

    # Output summaries
    best_model_name = models.CharField(max_length=100, blank=True, default='')
    best_dope_score = models.FloatField(null=True, blank=True)
    best_ga341_score = models.FloatField(null=True, blank=True)

    # Generated files
    dope_plot = models.FileField(upload_to='plots/', blank=True, null=True)
    alignment_pir = models.FileField(upload_to='alignments/', blank=True, null=True)
    alignment_pap = models.FileField(upload_to='alignments/', blank=True, null=True)

    # Logs
    log_output = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        owner = self.user.username if self.user else "Avulso"
        return f"{self.title} ({owner}) - {self.status}"

    @property
    def is_guest(self):
        return self.user is None

    @property
    def best_result_model(self):
        return self.result_models.filter(is_best=True).first()


class ExperimentResultModel(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='result_models')
    name = models.CharField(max_length=100)
    pdb_file = models.FileField(upload_to='models/')
    dope_score = models.FloatField(null=True, blank=True)
    ga341_score = models.FloatField(null=True, blank=True)
    is_best = models.BooleanField(default=False)
    is_loop_model = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_best', 'dope_score']

    def __str__(self):
        return f"{self.name} (DOPE: {self.dope_score})"


class TemplateCandidate(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='candidates')
    code = models.CharField(max_length=50)
    chain = models.CharField(max_length=10, default='A')
    identity = models.FloatField(default=0.0)
    is_selected = models.BooleanField(default=False)

    class Meta:
        ordering = ['-identity']

    def __str__(self):
        return f"{self.code} ({self.identity}% id)"
