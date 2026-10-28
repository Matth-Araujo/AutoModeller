import unittest
import uuid
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from should_dsl import should, should_not

from experiments.models import Experiment, ExperimentResultModel, TemplateCandidate
from experiments.services import ensure_pir_format, parse_pdb_scores
from experiments.forms import RegisterForm, ExperimentCreateForm


class ExperimentModelShouldDslTests(TestCase):
    """Testes dos modelos de dados utilizando should_dsl."""

    def setUp(self):
        self.user = User.objects.create_user(username='biologo_teste@email.com', email='biologo_teste@email.com', password='password123')

    def test_anonymous_experiment_is_guest(self):
        exp = Experiment.objects.create(
            title="Modelagem Avulsa",
            sequence_name="ProtA",
            sequence_text="MSEAAHVLITGAAGQIGYIL*",
            session_key="session_guest_xyz"
        )
        exp.is_guest |should| equal_to(True)
        exp.user |should| equal_to(None)
        exp.status |should| equal_to('PENDING')
        exp.progress_percent |should| equal_to(0)

    def test_authenticated_experiment_is_not_guest(self):
        exp = Experiment.objects.create(
            user=self.user,
            title="Modelagem com Conta",
            sequence_name="ProtB",
            sequence_text="MSEAAHVLITGAAGQIGYIL*"
        )
        exp.is_guest |should| equal_to(False)
        exp.user.email |should| equal_to('biologo_teste@email.com')

    def test_best_result_model_property(self):
        exp = Experiment.objects.create(
            title="Teste Best Model",
            sequence_name="ProtC",
            sequence_text="MSEAAHVLITGAAGQIGYIL*"
        )
        m1 = ExperimentResultModel.objects.create(
            experiment=exp,
            name="ProtC.B99990001.pdb",
            dope_score=-32000.5,
            is_best=False
        )
        m2 = ExperimentResultModel.objects.create(
            experiment=exp,
            name="ProtC.B99990002.pdb",
            dope_score=-38500.2,
            is_best=True
        )

        exp.best_result_model.name |should| equal_to("ProtC.B99990002.pdb")
        exp.best_result_model.dope_score |should| equal_to(-38500.2)

    def test_ensure_pir_format_generator(self):
        raw_seq = "MSEAAHVLITGAAGQIGYIL"
        pir_out = ensure_pir_format("TvLDH", raw_seq)
        pir_out.startswith(">P1;TvLDH") |should| equal_to(True)
        pir_out.endswith("*\n") or pir_out.endswith("*") |should| equal_to(True)

    def test_ensure_pir_format_preserves_existing_header(self):
        existing_pir = ">P1;MySeq\nsequence:MySeq:::::::0.00: 0.00\nMSEAAHVLITGAAGQIGYIL*\n"
        pir_out = ensure_pir_format("MySeq", existing_pir)
        pir_out |should| equal_to(existing_pir)


