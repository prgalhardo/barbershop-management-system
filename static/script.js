// 1. Integração com API Externa ViaCEP
async function buscarCEP(valor) {
    const cep = valor.replace(/\D/g, '');
    if (cep.length !== 8) return;

    document.getElementById('logradouro').value = 'Buscando...';
    document.getElementById('bairro').value = 'Buscando...';
    document.getElementById('cidade').value = 'Buscando...';
    document.getElementById('estado').value = '...';

    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();

        if (!data.erro) {
            document.getElementById('logradouro').value = data.logradouro || '';
            document.getElementById('bairro').value = data.bairro || '';
            document.getElementById('cidade').value = data.localidade || '';
            document.getElementById('estado').value = data.uf || '';
        } else {
            alert('CEP não encontrado.');
            limparEndereco();
        }
    } catch (err) {
        console.error('Erro na consulta ViaCEP:', err);
        limparEndereco();
    }
}

function limparEndereco() {
    document.getElementById('logradouro').value = '';
    document.getElementById('bairro').value = '';
    document.getElementById('cidade').value = '';
    document.getElementById('estado').value = '';
}

// Mapeamento dos IDs de serviço
const servicosMap = {
    "Corte": 1,
    "Barba": 2,
    "Corte + Barba": 3,
    "Sobrancelha": 4
};

// 2. Chamada Assíncrona para Listar Agendamentos do Dia
async function carregarAgendamentosDoDia(dataVal) {
    const secao = document.getElementById('secaoAgenda');
    const container = document.getElementById('containerAgendamentos');

    if (!dataVal) {
        secao.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/api/v1/agendamentos-do-dia?data=${dataVal}`);
        if (!response.ok) return;

        const dados = await response.json();
        container.innerHTML = '';

        if (dados.length > 0) {
            secao.style.display = 'block';
            dados.forEach(ag => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <p><strong>Cliente:</strong> ${ag.nome}</p>
                    <p><strong>Serviço:</strong> ${ag.servico}</p>
                    <p><strong>Horário:</strong> ${ag.data}</p>
                    <a href="/editar/${ag.id}"><button type="button">Remarcar</button></a>
                    <form method="POST" action="/deletar/${ag.id}" style="display:inline;">
                        <button type="submit">Cancelar</button>
                    </form>
                `;
                container.appendChild(card);
            });
        } else {
            secao.style.display = 'none';
        }
    } catch (err) {
        console.error('Erro ao buscar agendamentos do dia:', err);
    }
}

// 3. Chamada Assíncrona para Horários Dinâmicos
async function carregarHorariosDinamicos() {
    const dataVal = document.getElementById('dataInput').value;
    const servicoNome = document.getElementById('servico').value;
    const servicoId = servicosMap[servicoNome] || 1;
    const secao = document.getElementById('secaoHorarios');
    const grid = document.getElementById('gridHorarios');
    const status = document.getElementById('horariosStatus');
    const campoHora = document.getElementById('horaSelecionada');

    if (!dataVal) {
        secao.style.display = 'none';
        document.getElementById('secaoAgenda').style.display = 'none';
        return;
    }

    // Atualiza a lista de agendamentos existentes
    carregarAgendamentosDoDia(dataVal);

    // Carrega a grelha de horários disponíveis
    secao.style.display = 'block';
    grid.innerHTML = '';
    status.textContent = 'A verificar horários disponíveis...';

    try {
        const response = await fetch(`/api/v1/horarios-disponiveis?data=${dataVal}&servico_id=${servicoId}`);
        if (!response.ok) throw new Error('Erro ao obter horários.');

        const lista = await response.json();
        status.textContent = '';
        grid.innerHTML = '';

        if (lista.length === 0) {
            status.textContent = 'Nenhum horário disponível para esta data.';
            return;
        }

        lista.forEach(item => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `hora-btn ${item.ocupado ? 'ocupado' : ''}`;
            btn.textContent = item.hora;
            btn.disabled = item.ocupado;

            if (campoHora.value === item.hora && !item.ocupado) {
                btn.classList.add('selecionado');
            }

            if (!item.ocupado) {
                btn.onclick = () => {
                    document.querySelectorAll('.hora-btn').forEach(b => b.classList.remove('selecionado'));
                    btn.classList.add('selecionado');
                    campoHora.value = item.hora;
                };
            }

            grid.appendChild(btn);
        });
    } catch (err) {
        console.error(err);
        status.textContent = 'Erro ao carregar horários. Tente novamente.';
    }
}

// Inicialização caso a página já contenha uma data selecionada
window.addEventListener('DOMContentLoaded', () => {
    const inputData = document.getElementById('dataInput');
    if (inputData && inputData.value) {
        carregarHorariosDinamicos();
    }
});