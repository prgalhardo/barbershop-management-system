import unittest
import json
from app import app, criar_tabelas

class TestBarbeariaAPI(unittest.TestCase):

    def setUp(self):
        # Configura o app para modo de teste
        app.config["TESTING"] = True
        self.client = app.test_client()
        # Garante que as tabelas existam
        criar_tabelas()

    def test_listar_servicos(self):
        """Testa se a rota /api/v1/servicos retorna 200 e lista os servicos"""
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

    def test_criar_agendamento(self):
        """Testa a criacao de um agendamento via POST /api/v1/agendamentos"""
        payload = {
            "nome": "Cliente Teste",
            "servico_id": 1,
            "data_hora": "2026-10-20 10:00"
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

if __name__ == "__main__":
    unittest.main()