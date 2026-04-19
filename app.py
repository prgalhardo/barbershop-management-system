from flask import Flask, render_template, request
from datetime import datetime, timedelta
import os

app = Flask(__name__)

agendamentos = []

duracao_servicos = {
    "Corte": 60,
    "Barba": 30,
    "Corte + Barba": 60,
    "Sobrancelha": 30
}

@app.route("/", methods=["GET", "POST"])
def home():
    erro = None

    if request.method == "POST":
        nome = request.form.get("nome")
        servico = request.form.get("servico")
        data = request.form.get("data")
        hora = request.form.get("hora")

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

        # Regra 3: conflito inteligente (intervalo)
        else:
            for ag in agendamentos:
                inicio_existente = datetime.strptime(ag["data_original"], "%Y-%m-%d %H:%M")

                duracao_existente = ag.get("duracao", 60)
                fim_existente = inicio_existente + timedelta(minutes=duracao_existente)

                if (data_obj < fim_existente) and (data_fim > inicio_existente):
                    erro = "Este horário já está ocupado."
                    break

        # Se não houver erro, salva
        if not erro:
            data_formatada = data_obj.strftime("%d/%m/%Y às %H:%M")

            agendamentos.append({
                "nome": nome,
                "servico": servico,
                "data": data_formatada,
                "data_original": data_completa,
                "duracao": duracao
            })

    return render_template("index.html", agendamentos=agendamentos, erro=erro)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))