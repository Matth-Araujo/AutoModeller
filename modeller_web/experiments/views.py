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
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Experiment, ExperimentResultModel, TemplateCandidate
from .forms import ExperimentCreateForm, TemplateSelectForm, RegisterForm
from .services import (
    start_experiment_async,
    start_model_building_async,
    get_alignment_data,
    create_experiment_zip,
)
from .featured import get_daily_featured_structures, get_featured_structure_initial_data

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
    struct_id = request.GET.get('structure', '').strip()

    initial_data = {}
    if use_sample or struct_id.lower() == 'tvldh':
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
    elif struct_id:
        featured_init = get_featured_structure_initial_data(struct_id, is_pt=_is_pt(request))
        if featured_init:
            initial_data.update(featured_init)

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

            if experiment.pipeline_mode == 'STEP':
                if _is_pt(request):
                    messages.info(request, f"Experimento '{experiment.title}' iniciado! Selecione o molde homólogo para continuar.")
                else:
                    messages.info(request, f"Experiment '{experiment.title}' started! Please select the homologous template to proceed.")
                return redirect('template_select', uuid=experiment.uuid)
            else:
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


def template_select(request, uuid):
    """Página dedicada para inspeção e seleção interativa do molde homólogo (template)."""
    experiment = get_object_or_404(Experiment, uuid=uuid)
    candidates = experiment.candidates.all()
    is_pt = _is_pt(request)

    # Se já concluiu tudo ou falhou, redireciona para detalhes
    if experiment.status in ('COMPLETED', 'FAILED'):
        return redirect('experiment_detail', uuid=experiment.uuid)

    if request.method == 'POST':
        form = TemplateSelectForm(request.POST)
        if form.is_valid():
            custom_pdb = form.cleaned_data.get('custom_pdb', '').strip().upper()
            custom_chain = form.cleaned_data.get('custom_chain', '').strip().upper() or 'A'
            template_code = form.cleaned_data.get('template_code', '').strip().upper()
            template_chain = form.cleaned_data.get('template_chain', '').strip().upper() or 'A'

            if custom_pdb:
                final_template = custom_pdb
                final_chain = custom_chain
            elif template_code:
                final_template = template_code
                final_chain = template_chain
            elif candidates.exists():
                final_template = candidates.first().code
                final_chain = candidates.first().chain
            else:
                final_template = '1BDM'
                final_chain = 'A'

            experiment.selected_template = final_template
            experiment.template_chain = final_chain

            num_models = form.cleaned_data.get('num_models')
            if num_models:
                experiment.num_models = num_models
            experiment.enable_loop_refinement = form.cleaned_data.get('enable_loop_refinement', False)
            experiment.loop_start = form.cleaned_data.get('loop_start')
            experiment.loop_end = form.cleaned_data.get('loop_end')

            # Atualiza flag is_selected nos candidatos
            candidates.update(is_selected=False)
            candidates.filter(code__iexact=final_template).update(is_selected=True)

            experiment.status = 'PENDING'
            experiment.current_step = 'Iniciando alinhamento e modelagem 3D' if is_pt else 'Starting alignment and 3D modeling'
            experiment.save()

            # Dispara a segunda etapa da pipeline (AlignStep -> BuildModelStep -> etc.)
            start_model_building_async(experiment.id)

            if is_pt:
                messages.success(request, f"Molde '{final_template}' selecionado com sucesso! Modelagem 3D em andamento.")
            else:
                messages.success(request, f"Template '{final_template}' selected successfully! 3D modeling in progress.")

            return redirect('experiment_detail', uuid=experiment.uuid)
    else:
        top_cand = candidates.filter(is_selected=True).first() or candidates.first()
        initial_data = {
            'template_code': top_cand.code if top_cand else (experiment.selected_template or ''),
            'template_chain': top_cand.chain if top_cand else (experiment.template_chain or 'A'),
            'num_models': experiment.num_models or 5,
            'enable_loop_refinement': experiment.enable_loop_refinement,
            'loop_start': experiment.loop_start,
            'loop_end': experiment.loop_end,
        }
        form = TemplateSelectForm(initial=initial_data)

    return render(request, 'experiments/template_select.html', {
        'experiment': experiment,
        'candidates': candidates,
        'form': form,
        'is_pt': is_pt,
    })


def experiment_detail(request, uuid):
    """Página de detalhes, progresso em tempo real e visualização 3D/gráficos."""
    experiment = get_object_or_404(Experiment, uuid=uuid)
    candidates = experiment.candidates.all()
    result_models = experiment.result_models.all()
    best_model = experiment.best_result_model
    alignment_data = get_alignment_data(experiment)

    return render(request, 'experiments/experiment_detail.html', {
        'experiment': experiment,
        'candidates': candidates,
        'result_models': result_models,
        'best_model': best_model,
        'alignment_data': alignment_data,
        'is_pt': _is_pt(request),
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

    alignment_data = get_alignment_data(experiment)

    return JsonResponse({
        'status': experiment.status,
        'current_step': experiment.current_step,
        'progress_percent': experiment.progress_percent,
        'pipeline_mode': experiment.pipeline_mode,
        'selected_template': experiment.selected_template,
        'template_chain': experiment.template_chain,
        'best_model_name': experiment.best_model_name,
        'best_dope_score': experiment.best_dope_score,
        'best_ga341_score': experiment.best_ga341_score,
        'best_model_url': experiment.best_result_model.pdb_file.url if experiment.best_result_model and experiment.best_result_model.pdb_file else '',
        'dope_plot_url': experiment.dope_plot.url if experiment.dope_plot else '',
        'log_output': experiment.log_output,
        'error_message': experiment.error_message,
        'models': models_data,
        'candidates': candidates_data,
        'alignment_data': alignment_data,
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
    media_root_real = os.path.realpath(settings.MEDIA_ROOT)
    zip_abs_path = os.path.realpath(os.path.join(media_root_real, zip_rel_path))

    if not zip_abs_path.startswith(media_root_real + os.sep) or not os.path.exists(zip_abs_path):
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
    """Alterna o idioma entre inglês (en) e português (pt) com validação contra Open Redirect."""
    lang = request.GET.get('lang', 'en')
    if lang not in ('en', 'pt'):
        lang = 'en'
    request.session['site_lang'] = lang
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = '/'
    response = redirect(next_url)
    response.set_cookie(
        'site_lang',
        lang,
        max_age=365 * 24 * 60 * 60,
        httponly=True,
        samesite='Lax',
        secure=request.is_secure(),
    )
    return response


@require_GET
def privacy_policy(request):
    """Página da Política de Privacidade e Proteção de Dados (LGPD / GDPR)."""
    return render(request, 'experiments/privacy_policy.html', {
        'is_pt': _is_pt(request),
    })


@require_GET
def cookie_policy(request):
    """Página da Política de Cookies e Armazenamento Local."""
    return render(request, 'experiments/cookie_policy.html', {
        'is_pt': _is_pt(request),
    })
