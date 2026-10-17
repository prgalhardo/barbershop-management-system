// ==================== 1. NAVEGAÇÃO DE ABAS ====================
function switchPage(pageId) {
    // Se tentar acessar a área do barbeiro sem estar logado
    if (pageId === 'barber-page') {
        const estaLogado = document.getElementById('user-display')?.innerText.includes('Barbeiro');
        if (!estaLogado) {
            alert('Acesso restrito. Faça login como Barbeiro para acessar esta área.');
            abrirModalLogin();
            return;
        }
    }
    document.querySelectorAll('.page-section').forEach(sec => sec.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));

    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    if (pageId === 'home-page') document.getElementById('tab-nav-home')?.classList.add('active');
    if (pageId === 'client-page') document.getElementById('tab-nav-client')?.classList.add('active');
    if (pageId === 'barber-page') document.getElementById('tab-nav-barber')?.classList.add('active');

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==================== 2. INTEGRAÇÃO VIACEP ====================
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

// ==================== 3. AGENDAMENTOS E HORÁRIOS ASSÍNCRONOS ====================
const servicosMap = {
    "Corte": 1,
    "Barba": 2,
    "Corte + Barba": 3,
    "Sobrancelha": 4
};

async function carregarAgendamentosDoDia(dataVal) {
    const secao = document.getElementById('secaoAgenda');
    const container = document.getElementById('containerAgendamentos');

    // Se o elemento não existe na tela (ou seja, usuário não é barbeiro), não faz nada
    if (!secao || !container) return;

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
                    <div style="display:flex; gap: 8px;">
                        <a href="/editar/${ag.id}"><button type="button">Remarcar</button></a>
                        <form method="POST" action="/deletar/${ag.id}" style="display:inline;" onsubmit="return confirm('Tem certeza que deseja cancelar o agendamento de ${ag.nome}?');">
                            <button type="submit">Cancelar</button>
                        </form>
                    </div>
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

async function carregarHorariosDinamicos() {
    const dataVal = document.getElementById('dataInput')?.value;
    const servicoNome = document.getElementById('servico')?.value;
    const servicoId = servicosMap[servicoNome] || 1;
    const secao = document.getElementById('secaoHorarios');
    const grid = document.getElementById('gridHorarios');
    const status = document.getElementById('horariosStatus');
    const campoHora = document.getElementById('horaSelecionada');

    if (!dataVal) {
        if (secao) secao.style.display = 'none';
        return;
    }

    carregarAgendamentosDoDia(dataVal);

    if (secao) secao.style.display = 'block';
    if (grid) grid.innerHTML = '';
    if (status) status.textContent = 'Verificando horários disponíveis...';

    try {
        const response = await fetch(`/api/v1/horarios-disponiveis?data=${dataVal}&servico_id=${servicoId}`);
        if (!response.ok) throw new Error('Erro ao buscar horários.');

        const lista = await response.json();
        if (status) status.textContent = '';
        if (grid) grid.innerHTML = '';

        if (lista.length === 0) {
            if (status) status.textContent = 'Nenhum horário disponível para esta data.';
            return;
        }

        lista.forEach(item => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `hora-btn ${item.ocupado ? 'ocupado' : ''}`;
            btn.textContent = item.hora;
            btn.disabled = item.ocupado;

            if (campoHora && campoHora.value === item.hora && !item.ocupado) {
                btn.classList.add('selecionado');
            }

            if (!item.ocupado) {
                btn.onclick = () => {
                    document.querySelectorAll('.hora-btn').forEach(b => b.classList.remove('selecionado'));
                    btn.classList.add('selecionado');
                    if (campoHora) campoHora.value = item.hora;
                };
            }

            grid.appendChild(btn);
        });
    } catch (err) {
        console.error(err);
        if (status) status.textContent = 'Erro ao carregar horários. Verifique a conexão com o servidor.';
    }
}

// ==================== 4. BUSCA E CHAT ====================
function filterAppointments() {
    const input = document.getElementById('search-input')?.value.toLowerCase();
    const items = document.querySelectorAll('#appointments-list .card-item');
    items.forEach(item => {
        const text = item.getAttribute('data-name')?.toLowerCase() || '';
        item.style.display = text.includes(input) ? 'flex' : 'none';
    });
}

function sendClientMsg() {
    const input = document.getElementById('client-chat-input');
    if (!input || !input.value.trim()) return;
    appendMsg('client-chat-msgs', input.value, 'msg-client');
    appendMsg('barber-chat-msgs', input.value, 'msg-client');
    input.value = '';
}

