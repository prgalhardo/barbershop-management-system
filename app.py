from flask import Flask, render_template, request
from datetime import datetime, timedelta
import os
import sqlite3

app = Flask(__name__)

duracao_servicos = {
    "Corte": 60,
    "Barba": 30,
    "Corte + Barba": 60,
    "Sobrancelha": 30
}

def criar_tabela():
    conn = sqlite3.connect("barbearia.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        servico TEXT,
        data TEXT,
        duracao INTEGER
    )
    """)

    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def home():
    erro = None

    # Filtro unificado (prioriza GET, depois POST)
    data_filtro = request.args.get("data") or request.form.get("data")

    if request.method == "POST":
        nome = request.form.get("nome")
        servico = request.form.get("servico")
        data = request.form.get("data")
        hora = request.form.get("hora")

        if not data or not hora:
            erro = "Preencha a data e a hora."
        else:
            data_completa = f"{data} {hora}"
            data_obj = datetime.strptime(data_completa, "%Y-%m-%d %H:%M")

            # Calcula duração
            duracao = duracao_servicos.get(servico, 60)
            data_fim = data_obj + timedelta(minutes=duracao)

            # Regra 1: dia da semana (terça a sábado)
            if data_obj.weekday() < 1 or data_obj.weekday() > 5:
                erro = "Atendemos apenas de terça a sábado."

            # Regra 2: horário (08h às 18h)
            elif data_obj.hour < 8 or data_obj.hour >= 18:
                erro = "Horário permitido é das 08h às 18h."

            # Regra 3: conflito inteligente
            else:
                conn = sqlite3.connect("barbearia.db")
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT data, duracao 
                    FROM agendamentos 
                    WHERE data LIKE ?
                """, (f"{data}%",))
                agendamentos_db = cursor.fetchall()

                conn.close()

                for ag in agendamentos_db:
                    inicio_existente = datetime.strptime(ag[0], "%Y-%m-%d %H:%M")
                    duracao_existente = ag[1]
                    fim_existente = inicio_existente + timedelta(minutes=duracao_existente)

                    if (data_obj < fim_existente) and (data_fim > inicio_existente):
                        erro = "Este horário já está ocupado."
                        break

            # Salva no banco se não houver erro
            if not erro:
                conn = sqlite3.connect("barbearia.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO agendamentos (nome, servico, data, duracao)
                VALUES (?, ?, ?, ?)
                """, (nome, servico, data_completa, duracao))

                conn.commit()
                conn.close()

    # Busca no banco com filtro por data
    conn = sqlite3.connect("barbearia.db")
    cursor = conn.cursor()

    if data_filtro:
        cursor.execute("""
            SELECT nome, servico, data 
            FROM agendamentos 
            WHERE data LIKE ?
        """, (f"{data_filtro}%",))
        dados = cursor.fetchall()
    else:
        dados = []

    conn.close()

    agendamentos = []

    for ag in dados:
        data_formatada = datetime.strptime(ag[2], "%Y-%m-%d %H:%M").strftime("%d/%m/%Y às %H:%M")

        agendamentos.append({
            "nome": ag[0],
            "servico": ag[1],
            "data": data_formatada
        })

    return render_template(
        "index.html",
        agendamentos=agendamentos,
        erro=erro,
        data_filtro=data_filtro
    )

if __name__ == "__main__":
    criar_tabela()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))