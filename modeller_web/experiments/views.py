import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_GET, require_POST
from django.conf import settings
from django.utils import timezone

from .models import Experiment, ExperimentResultModel, TemplateCandidate
from .forms import ExperimentCreateForm, RegisterForm
from .services import start_experiment_async, create_experiment_zip
from .featured import get_daily_featured_structures

SAMPLE_TVLDH_PIR = """>P1;TvLDH
sequence:TvLDH:::::::0.00: 0.00
MSEAAHVLITGAAGQIGYILSHWIASGELYGDRQVYLHLLDIPPAMNRLTALTMELEDCAFPHLAGFVATTDPKA
AFKDIDCAFLVASMPLKPGQVRADLISSNSVIFKNTGEYLSKWAKPSVKVLVIGNPDNTNCEIAMLHAKNLKPEN
FSSLSMLDQNRAYYEVASKLGVDVKDVHDIIVWGNHGESMVADLTQATFTKEGKTQKVVDVLDHDYVFDTFFKKI
GHRAWDILEHRGFTSAASPTKAAIQHMKAWLFGTAPGEVLSMGIPVPEGNPYGIKPGVVFSFPCNVDKEGKIHVV
EGFKVNDWLREKLDFTEKDLFHEKEIALNHLAQGG*"""


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _is_pt(request):
    lang = request.session.get('site_lang') or request.COOKIES.get('site_lang', 'en')
    return lang == 'pt'


def home(request):
    """Página inicial com apresentação, chamada para ação e estruturas em destaque do dia."""
    session_key = _ensure_session_key(request)
    is_pt = _is_pt(request)

    recent_experiments = []
    if request.user.is_authenticated:
        recent_experiments = Experiment.objects.filter(user=request.user)[:5]
    else:
        recent_experiments = Experiment.objects.filter(session_key=session_key)[:5]

    today = timezone.localdate()
    today_str = today.strftime('%d/%m/%Y') if is_pt else today.strftime('%Y-%m-%d')
    featured_structures = get_daily_featured_structures(target_date=today, count=4, is_pt=is_pt)

    return render(request, 'experiments/home.html', {
        'recent_experiments': recent_experiments,
        'today_str': today_str,
        'featured_structures': featured_structures,
        'featured_structures_json': json.dumps(featured_structures),
    })


@require_GET
def featured_shuffle_api(request):
    """Retorna uma nova seleção de estruturas sorteadas sob demanda."""
    is_pt = _is_pt(request)
    try:
        offset = int(request.GET.get('offset', 0))
    except (ValueError, TypeError):
        offset = 0

    structures = get_daily_featured_structures(count=4, seed_offset=offset, is_pt=is_pt)
    return JsonResponse({
        'status': 'ok',
        'structures': structures,
        'offset': offset,
    })


def experiment_create(request):
    """Cria um novo experimento (suporta usuário autenticado e anônimo/avulso)."""
    session_key = _ensure_session_key(request)
    use_sample = request.GET.get('sample') == '1'

    initial_data = {}
    if use_sample:
        # Puxa o exemplo real do smosh se existir
        sample_path = os.path.join(settings.SMOSH_PARENT_DIR, 'smosh', 'files', 'TvLDH.pir')
        if os.path.exists(sample_path):
            with open(sample_path, 'r') as f:
                initial_data['sequence_text'] = f.read()
        else:
            initial_data['sequence_text'] = SAMPLE_TVLDH_PIR
        initial_data['sequence_name'] = 'TvLDH'
        initial_data['sequence_type'] = 'PIR'
        if _is_pt(request):
            initial_data['title'] = 'Experimento Exemplo: TvLDH (Lactato Desidrogenase)'
            initial_data['description'] = 'Demonstração automatizada completa de modelagem 3D comparativa utilizando TvLDH.'
        else:
            initial_data['title'] = 'TvLDH Example Experiment (Lactate Dehydrogenase)'
            initial_data['description'] = 'Full automated 3D comparative modeling demonstration using TvLDH.'

    if request.method == 'POST':
        form = ExperimentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            experiment = form.save(commit=False)
            if request.user.is_authenticated:
                experiment.user = request.user
            else:
                experiment.session_key = session_key

            experiment.sequence_name = form.cleaned_data.get('sequence_name', 'TargetProt')
            experiment.title = form.cleaned_data.get('title') or f"Modeling {experiment.sequence_name}"
            experiment.status = 'PENDING'
            experiment.current_step = 'Enfileirado' if _is_pt(request) else 'Queued'
            experiment.save()

            # Guardar lista de uuids na sessão para o convidado
            guest_uuids = request.session.get('guest_experiment_uuids', [])
            guest_uuids.append(str(experiment.uuid))
            request.session['guest_experiment_uuids'] = guest_uuids

            # Disparar pipeline assíncrona
            start_experiment_async(experiment.id)

            if _is_pt(request):
                messages.success(request, f"Experimento '{experiment.title}' iniciado com sucesso!")
            else:
                messages.success(request, f"Experiment '{experiment.title}' started successfully!")
            return redirect('experiment_detail', uuid=experiment.uuid)
    else:
        form = ExperimentCreateForm(initial=initial_data)

    return render(request, 'experiments/experiment_form.html', {
        'form': form,
        'is_guest': not request.user.is_authenticated,
    })


def experiment_detail(request, uuid):
    """Página de detalhes, progresso em tempo real e visualização 3D/gráficos."""
    experiment = get_object_or_404(Experiment, uuid=uuid)
    candidates = experiment.candidates.all()
    result_models = experiment.result_models.all()
    best_model = experiment.best_result_model

    return render(request, 'experiments/experiment_detail.html', {
        'experiment': experiment,
        'candidates': candidates,
        'result_models': result_models,
        'best_model': best_model,
    })


