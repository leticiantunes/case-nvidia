import csv, os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/startups_db")
AQUI = os.path.dirname(os.path.abspath(__file__))


def carregar(cur, arquivo, tabela, colunas):
    caminho = os.path.join(AQUI, arquivo)
    with open(caminho, encoding="utf-8") as f:
        linhas = [tuple(r[c] for c in colunas) for r in csv.DictReader(f)]
    marcadores = ",".join(["%s"] * len(colunas))
    cur.executemany(
        f"INSERT INTO {tabela} ({','.join(colunas)}) VALUES ({marcadores})",
        linhas,
    )
    print(f"{tabela}: {len(linhas)} linhas inseridas")


conn = psycopg2.connect(DB)
cur = conn.cursor()

with open(os.path.join(AQUI, "schema.sql"), encoding="utf-8") as f:
    cur.execute(f.read())
print("schema criado")

carregar(
    cur,
    "startups.csv",
    "startups",
    [
        "id",
        "nome",
        "site",
        "setor",
        "setor_detalhado",
        "estagio",
        "localizacao",
        "descricao_curta",
        "ano_fundacao",
        "tamanho_time",
    ],
)
carregar(
    cur,
    "documentos.csv",
    "documentos",
    ["id", "startup_id", "tipo", "titulo", "conteudo_texto", "url_fonte", "data_publicacao"],
)

conn.commit()

cur.execute("SELECT COUNT(*) FROM startups")
print("total startups no banco:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM documentos")
print("total documentos no banco:", cur.fetchone()[0])

cur.close()
conn.close()
