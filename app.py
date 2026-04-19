from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nome = request.form.get("nome")
        servico = request.form.get("servico")
        data = request.form.get("data")

        print(nome, servico, data)  # só pra testar por enquanto

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)