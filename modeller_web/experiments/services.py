import os
import shutil
import zipfile
import threading
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Experiment, ExperimentResultModel, TemplateCandidate

# Import smosh components
from smosh.ModelingStep.FindTemplatesStep import FindTemplatesStep
from smosh.ModelingStep.GetSequenceFromPDBStep import GetSequenceFromPDBStep
from smosh.ModelingStep.AlignStep import AlignStep
from smosh.ModelingStep.BuildModelStep import BuildModelStep
from smosh.ModelingStep.MakeProfile import MakeProfile
from smosh.ModelingStep.EvaluateEnergy import EvaluateEnergy
from smosh.ModelingStep.LoopRefinementStep import LoopRefinementStep
from smosh.ModelingStep.EvaluateEnergyofLoopRefinementStep import EvaluateEnergyofLoopRefinementStep

from smosh.ModelingTools.TemplateProfile import TemplateProfile
from smosh.ModelingTools.GetDataFromPDB import GetDataFromPDB
from smosh.ModelingTools.PDBFile import PDBFile
from smosh.ModelingTools.AlignFile import AlignFile
from smosh.Exceptions.ModellerException import ModellerException


def parse_pdb_scores(pdb_path):
    """Extrai DOPE score, GA341 e função objetivo do cabeçalho do arquivo PDB."""
    scores = {'dope': None, 'ga341': None, 'molpdf': None}
    try:
        with open(pdb_path, 'r') as f:
            for line in f:
                if not line.startswith('REMARK   6'):
                    if line.startswith('ATOM'):
                        break
                    continue
                if 'DOPE score:' in line:
                    parts = line.split('DOPE score:')
                    if len(parts) > 1:
                        scores['dope'] = float(parts[1].strip().split()[0])
                elif 'GA341 score:' in line:
                    parts = line.split('GA341 score:')
                    if len(parts) > 1:
                        scores['ga341'] = float(parts[1].strip().split()[0])
                elif 'MODELLER OBJECTIVE FUNCTION:' in line:
                    parts = line.split('MODELLER OBJECTIVE FUNCTION:')
                    if len(parts) > 1:
                        scores['molpdf'] = float(parts[1].strip().split()[0])
    except Exception as e:
        print(f"Erro ao extrair scores de {pdb_path}: {e}")
    return scores


def ensure_pir_format(seq_name, seq_text):
    """Garante formatação PIR adequada com cabeçalho >P1;... e linha de descrição de 10 campos."""
    text = seq_text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return text

    if lines[0].startswith('>P1;') or lines[0].startswith('>'):
        code = lines[0].replace('>P1;', '').replace('>', '').strip() or seq_name
        header = f">P1;{code}"
        # Verifica se a segunda linha contém campos separados por dois pontos
        if len(lines) > 1 and lines[1].count(':') >= 4:
            desc = lines[1]
            body_lines = lines[2:]
        else:
            desc = f"sequence:{code}:::::::0.00: 0.00"
            body_lines = lines[1:]
    else:
        header = f">P1;{seq_name}"
        desc = f"sequence:{seq_name}:::::::0.00: 0.00"
        body_lines = lines

    body = "\n".join(body_lines)
    if not body.endswith('*'):
        body += '*'

    return f"{header}\n{desc}\n{body}\n"