@require_GET
def experiment_status_api(request, uuid):
    """Endpoint JSON consultado via AJAX para polling de status em tempo real."""
    experiment = get_object_or_404(Experiment, uuid=uuid)
    
    models_data = []
    for m in experiment.result_models.all():
        models_data.append({
            'name': m.name,
            'url': m.pdb_file.url if m.pdb_file else '',
            'dope_score': m.dope_score,
            'ga341_score': m.ga341_score,
            'is_best': m.is_best,
            'is_loop_model': m.is_loop_model,
        })

    candidates_data = [
        {'code': c.code, 'identity': c.identity, 'is_selected': c.is_selected}
        for c in experiment.candidates.all()
    ]

    return JsonResponse({
        'status': experiment.status,
        'current_step': experiment.current_step,
        'progress_percent': experiment.progress_percent,
        'best_model_name': experiment.best_model_name,
        'best_dope_score': experiment.best_dope_score,
        'best_ga341_score': experiment.best_ga341_score,
        'best_model_url': experiment.best_result_model.pdb_file.url if experiment.best_result_model and experiment.best_result_model.pdb_file else '',
        'dope_plot_url': experiment.dope_plot.url if experiment.dope_plot else '',
        'log_output': experiment.log_output,
        'error_message': experiment.error_message,
        'models': models_data,
        'candidates': candidates_data,
    })


def experiment_list(request):
    """Lista experimentos do usuário autenticado ou experimentos avulsos da sessão."""
    session_key = _ensure_session_key(request)

    if request.user.is_authenticated:
        experiments = Experiment.objects.filter(user=request.user)
        # Verifica se há experimentos avulsos na sessão para permitir associação
        guest_uuids = request.session.get('guest_experiment_uuids', [])
        unclaimed_count = Experiment.objects.filter(uuid__in=guest_uuids, user__isnull=True).count()
    else:
        experiments = Experiment.objects.filter(session_key=session_key)
        unclaimed_count = 0

    return render(request, 'experiments/experiment_list.html', {
        'experiments': experiments,
        'unclaimed_count': unclaimed_count,
        'is_guest': not request.user.is_authenticated,
    })


@login_required
def experiment_claim(request):
    """Associa experimentos avulsos criados nesta sessão ao usuário recém-logado."""
    session_key = _ensure_session_key(request)
    guest_uuids = request.session.get('guest_experiment_uuids', [])

    claimed = Experiment.objects.filter(uuid__in=guest_uuids, user__isnull=True).update(user=request.user)
    Experiment.objects.filter(session_key=session_key, user__isnull=True).update(user=request.user)

    request.session['guest_experiment_uuids'] = []
    if _is_pt(request):
        messages.success(request, f"{claimed} experimento(s) avulso(s) foram vinculados à sua conta com sucesso!")
    else:
        messages.success(request, f"{claimed} guest experiment(s) were successfully linked to your account!")
    return redirect('experiment_list')


@require_POST
def experiment_retry(request, uuid):
    """Reinicia a execução de um experimento."""
    experiment = get_object_or_404(Experiment, uuid=uuid)
    experiment.status = 'PENDING'
    experiment.current_step = 'Reiniciando' if _is_pt(request) else 'Restarting'
    experiment.progress_percent = 0
    experiment.error_message = ''
    experiment.log_output += f"\n--- RESTARTING EXPERIMENT AT {settings.TIME_ZONE} ---\n"
    experiment.save()

    start_experiment_async(experiment.id)
    if _is_pt(request):
        messages.info(request, "O experimento foi reiniciado.")
    else:
        messages.info(request, "Experiment has been restarted.")
    return redirect('experiment_detail', uuid=experiment.uuid)


def experiment_download_zip(request, uuid):
    """Gera e faz o download de um pacote ZIP com todos os arquivos gerados."""
    experiment = get_object_or_404(Experiment, uuid=uuid)
    zip_rel_path = create_experiment_zip(experiment)
    zip_abs_path = os.path.join(settings.MEDIA_ROOT, zip_rel_path)

    if not os.path.exists(zip_abs_path):
        raise Http404("Arquivo ZIP não encontrado.")

    return FileResponse(
        open(zip_abs_path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(zip_abs_path)
    )


def register_view(request):
    """Cadastro de novo usuário."""
    if request.user.is_authenticated:
        return redirect('experiment_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Reivindica experimentos avulsos da sessão
            session_key = request.session.session_key
            guest_uuids = request.session.get('guest_experiment_uuids', [])
            Experiment.objects.filter(uuid__in=guest_uuids, user__isnull=True).update(user=user)
            if session_key:
                Experiment.objects.filter(session_key=session_key, user__isnull=True).update(user=user)
            request.session['guest_experiment_uuids'] = []

            if _is_pt(request):
                messages.success(request, f"Bem-vindo(a), {user.first_name or user.email}! Sua conta foi criada com sucesso.")
            else:
                messages.success(request, f"Welcome, {user.first_name or user.email}! Your account was created successfully.")
            return redirect('experiment_list')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


def set_language_custom(request):
    """Alterna o idioma entre inglês (en) e português (pt)."""
    lang = request.GET.get('lang', 'en')
    if lang not in ('en', 'pt'):
        lang = 'en'
    request.session['site_lang'] = lang
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
    if not next_url.startswith('/'):
        next_url = '/'
    response = redirect(next_url)
    response.set_cookie('site_lang', lang, max_age=365*24*60*60)
    return response
