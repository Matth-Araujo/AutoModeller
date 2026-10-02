from django.contrib import admin
from .models import Experiment, ExperimentResultModel, TemplateCandidate

class ExperimentResultModelInline(admin.TabularInline):
    model = ExperimentResultModel
    extra = 0
    readonly_fields = ('name', 'dope_score', 'ga341_score', 'is_best', 'is_loop_model')

class TemplateCandidateInline(admin.TabularInline):
    model = TemplateCandidate
    extra = 0
    readonly_fields = ('code', 'chain', 'identity', 'is_selected')

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ('title', 'sequence_name', 'user_display', 'status', 'best_model_name', 'best_dope_score', 'created_at')
    list_filter = ('status', 'sequence_type', 'created_at')
    search_fields = ('title', 'sequence_name', 'user__username', 'description')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    inlines = [ExperimentResultModelInline, TemplateCandidateInline]

    def user_display(self, obj):
        return obj.user.username if obj.user else "Avulso (Convidado)"
    user_display.short_description = "Usuário"

@admin.register(ExperimentResultModel)
class ExperimentResultModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'experiment', 'dope_score', 'ga341_score', 'is_best', 'is_loop_model')
    list_filter = ('is_best', 'is_loop_model')

@admin.register(TemplateCandidate)
class TemplateCandidateAdmin(admin.ModelAdmin):
    list_display = ('code', 'experiment', 'chain', 'identity', 'is_selected')
    list_filter = ('is_selected',)