def create_experiment_zip(experiment):
    """Cria um arquivo ZIP com todos os arquivos do experimento."""
    zip_filename = f"experiment_{experiment.uuid}_{experiment.sequence_name}.zip"
    zip_rel_path = os.path.join('zips', zip_filename)
    zip_abs_path = os.path.join(settings.MEDIA_ROOT, zip_rel_path)
    os.makedirs(os.path.dirname(zip_abs_path), exist_ok=True)

    with zipfile.ZipFile(zip_abs_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Sequence input
        zf.writestr(f"{experiment.sequence_name}.{experiment.sequence_type.lower()}", experiment.sequence_text)

        # Result PDB models
        for m in experiment.result_models.all():
            if m.pdb_file and os.path.exists(m.pdb_file.path):
                zf.write(m.pdb_file.path, arcname=f"models/{os.path.basename(m.pdb_file.path)}")

        # Plot
        if experiment.dope_plot and os.path.exists(experiment.dope_plot.path):
            zf.write(experiment.dope_plot.path, arcname=f"plots/{os.path.basename(experiment.dope_plot.path)}")

        # Alignments
        if experiment.alignment_pir and os.path.exists(experiment.alignment_pir.path):
            zf.write(experiment.alignment_pir.path, arcname=f"alignments/{os.path.basename(experiment.alignment_pir.path)}")
        if experiment.alignment_pap and os.path.exists(experiment.alignment_pap.path):
            zf.write(experiment.alignment_pap.path, arcname=f"alignments/{os.path.basename(experiment.alignment_pap.path)}")

        # Log
        log_content = f"--- LOG DE EXECUÇÃO MODELLER ---\nStatus: {experiment.status}\nEtapa: {experiment.current_step}\n\n{experiment.log_output}"
        if experiment.error_message:
            log_content += f"\n\n--- ERRO ---\n{experiment.error_message}"
        zf.writestr("execution.log", log_content)

    return zip_rel_path


def run_pipeline(experiment_id):
    """
    Executa o fluxo completo do Smosh / Modeller de forma automatizada:
    1. Preparação da sequência alvo
    2. Busca de templates homólogos (FindTemplatesStep com pdb_95)
    3. Download da estrutura PDB do RCSB
    4. Limpeza e preparação de cadeias (PDBFile)
    5. Extração de sequência do PDB (GetSequenceFromPDBStep)
    6. Alinhamento das sequências alvo e molde (AlignFile e AlignStep)
    7. Construção de modelos 3D comparativos (BuildModelStep)
    8. Avaliação energética DOPE de perfil (MakeProfile e EvaluateEnergy)
    9. (Opcional) Refinamento de Loop (LoopRefinementStep e EvaluateEnergyofLoopRefinementStep)
    10. Finalização e persistência no banco de dados
    """
    experiment = Experiment.objects.get(id=experiment_id)
    experiment.status = 'RUNNING'
    experiment.current_step = 'Iniciando ambiente de trabalho'
    experiment.progress_percent = 5
    experiment.log_output += f"[{timezone.now().strftime('%H:%M:%S')}] Iniciando experimento '{experiment.title}'...\n"
    experiment.save()

    workdir = os.path.join(settings.MEDIA_ROOT, 'workspaces', str(experiment.uuid))
    os.makedirs(workdir, exist_ok=True)

    try:
        # ETAPA 1: Preparar arquivo da sequência alvo
        seq_name = experiment.sequence_name.strip() or "target"
        ext = "pir" if experiment.sequence_type == "PIR" else "fasta"
        seq_file_path = os.path.join(workdir, f"{seq_name}.{ext}")

        content_to_write = experiment.sequence_text
        if experiment.sequence_type == "PIR":
            content_to_write = ensure_pir_format(seq_name, content_to_write)

        with open(seq_file_path, "w") as f:
            f.write(content_to_write)

        experiment.log_output += f"[{timezone.now().strftime('%H:%M:%S')}] Arquivo de sequência salvo em: {os.path.basename(seq_file_path)}\n"
        experiment.current_step = 'Buscando templates homólogos (FindTemplatesStep)'
        experiment.progress_percent = 15
        experiment.save()

        # ETAPA 2: Buscar templates homólogos no pdb_95
        find_step = FindTemplatesStep(seq_file_path, experiment.sequence_type)
        find_step.execute()

        profile_prf_path = os.path.join(workdir, 'build_profile.prf')
        if not os.path.exists(profile_prf_path):
            raise Exception("O perfil de busca de templates 'build_profile.prf' não foi gerado.")

        profile_of_templates = TemplateProfile(profile_prf_path)
        candidates = profile_of_templates.list_of_sequences

        # Registrar candidatos a molde no banco
        TemplateCandidate.objects.filter(experiment=experiment).delete()
        for cand in candidates[:15]:  # Armazena os 15 melhores
            try:
                cand_code = cand.name()
                cand_id = float(cand.identity())
                TemplateCandidate.objects.create(
                    experiment=experiment,
                    code=cand_code,
                    chain=cand_code[-1] if len(cand_code) >= 5 else 'A',
                    identity=cand_id,
                    is_selected=False
                )
            except Exception:
                pass

        # Selecionar o melhor template (ou template escolhido pelo usuário)
        if experiment.selected_template:
            best_template_code = experiment.selected_template.strip()
        else:
            better_profile = profile_of_templates.getBetterProfile()
            best_template_code = better_profile.name()
            experiment.selected_template = best_template_code

        # Marcar template selecionado no banco
        TemplateCandidate.objects.filter(experiment=experiment, code=best_template_code).update(is_selected=True)

        chain = best_template_code[-1] if len(best_template_code) >= 5 else 'A'
        experiment.template_chain = chain
        experiment.log_output += f"[{timezone.now().strftime('%H:%M:%S')}] Template selecionado: {best_template_code} (Cadeia: {chain})\n"
        experiment.current_step = f'Baixando e tratando PDB ({best_template_code})'
        experiment.progress_percent = 30
        experiment.save()

        # ETAPA 3: Obter PDB do molde (RCSB ou local)
        # Verifica se o PDB já existe nos arquivos de teste do smosh
        smosh_base = os.path.join(settings.SMOSH_PARENT_DIR, 'smosh', 'files')
        pdb_id_short = best_template_code[:4].lower()
        local_pdb_sample = os.path.join(smosh_base, f"{pdb_id_short}.pdb")

        downloaded_pdb_path = os.path.join(workdir, f"{pdb_id_short}.pdb")
        if os.path.exists(local_pdb_sample):
            shutil.copyfile(local_pdb_sample, downloaded_pdb_path)
            experiment.log_output += f"[{timezone.now().strftime('%H:%M:%S')}] PDB obtido do repositório local: {pdb_id_short}.pdb\n"
        else:
            template_manager = GetDataFromPDB(workdir, best_template_code)
            downloaded_pdb_path = template_manager.getPDB_File()
            experiment.log_output += f"[{timezone.now().strftime('%H:%M:%S')}] PDB baixado via RCSB: {os.path.basename(downloaded_pdb_path)}\n"

        # ETAPA 4: Filtrar e isolar a cadeia de interesse no PDB
        downloaded_pdb = PDBFile(downloaded_pdb_path, 'r')
        new_pdb = downloaded_pdb_path + ".clean"
        with open(new_pdb, "w") as modified_pdb:
            hetatoms = {chain: downloaded_pdb.hetatomsInChain(chain)}
            modified_pdb.write(downloaded_pdb.const(hetatoms, chain))
        os.rename(new_pdb, downloaded_pdb_path)

        experiment.current_step = 'Extraindo sequência do PDB (GetSequenceFromPDBStep)'
        experiment.progress_percent = 40
        experiment.save()

        # ETAPA 5: Extrair sequência do molde a partir do PDB limpo
        template_seq_manager = GetSequenceFromPDBStep(downloaded_pdb_path, chain, chain)
        template_seq_manager.execute()
        template_seq_file = template_seq_manager.__output_files__[0]

        # ETAPA 6: Montar arquivo conjunto e alinhar (AlignStep)
        experiment.current_step = 'Alinhando sequências alvo e molde (AlignStep)'
        experiment.progress_percent = 50
        experiment.save()

        unaligned_seq_path = os.path.join(workdir, 'unaligned_sequence.pir')
        with open(unaligned_seq_path, 'w') as outfile:
            with open(seq_file_path, 'r') as infile1:
                outfile.write(infile1.read().strip() + "\n")
            with open(os.path.join(workdir, template_seq_file), 'r') as infile2:
                outfile.write(infile2.read().strip() + "\n")

        # Alinhamento das sequências alvo e molde via AlignStep
        align_manager = AlignStep(unaligned_seq_path)
        align_manager.execute()

        ali_path = os.path.join(workdir, 'ali.ali')
        pap_path = os.path.join(workdir, 'ali.pap')

        if os.path.exists(ali_path):
            with open(ali_path, 'rb') as f:
                experiment.alignment_pir.save('ali.ali', ContentFile(f.read()), save=False)
        if os.path.exists(pap_path):
            with open(pap_path, 'rb') as f:
                experiment.alignment_pap.save('ali.pap', ContentFile(f.read()), save=False)

        experiment.log_output += f"[{timezone.now().strftime('%H:%M:%S')}] Alinhamento concluído com sucesso.\n"
        experiment.current_step = 'Construindo modelos 3D com Modeller (BuildModelStep)'
        experiment.progress_percent = 65
        experiment.save()

        # ETAPA 7: Construir modelos 3D com Modeller Automodel
        modeling_manager = BuildModelStep(ali_path, downloaded_pdb_path)
        modeling_manager.execute()

        # Coletar modelos PDB gerados
        pdb_files = [f for f in os.listdir(workdir) if f.startswith(seq_name + '.B') and f.endswith('.pdb')]
        if not pdb_files:
            # Tenta pegar qualquer .B*.pdb
            pdb_files = [f for f in os.listdir(workdir) if '.B9999' in f and f.endswith('.pdb')]

        best_model_path = None
        best_dope = None
        best_ga341 = None

        ExperimentResultModel.objects.filter(experiment=experiment).delete()

        for pdb_filename in pdb_files:
            full_model_path = os.path.join(workdir, pdb_filename)
            scores = parse_pdb_scores(full_model_path)
            
            with open(full_model_path, 'rb') as f:
                db_model = ExperimentResultModel(
                    experiment=experiment,
                    name=pdb_filename,
                    dope_score=scores['dope'],
                    ga341_score=scores['ga341'],
                    is_best=False,
                    is_loop_model=False
                )
                db_model.pdb_file.save(pdb_filename, ContentFile(f.read()), save=True)

            if scores['dope'] is not None:
                if best_dope is None or scores['dope'] < best_dope:
                    best_dope = scores['dope']
                    best_ga341 = scores['ga341']
                    best_model_path = full_model_path
                    experiment.best_model_name = pdb_filename
                    experiment.best_dope_score = best_dope
                    experiment.best_ga341_score = best_ga341

        if not best_model_path and pdb_files:
            best_model_path = os.path.join(workdir, pdb_files[0])
            experiment.best_model_name = pdb_files[0]

        # Marcar o melhor no banco
        if experiment.best_model_name:
            ExperimentResultModel.objects.filter(
                experiment=experiment,
                name=experiment.best_model_name
            ).update(is_best=True)

        experiment.log_output += f"[{timezone.now().strftime('%H:%M:%S')}] Modelagem concluída. Melhor modelo: {experiment.best_model_name} (DOPE: {best_dope})\n"
        experiment.current_step = 'Avaliando energia e gerando perfis DOPE'
        experiment.progress_percent = 80
        experiment.save()

        # ETAPA 8: Avaliação de Energia DOPE (Gráfico)
        profile_mgr_model = MakeProfile(best_model_path)
        profile_mgr_model.execute()

        profile_mgr_tmpl = MakeProfile(downloaded_pdb_path)
        profile_mgr_tmpl.execute()

        eval_energy = EvaluateEnergy(
            ali_path,
            os.path.join(workdir, profile_mgr_tmpl.__output_files__[0]),
            os.path.join(workdir, profile_mgr_model.__output_files__[0])
        )
        eval_energy.execute()

        dope_plot_path = os.path.join(workdir, 'dope_profile_loop.png')
        if os.path.exists(dope_plot_path):
            with open(dope_plot_path, 'rb') as f:
                experiment.dope_plot.save('dope_profile_loop.png', ContentFile(f.read()), save=False)

        # ETAPA 9: Refinamento de Loop (Opcional)
        if experiment.enable_loop_refinement and experiment.loop_start and experiment.loop_end:
            experiment.current_step = f'Refinando loop nos resíduos {experiment.loop_start} a {experiment.loop_end}'
            experiment.progress_percent = 90
            experiment.save()

            loop_step = LoopRefinementStep(best_model_path, experiment.loop_start, experiment.loop_end)
            loop_step.execute()

            loop_files = [f for f in os.listdir(workdir) if f.startswith(seq_name + '.BL') and f.endswith('.pdb')]
            best_loop_path = None
            best_loop_dope = None

            for loop_filename in loop_files:
                full_loop_path = os.path.join(workdir, loop_filename)
                scores = parse_pdb_scores(full_loop_path)
                with open(full_loop_path, 'rb') as f:
                    db_model = ExperimentResultModel(
                        experiment=experiment,
                        name=loop_filename,
                        dope_score=scores['dope'],
                        ga341_score=scores['ga341'],
                        is_best=False,
                        is_loop_model=True
                    )
                    db_model.pdb_file.save(loop_filename, ContentFile(f.read()), save=True)

                if scores['dope'] is not None:
                    if best_loop_dope is None or scores['dope'] < best_loop_dope:
                        best_loop_dope = scores['dope']
                        best_loop_path = full_loop_path

            if best_loop_path:
                prof_loop = MakeProfile(best_loop_path)
                prof_loop.execute()

                eval_loop = EvaluateEnergyofLoopRefinementStep(
                    ali_path,
                    os.path.join(workdir, profile_mgr_tmpl.__output_files__[0]),
                    os.path.join(workdir, profile_mgr_model.__output_files__[0]),
                    os.path.join(workdir, prof_loop.__output_files__[0])
                )
                eval_loop.execute()

                if os.path.exists(dope_plot_path):
                    with open(dope_plot_path, 'rb') as f:
                        experiment.dope_plot.save('dope_profile_loop.png', ContentFile(f.read()), save=False)

        # ETAPA 10: Finalização com Sucesso
        experiment.status = 'COMPLETED'
        experiment.current_step = 'Concluído com sucesso'
        experiment.progress_percent = 100
        experiment.log_output += f"[{timezone.now().strftime('%H:%M:%S')}] Processo finalizado com sucesso!\n"
        experiment.save()

    except ModellerException as me:
        experiment.status = 'FAILED'
        experiment.current_step = 'Falha na execução do Modeller'
        experiment.error_message = f"ModellerException: {me.log}"
        experiment.log_output += f"\n[{timezone.now().strftime('%H:%M:%S')}] ERRO DO MODELLER:\n{me.log}\n"
        experiment.save()
    except Exception as e:
        experiment.status = 'FAILED'
        experiment.current_step = f'Erro: {str(e)}'
        experiment.error_message = str(e)
        experiment.log_output += f"\n[{timezone.now().strftime('%H:%M:%S')}] ERRO INESPERADO:\n{str(e)}\n"
        experiment.save()


def start_experiment_async(experiment_id):
    """Dispara a execução do experimento em uma thread em segundo plano."""
    t = threading.Thread(target=run_pipeline, args=(experiment_id,), daemon=True)
    t.start()
    return t
