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


if __name__ == '__main__':
    unittest.main()