class ExperimentViewsShouldDslTests(TestCase):
    """Testes das views e rotas web utilizando should_dsl."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='pesquisador1@email.com',
            email='pesquisador1@email.com',
            password='secret123',
            first_name='Pesquisador'
        )

    def test_home_page_status_code_and_elements(self):
        response = self.client.get('/')
        response.status_code |should| equal_to(200)
        content_str = response.content.decode('utf-8')
        content_str |should| include("AutoModeller")
        content_str |should| include("Modeller")
        # Default language is English
        content_str |should| include("Featured 3D Structures")
        # Removed cards should NOT be present
        content_str |should_not| include("Previsão Estrutural 3D Automática")
        content_str |should_not| include("Busca & Alinhamento de Moldes")
        content_str |should_not| include("Validação DOPE & Visualização HTML5")

    def test_language_switch_to_portuguese(self):
        # Switch language to Portuguese
        switch_response = self.client.get('/set-language/?lang=pt&next=/')
        switch_response.status_code |should| equal_to(302)

        # GET homepage again with session cookie set
        response = self.client.get('/')
        response.status_code |should| equal_to(200)
        content_str = response.content.decode('utf-8')
        content_str |should| include("Estruturas 3D em Destaque")
        content_str |should| include("Modelagem Molecular 3D")

    @patch('experiments.views.start_experiment_async')
    def test_create_guest_experiment_automatic_sequence_name(self, mock_start_async):
        # Envia sem campo sequence_name, verificando a auto-detecção da sequência
        payload = {
            'title': 'Experimento Avulso Teste',
            'sequence_type': 'PIR',
            'sequence_text': '>P1;TesteAutoGuest\nsequence:TesteAutoGuest:::::::0.00: 0.00\nMSEAAHVLITGAAGQIGYIL*\n',
        }
        response = self.client.post('/experiments/new/', data=payload)
        response.status_code |should| equal_to(302)
        mock_start_async.called |should| equal_to(True)

        exp = Experiment.objects.get(sequence_name='TesteAutoGuest')
        exp.title |should| equal_to('Experimento Avulso Teste')
        exp.is_guest |should| equal_to(True)
        exp.session_key |should_not| equal_to('')

    def test_status_api_endpoint(self):
        exp = Experiment.objects.create(
            title="Experimento API",
            sequence_name="ApiSeq",
            sequence_text="MSEAAHVLITGAAGQIGYIL*",
            status='RUNNING',
            current_step='Construindo Modelos',
            progress_percent=65,
            best_dope_score=-35400.1
        )
        response = self.client.get(f'/experiments/{exp.uuid}/status/')
        response.status_code |should| equal_to(200)

        data = response.json()
        data['status'] |should| equal_to('RUNNING')
        data['current_step'] |should| equal_to('Construindo Modelos')
        data['progress_percent'] |should| equal_to(65)
        data['best_dope_score'] |should| equal_to(-35400.1)

    @patch('experiments.views.start_experiment_async')
    def test_authenticated_user_experiment_association(self, mock_start_async):
        self.client.login(username='pesquisador1@email.com', password='secret123')
        payload = {
            'sequence_type': 'FASTA',
            'sequence_text': '>ProtUser\nMSEAAHVLITGAAGQIGYIL\n',
        }
        response = self.client.post('/experiments/new/', data=payload)
        response.status_code |should| equal_to(302)
        mock_start_async.called |should| equal_to(True)

        exp = Experiment.objects.get(sequence_name='ProtUser')
        exp.is_guest |should| equal_to(False)
        exp.user.email |should| equal_to('pesquisador1@email.com')
        exp.title |should| equal_to('Modeling ProtUser')

    def test_email_backend_login(self):
        # Testa login autenticado pelo e-mail
        logged_in = self.client.login(username='pesquisador1@email.com', password='secret123')
        logged_in |should| equal_to(True)

    def test_register_form_without_username(self):
        form_data = {
            'first_name': 'Novo',
            'last_name': 'Pesquisador',
            'email': 'novo@laboratorio.org',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
        }
        form = RegisterForm(data=form_data)
        form.is_valid() |should| equal_to(True)
        user = form.save()
        user.email |should| equal_to('novo@laboratorio.org')
        user.username |should| equal_to('novo@laboratorio.org')

    def test_daily_featured_structures_rotation(self):
        from experiments.featured import get_daily_featured_structures, FEATURED_CATALOG
        import datetime

        d1 = datetime.date(2026, 10, 7)
        d2 = datetime.date(2026, 10, 8)

        structs_d1 = get_daily_featured_structures(target_date=d1, count=4, is_pt=True)
        structs_d2 = get_daily_featured_structures(target_date=d2, count=4, is_pt=True)

        len(structs_d1) |should| equal_to(4)
        len(structs_d2) |should| equal_to(4)

        # A seleção deve ser determinística no mesmo dia
        structs_d1_repeat = get_daily_featured_structures(target_date=d1, count=4, is_pt=True)
        [s['id'] for s in structs_d1] |should| equal_to([s['id'] for s in structs_d1_repeat])

        # Cada estrutura deve ter chaves essenciais
        for s in structs_d1:
            ('id' in s) |should| equal_to(True)
            ('name' in s) |should| equal_to(True)
            ('organism' in s) |should| equal_to(True)
            ('badge' in s) |should| equal_to(True)
            ('desc' in s) |should| equal_to(True)
            ('pdbUrl' in s) |should| equal_to(True)

    def test_featured_shuffle_api(self):
        response = self.client.get('/api/featured/shuffle/?offset=3')
        response.status_code |should| equal_to(200)

        data = response.json()
        data['status'] |should| equal_to('ok')
        data['offset'] |should| equal_to(3)
        len(data['structures']) |should| equal_to(4)

    def test_home_page_featured_structures(self):
        response = self.client.get('/')
        response.status_code |should| equal_to(200)
        ('featured_structures' in response.context) |should| equal_to(True)
        len(response.context['featured_structures']) |should| equal_to(4)
        ('today_str' in response.context) |should| equal_to(True)

    @patch('experiments.views.start_experiment_async')
    def test_create_experiment_quick_mode_redirects_to_detail(self, mock_start_async):
        payload = {
            'title': 'Quick Mode Test',
            'sequence_type': 'PIR',
            'pipeline_mode': 'AUTO',
            'sequence_text': '>P1;QuickProt\nsequence:QuickProt:::::::0.00: 0.00\nMSEAAHVLITGAAGQIGYIL*\n',
        }
        response = self.client.post('/experiments/new/', data=payload)
        response.status_code |should| equal_to(302)
        mock_start_async.called |should| equal_to(True)
        exp = Experiment.objects.get(sequence_name='QuickProt')
        response.url |should| equal_to(f'/experiments/{exp.uuid}/')

    @patch('experiments.views.start_experiment_async')
    def test_create_experiment_step_mode_redirects_to_template_select(self, mock_start_async):
        payload = {
            'title': 'Step Parameter Mode Test',
            'sequence_type': 'PIR',
            'pipeline_mode': 'STEP',
            'sequence_text': '>P1;StepProt\nsequence:StepProt:::::::0.00: 0.00\nMSEAAHVLITGAAGQIGYIL*\n',
        }
        response = self.client.post('/experiments/new/', data=payload)
        response.status_code |should| equal_to(302)
        mock_start_async.called |should| equal_to(True)
        exp = Experiment.objects.get(sequence_name='StepProt')
        response.url |should| equal_to(f'/experiments/{exp.uuid}/select-template/')

    @patch('experiments.views.start_model_building_async')
    def test_template_select_flow_and_submission(self, mock_build_async):
        exp = Experiment.objects.create(
            title="Interactive Selection Test",
            sequence_name="SelectProt",
            sequence_text="MSEAAHVLITGAAGQIGYIL*",
            pipeline_mode="STEP",
            status="AWAITING_TEMPLATE",
            current_step="Aguardando seleção do molde homólogo"
        )
        cand1 = TemplateCandidate.objects.create(experiment=exp, code="1bdm", chain="A", identity=45.2, is_selected=True)
        cand2 = TemplateCandidate.objects.create(experiment=exp, code="1smk", chain="A", identity=38.1, is_selected=False)

        # GET da página de seleção
        get_res = self.client.get(f'/experiments/{exp.uuid}/select-template/')
        get_res.status_code |should| equal_to(200)
        len(get_res.context['candidates']) |should| equal_to(2)

        # POST confirmando seleção
        post_payload = {
            'template_code': '1smk',
            'template_chain': 'A',
            'num_models': 6,
            'enable_loop_refinement': True,
            'loop_start': 15,
            'loop_end': 25,
        }
        post_res = self.client.post(f'/experiments/{exp.uuid}/select-template/', data=post_payload)
        post_res.status_code |should| equal_to(302)
        post_res.url |should| equal_to(f'/experiments/{exp.uuid}/')
        mock_build_async.called |should| equal_to(True)

        exp.refresh_from_db()
        exp.selected_template |should| equal_to('1SMK')
        exp.num_models |should| equal_to(6)
        exp.enable_loop_refinement |should| equal_to(True)
        exp.loop_start |should| equal_to(15)
        exp.loop_end |should| equal_to(25)

    def test_alignment_data_and_status_api(self):
        from django.core.files.base import ContentFile
        from experiments.services import get_alignment_data

        exp = Experiment.objects.create(
            title="Alignment Test",
            sequence_name="AlignProt",
            sequence_text="MSEAAHVLITGAAGQIGYIL*",
            status="RUNNING",
            selected_template="1BDM"
        )
        sample_pap = "_aln.pos 10 20\nTarget MSEAAH\n1BDM   M-EAAH\n_consrvd * ****"
        sample_pir = ">P1;AlignProt\nsequence:AlignProt:::::::0.00: 0.00\nMSEAAH*\n>P1;1BDM\nstructureX:1BDM:0:A:+10:A::::\nM-EAAH*\n"

        exp.alignment_pap.save('test_ali.pap', ContentFile(sample_pap.encode('utf-8')))
        exp.alignment_pir.save('test_ali.ali', ContentFile(sample_pir.encode('utf-8')))
        exp.save()

        data = get_alignment_data(exp)
        data['has_alignment'] |should| equal_to(True)
        data['conserved_count'] |should| equal_to(5)
        data['pap_text'] |should| include('_aln.pos')

        # API de status
        res = self.client.get(f'/experiments/{exp.uuid}/status/')
        res.status_code |should| equal_to(200)
        json_data = res.json()
        json_data['alignment_data']['has_alignment'] |should| equal_to(True)
        json_data['alignment_data']['conserved_count'] |should| equal_to(5)
        json_data['selected_template'] |should| equal_to('1BDM')

    def test_featured_structure_prepopulates_experiment_form(self):
        res = self.client.get('/experiments/new/?structure=1crn')
        res.status_code |should| equal_to(200)
        form = res.context['form']
        form.initial['sequence_name'] |should| equal_to('1crn')
        form.initial['sequence_text'] |should| include('>P1;1crn')
        form.initial['sequence_text'] |should| include('TTCCPSIVARSNFNVCRLPGTPEAICATYT')

    def test_privacy_and_cookie_policy_pages_and_security_headers(self):
        res_privacy = self.client.get('/privacy/')
        res_privacy.status_code |should| equal_to(200)
        res_privacy.content.decode('utf-8') |should| include('LGPD')
        res_privacy['X-Content-Type-Options'] |should| equal_to('nosniff')
        res_privacy['X-Frame-Options'] |should| equal_to('DENY')
        res_privacy['Content-Security-Policy'] |should| include("default-src 'self'")

        res_cookies = self.client.get('/cookies/')
        res_cookies.status_code |should| equal_to(200)
        res_cookies.content.decode('utf-8') |should| include('csrftoken')
        res_cookies.content.decode('utf-8') |should| include('sessionid')

    def test_open_redirect_protection_in_set_language(self):
        res = self.client.get('/set-language/?lang=pt&next=https://evil-attacker.example.com/phishing')
        res.status_code |should| equal_to(302)
        res.url |should| equal_to('/')

        res_proto = self.client.get('/set-language/?lang=pt&next=//evil-attacker.example.com')
        res_proto.status_code |should| equal_to(302)
        res_proto.url |should| equal_to('/')

    def test_security_upload_and_xss_sanitization(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Rejeita extensão maliciosa (.php)
        bad_file = SimpleUploadedFile("shell.php", b"<?php system($_GET['cmd']); ?>")
        form_bad = ExperimentCreateForm(data={'sequence_type': 'PIR'}, files={'sequence_file': bad_file})
        form_bad.is_valid() |should| equal_to(False)

        # Rejeita payload binário com null bytes disfarçado de .pir
        bin_file = SimpleUploadedFile("malware.pir", b">P1;Test\x00\x00BINARY_PAYLOAD")
        form_bin = ExperimentCreateForm(data={'sequence_type': 'PIR'}, files={'sequence_file': bin_file})
        form_bin.is_valid() |should| equal_to(False)

        # Remove tags XSS do título e descrição
        form_xss = ExperimentCreateForm(data={
            'title': '<script>alert(1)</script>Safe Title',
            'description': '<img src=x onerror=alert(1)>Safe Desc',
            'sequence_type': 'FASTA',
            'sequence_text': '>MyProt\nMSEAAHVLITGAAGQIGYIL*\n',
        })
        form_xss.is_valid() |should| equal_to(True)
        form_xss.cleaned_data['title'] |should| equal_to('alert(1)Safe Title')
        form_xss.cleaned_data['description'] |should| equal_to('Safe Desc')

    def test_admin_access_restricted_to_superuser_only(self):
        # 1. Visitante anônimo é redirecionado para a tela de login do admin
        res_anon = self.client.get('/admin/')
        res_anon.status_code |should| equal_to(302)
        res_anon.url |should| include('/admin/login/')

        # 2. Usuário comum cadastrado no site NÃO tem acesso ao painel /admin/
        normal_user = User.objects.create_user(
            username='pesquisador_comum',
            email='pesquisador@teste.com',
            password='StrongPassword123!'
        )
        self.client.force_login(normal_user)
        res_normal = self.client.get('/admin/')
        res_normal.status_code |should| equal_to(302)
        res_normal.url |should| include('/admin/login/')

        # 3. Apenas Superusuário (is_staff=True, is_superuser=True) consegue acessar
        admin_user = User.objects.create_superuser(
            username='admin_master',
            email='admin@automodeller.org',
            password='SuperSecretAdminPass123!'
        )
        self.client.force_login(admin_user)
        res_admin = self.client.get('/admin/')
        res_admin.status_code |should| equal_to(200)


if __name__ == '__main__':
    unittest.main()

