from flask import Flask, render_template, request, redirect, url_for
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

# EDITAR (UPDATE)
@app.route("/editar/<int:id>")
def editar(id):
    conn = sqlite3.connect("barbearia.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, servico, data
        FROM agendamentos
        WHERE id = ?
    """, (id,))

    ag = cursor.fetchone()
    conn.close()

    if not ag:
        return redirect("/")

    data_obj = datetime.strptime(ag[3], "%Y-%m-%d %H:%M")

    return redirect(url_for(
        "home",
        editar_id=ag[0],
        nome=ag[1],
        servico=ag[2],
        data=data_obj.strftime("%Y-%m-%d"),
        hora=data_obj.strftime("%H:%M")
    ))

# DELETAR (DELETE)
@app.route("/deletar/<int:id>", methods=["POST"])
def deletar(id):
    conn = sqlite3.connect("barbearia.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM agendamentos WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")

# HOME
@app.route("/", methods=["GET", "POST"])
def home():
    erro = None

    data_filtro = request.args.get("data") or request.form.get("data")
    servico_filtro = request.args.get("servico") or request.form.get("servico")
    editar_id = request.args.get("editar_id") or request.form.get("editar_id")

    if not servico_filtro:
        duracao_selecionada = 60  # bloqueia mais horários
    else:
        duracao_selecionada = duracao_servicos.get(servico_filtro, 60)

    # CADASTRAR / ATUALIZAR
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

            if data_obj.weekday() < 1 or data_obj.weekday() > 5:
                erro = "Atendemos apenas de terça a sábado."

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

                for data_str, duracao_existente in agendamentos_db:
                    inicio_existente = datetime.strptime(data_str, "%Y-%m-%d %H:%M")
                    fim_existente = inicio_existente + timedelta(minutes=duracao_existente)

                    if not (data_fim <= inicio_existente or data_obj >= fim_existente):
                        erro = "Este horário já está ocupado."
                        break

            if not erro:
                conn = sqlite3.connect("barbearia.db")
                cursor = conn.cursor()

                if editar_id:
                    cursor.execute("""
                        UPDATE agendamentos
                        SET nome = ?, servico = ?, data = ?, duracao = ?
                        WHERE id = ?
                    """, (nome, servico, data_completa, duracao, editar_id))
                else:
                    cursor.execute("""
                        INSERT INTO agendamentos (nome, servico, data, duracao)
                        VALUES (?, ?, ?, ?)
                    """, (nome, servico, data_completa, duracao))

                conn.commit()
                conn.close()

                return redirect("/")

    # LISTAR AGENDAMENTOS
    conn = sqlite3.connect("barbearia.db")
    cursor = conn.cursor()

    if data_filtro:
        cursor.execute("""
            SELECT id, nome, servico, data 
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
            ag[3], "%Y-%m-%d %H:%M"
        ).strftime("%d/%m/%Y às %H:%M")

        agendamentos.append({
            "id": ag[0],
            "nome": ag[1],
            "servico": ag[2],
            "data": data_formatada
        })

    # GERAR HORÁRIOS
    horarios = []

    if data_filtro:
        data_base = datetime.strptime(data_filtro, "%Y-%m-%d")
        inicio_dia = data_base.replace(hour=8, minute=0)
        fim_dia = data_base.replace(hour=18, minute=0)

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