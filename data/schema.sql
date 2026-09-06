DROP TABLE IF EXISTS documentos;
DROP TABLE IF EXISTS startups;

CREATE TABLE startups (
    id              TEXT PRIMARY KEY,
    nome            TEXT NOT NULL,
    site            TEXT,
    setor           TEXT,
    setor_detalhado TEXT,
    estagio         TEXT,
    localizacao     TEXT,
    descricao_curta TEXT,
    ano_fundacao    TEXT,
    tamanho_time    TEXT
);

CREATE TABLE documentos (
    id              TEXT PRIMARY KEY,
    startup_id      TEXT REFERENCES startups(id),
    tipo            TEXT,
    titulo          TEXT,
    conteudo_texto  TEXT,
    url_fonte       TEXT,
    data_publicacao TEXT
);

CREATE INDEX idx_documentos_startup ON documentos(startup_id);
CREATE INDEX idx_startups_setor ON startups(setor);