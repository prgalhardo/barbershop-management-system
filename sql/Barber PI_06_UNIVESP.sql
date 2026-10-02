CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE servicos (
    id_servico INT AUTO_INCREMENT PRIMARY KEY,
    nome_servico VARCHAR(80) NOT NULL,
    preco DECIMAL(10, 2) NOT NULL,
    duracao_minutos INT NOT NULL DEFAULT 30
);

CREATE TABLE agendamentos (
    id_agendamento INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_servico INT NOT NULL,
    data_hora_agendada DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'Pendente', -- Ex: Pendente, Confirmado, Concluído, Cancelado
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente) ON DELETE CASCADE,
    FOREIGN KEY (id_servico) REFERENCES servicos(id_servico) ON DELETE RESTRICT
);

select * from agendamentos

SELECT 
    a.id_agendamento,
    c.nome AS cliente,
    c.telefone,
    s.nome_servico AS servico_pretendido,
    s.preco,
    a.data_hora_agendada AS horario_pretendido,
    a.status
FROM agendamentos a
INNER JOIN clientes c ON a.id_cliente = c.id_cliente
INNER JOIN servicos s ON a.id_servico = s.id_servico
ORDER BY a.data_hora_agendada ASC;

ALTER TABLE agendamentos 
ADD COLUMN data_hora_fim DATETIME NOT NULL AFTER data_hora_agendada;



select * from agendamentos

select * from clientes