function sendBarberMsg() {
    const input = document.getElementById('barber-chat-input');
    if (!input || !input.value.trim()) return;
    appendMsg('barber-chat-msgs', input.value, 'msg-barber');
    appendMsg('client-chat-msgs', input.value, 'msg-barber');
    input.value = '';
}

function appendMsg(containerId, text, className) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${className}`;
    msgDiv.innerText = text;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

// Inicialização: se vier data ou editar_id na URL, ativa direto a aba de agendamento
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('data') || urlParams.has('editar_id') || urlParams.has('sucesso')) {
        switchPage('client-page');
    }

    if (document.getElementById('dataInput')?.value) {
        carregarHorariosDinamicos();
    }
});

// ==================== 5. AUTENTICAÇÃO DO BARBEIRO ====================
function abrirModalLogin() {
    const modal = document.getElementById('modal-login');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
    } else {
        console.error("Elemento modal-login não foi encontrado no DOM.");
    }
}

function fecharModalLogin() {
    const modal = document.getElementById('modal-login');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
    const erroEl = document.getElementById('login-erro');
    if (erroEl) erroEl.style.display = 'none';
}

async function realizarLogin(e) {
    e.preventDefault();
    const usuario = document.getElementById('login-usuario').value;
    const senha = document.getElementById('login-senha').value;
    const erroEl = document.getElementById('login-erro');
    const btn = document.getElementById('btn-login-submit');

    btn.disabled = true;
    btn.textContent = "Verificando...";

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: usuario, password: senha })
        });

        const data = await response.json();

        if (response.ok && data.sucesso) {
            // Recarrega na aba do barbeiro já autenticado
            window.location.href = '/?aba=barbeiro';
        } else {
            erroEl.textContent = data.erro || "Credenciais inválidas.";
            erroEl.style.display = 'block';
        }
    } catch (err) {
        erroEl.textContent = "Erro ao conectar com o servidor.";
        erroEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = "Entrar no Painel";
    }
}

// ==================== 6. AUTO-LIMPEZA DE MENSAGENS E INICIALIZAÇÃO ====================
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);

    // Se vier do login para a aba do barbeiro
    if (urlParams.get('aba') === 'barbeiro') {
        switchPage('barber-page');
    } else if (urlParams.has('data') || urlParams.has('editar_id')) {
        switchPage('client-page');
    }

    if (document.getElementById('dataInput')?.value) {
        carregarHorariosDinamicos();
    }

    // Remove o aviso verde após 4 segundos e limpa a URL silenciosamente
    const alertaSucesso = document.querySelector('.alert-success');
    if (alertaSucesso) {
        setTimeout(() => {
            alertaSucesso.style.transition = 'opacity 0.6s ease';
            alertaSucesso.style.opacity = '0';
            setTimeout(() => {
                alertaSucesso.remove();
            }, 600);
        }, 3500);

        // Limpa sucesso=... da barra de endereço sem recarregar a tela
        if (urlParams.has('sucesso')) {
            const novaUrl = window.location.pathname;
            window.history.replaceState({}, document.title, novaUrl);
        }
    }
});

// ==================== 7. FILTROS DA AGENDA DO BARBEIRO ====================
function filtrarAgendaPorData(dataIso) {
    if (!dataIso) return;
    // Converte de AAAA-MM-DD para DD/MM/AAAA
    const partes = dataIso.split('-');
    const dataFormatada = `${partes[2]}/${partes[1]}/${partes[0]}`;

    const items = document.querySelectorAll('#appointments-list .card-item');
    let encontrados = 0;

    items.forEach(item => {
        const dataItem = item.getAttribute('data-data') || '';
        if (dataItem.includes(dataFormatada)) {
            item.style.display = 'flex';
            encontrados++;
        } else {
            item.style.display = 'none';
        }
    });

    const kpi = document.getElementById('kpi-total-agendamentos');
    if (kpi) kpi.textContent = encontrados;
}

function limparFiltroDataBarbeiro() {
    const inputData = document.getElementById('filtro-data-barbeiro');
    if (inputData) inputData.value = '';

    const items = document.querySelectorAll('#appointments-list .card-item');
    items.forEach(item => item.style.display = 'flex');

    const kpi = document.getElementById('kpi-total-agendamentos');
    if (kpi) kpi.textContent = items.length;
}