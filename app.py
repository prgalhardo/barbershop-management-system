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

    # Filtro (GET tem prioridade)
    data_filtro = request.args.get("data") or request.form.get("data")
    servico_filtro = request.args.get("servico") or request.form.get("servico")

    duracao_selecionada = duracao_servicos.get(servico_filtro, 30)

    # CADASTRAR AGENDAMENTO
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

            duracao = duracao_servicos.get(servico, 60)
            data_fim = data_obj + timedelta(minutes=duracao)

            # Regra 1: dias permitidos
            if data_obj.weekday() < 1 or data_obj.weekday() > 5:
                erro = "Atendemos apenas de terça a sábado."

            # Regra 2: horário permitido
            elif data_obj.hour < 8 or data_obj.hour >= 18:
                erro = "Horário permitido é das 08h às 18h."

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

                # Regra 3: conflito de horários
                for data_str, duracao_existente in agendamentos_db:
                    inicio_existente = datetime.strptime(data_str, "%Y-%m-%d %H:%M")
                    fim_existente = inicio_existente + timedelta(minutes=duracao_existente)

                    if not (data_fim <= inicio_existente or data_obj >= fim_existente):
                        erro = "Este horário já está ocupado."
                        break

            # Salva se estiver ok
            if not erro:
                conn = sqlite3.connect("barbearia.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO agendamentos (nome, servico, data, duracao)
                VALUES (?, ?, ?, ?)
                """, (nome, servico, data_completa, duracao))

                conn.commit()
                conn.close()

    # BUSCAR AGENDAMENTOS DO DIA (ORDENADO)
    conn = sqlite3.connect("barbearia.db")
    cursor = conn.cursor()

    if data_filtro:
        cursor.execute("""
            SELECT nome, servico, data 
            FROM agendamentos 
            WHERE data LIKE ?
            ORDER BY data
        """, (f"{data_filtro}%",))
        dados = cursor.fetchall()
    else:
        dados = []

    conn.close()

    agendamentos = []

    for ag in dados:
        data_formatada = datetime.strptime(
            ag[2], "%Y-%m-%d %H:%M"
        ).strftime("%d/%m/%Y às %H:%M")

        agendamentos.append({
            "nome": ag[0],
            "servico": ag[1],
            "data": data_formatada
        })

    # GERAR HORÁRIOS (BOTÕES)
    horarios = []

    if data_filtro:
        inicio_dia = datetime.strptime("08:00", "%H:%M")
        fim_dia = datetime.strptime("18:00", "%H:%M")

        conn = sqlite3.connect("barbearia.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data, duracao FROM agendamentos
            WHERE data LIKE ?
        """, (f"{data_filtro}%",))

        agendamentos_db = cursor.fetchall()
        conn.close()

        atual = inicio_dia

        while atual < fim_dia:
            hora_str = atual.strftime("%H:%M")

            inicio_teste = atual
            fim_teste = inicio_teste + timedelta(minutes=duracao_selecionada)

            ocupado = False

            for data_str, duracao_existente in agendamentos_db:
                inicio_existente = datetime.strptime(data_str, "%Y-%m-%d %H:%M")
                fim_existente = inicio_existente + timedelta(minutes=duracao_existente)

                if not (fim_teste <= inicio_existente or inicio_teste >= fim_existente):
                    ocupado = True
                    break

            if fim_teste > fim_dia:
                ocupado = True

            horarios.append({
                "hora": hora_str,
                "ocupado": ocupado
            })

            atual += timedelta(minutes=30)

    return render_template(
        "index.html",
        agendamentos=agendamentos,
        erro=erro,
        data_filtro=data_filtro,
        horarios=horarios
    )


if __name__ == "__main__":
    criar_tabela()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))