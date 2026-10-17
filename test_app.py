import unittest
import json
import sqlite3
from app import app, criar_tabelas, duracao_servicos

class TestBarbearia(unittest.TestCase):

    def setUp(self):
        # Configura o app para modo de teste
        app.config["TESTING"] = True
        self.client = app.test_client()
        # Garante que as tabelas existam
        criar_tabelas()

    # --- TESTES DAS ROTAS REST (APIs) ---

    def test_listar_servicos(self):
        """Testa se a rota /api/v1/servicos retorna 200 e lista os servicos cadastrados"""
        resposta = self.client.get("/api/v1/servicos")
        self.assertEqual(resposta.status_code, 200)
        
        dados = json.loads(resposta.data.decode("utf-8"))
        self.assertIsInstance(dados, list)
        self.assertGreater(len(dados), 0)
        self.assertIn("nome", dados[0])
        self.assertIn("duracao", dados[0])

    def test_horarios_sem_parametros(self):
        """Testa se a rota /api/v1/horarios-disponiveis devolve erro 400 sem filtros"""
        resposta = self.client.get("/api/v1/horarios-disponiveis")
        self.assertEqual(resposta.status_code, 400)

    def test_horarios_com_parametros_validos(self):
        """Testa o endpoint assíncrono consumido pelo Fetch no front-end"""
        # 2026-10-21 é uma quarta-feira (serviço id 1 = Corte)
        resposta = self.client.get("/api/v1/horarios-disponiveis?data=2026-10-21&servico_id=1")
        self.assertEqual(resposta.status_code, 200)

        dados = json.loads(resposta.data.decode("utf-8"))
        self.assertIsInstance(dados, list)
        self.assertGreater(len(dados), 0)
        self.assertIn("hora", dados[0])
        self.assertIn("ocupado", dados[0])

    def test_api_agendamentos_do_dia(self):
        """Testa a rota da API que lista os agendamentos cadastrados para um dia em JSON"""
        resposta = self.client.get("/api/v1/agendamentos-do-dia?data=2026-10-21")
        self.assertEqual(resposta.status_code, 200)
        dados = json.loads(resposta.data.decode("utf-8"))
        self.assertIsInstance(dados, list)

    def test_criar_agendamento_api_sucesso(self):
        """Testa a criacao de um agendamento via POST /api/v1/agendamentos"""
        payload = {
            "nome": "Cliente Teste API",
            "servico_id": 1,
            "data_hora": "2026-10-21 14:00"
        }
        resposta = self.client.post(
            "/api/v1/agendamentos",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 201)
        dados = json.loads(resposta.data.decode("utf-8"))
        self.assertIn("id", dados)
        self.assertEqual(dados["mensagem"], "Agendamento registrado com sucesso.")

    def test_criar_agendamento_api_incompleto(self):
        """Testa se a tentativa de criacao sem os campos obrigatorios devolve erro 400"""
        payload = {
            "nome": "Cliente Incompleto"
        }
        resposta = self.client.post(
            "/api/v1/agendamentos",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 400)

    # --- TESTES DE REGRAS DE NEGÓCIO E CONFLITOS (QUINZENA 5) ---

    def test_validacao_formulario_campos_vazios(self):
        """Garante bloqueio de submissão do formulário sem data e hora"""
        resposta = self.client.post("/", data={
            "nome": "Cliente Sem Horario",
            "servico": "Corte",
            "data": "",
            "hora": ""
        })
        self.assertIn("Preencha a data e a hora.".encode("utf-8"), resposta.data)

    def test_bloqueio_dia_sem_expediente(self):
        """Garante bloqueio de agendamentos no domingo e na segunda-feira"""
        # 18/10/2026 é Domingo
        resposta_domingo = self.client.post("/", data={
            "nome": "Cliente Domingo",
            "servico": "Corte",
            "data": "2026-10-18",
            "hora": "10:00"
        })
        self.assertIn("Atendemos apenas de terça a sábado.".encode("utf-8"), resposta_domingo.data)

    def test_bloqueio_fora_do_horario_comercial(self):
        """Garante que o agendamento só é aceito das 08h às 18h"""
        # Tentativa às 07:00 (antes das 08h)
        resposta_cedo = self.client.post("/", data={
            "nome": "Cliente Madrugador",
            "servico": "Corte",
            "data": "2026-10-21",
            "hora": "07:00"
        })
        self.assertIn("Horário permitido é das 08h às 18h.".encode("utf-8"), resposta_cedo.data)

    def test_conflito_sobreposicao_de_horarios(self):
        """Valida que o sistema impede dois agendamentos no mesmo intervalo"""
        # 1. Cria um primeiro agendamento às 15:00 de quarta-feira (Corte = 60 min, ocupa até 16:00)
        self.client.post("/", data={
            "nome": "Cliente 1 Conflito",
            "servico": "Corte",
            "data": "2026-10-21",
            "hora": "15:00"
        })

        # 2. Tenta agendar no meio desse intervalo (15:30)
        resposta_conflito = self.client.post("/", data={
            "nome": "Cliente 2 Conflito",
            "servico": "Barba",
            "data": "2026-10-21",
            "hora": "15:30"
        })

        # O sistema deve barrar com a mensagem de horário ocupado
        self.assertIn("Este horário já está ocupado.".encode("utf-8"), resposta_conflito.data)

if __name__ == "__main__":
    unittest.main()