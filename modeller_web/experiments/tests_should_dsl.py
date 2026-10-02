import unittest
import uuid
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from should_dsl import should, should_not

from experiments.models import Experiment, ExperimentResultModel, TemplateCandidate
from experiments.services import ensure_pir_format, parse_pdb_scores


class ExperimentModelShouldDslTests(TestCase):
    """Testes dos modelos de dados utilizando should_dsl."""

    def setUp(self):
        self.user = User.objects.create_user(username='biologo_teste', password='password123')

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
        exp.user.username |should| equal_to('biologo_teste')

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
        self.user = User.objects.create_user(username='pesquisador1', password='secret123')

    def test_home_page_status_code_and_elements(self):
        response = self.client.get('/')
        response.status_code |should| equal_to(200)
        str(response.content) |should| include("Modeller")
        str(response.content) |should| include("smosh")
        str(response.content) |should| include("Iniciar Experimento Avulso")

    @patch('experiments.views.start_experiment_async')
    def test_create_guest_experiment_post(self, mock_start_async):
        payload = {
            'title': 'Experimento Avulso Teste',
            'sequence_name': 'TesteGuest',
            'sequence_type': 'PIR',
            'sequence_text': '>P1;TesteGuest\nsequence:TesteGuest:::::::0.00: 0.00\nMSEAAHVLITGAAGQIGYIL*\n',
        }
        response = self.client.post('/experiments/new/', data=payload)
        response.status_code |should| equal_to(302)
        mock_start_async.called |should| equal_to(True)

        exp = Experiment.objects.get(sequence_name='TesteGuest')
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
        self.client.login(username='pesquisador1', password='secret123')
        payload = {
            'title': 'Experimento do Pesquisador',
            'sequence_name': 'ProtUser',
            'sequence_type': 'FASTA',
            'sequence_text': '>ProtUser\nMSEAAHVLITGAAGQIGYIL\n',
        }
        response = self.client.post('/experiments/new/', data=payload)
        response.status_code |should| equal_to(302)
        mock_start_async.called |should| equal_to(True)

        exp = Experiment.objects.get(sequence_name='ProtUser')
        exp.is_guest |should| equal_to(False)
        exp.user.username |should| equal_to('pesquisador1')


if __name__ == '__main__':
    unittest.main()
