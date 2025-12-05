import sqlite3
import os

def init_db():
    """Inicializa o banco de dados SQLite se não existir."""
    # Define o caminho do banco de dados (um nível acima de src)
    db_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(db_dir, 'imoveis.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabela de Imóveis
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS imoveis_avaliados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        endereco TEXT NOT NULL,
        area_m2 REAL,
        data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabela de Avaliações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        imovel_id INTEGER,
        valor_medio_m2 REAL,
        preco_estimado REAL,
        finalidade TEXT,
        data_avaliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (imovel_id) REFERENCES imoveis_avaliados (id)
    )
    ''')

    # Tabela de Imóveis Comparativos (Considerados)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS imoveis_comparativos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        avaliacao_id INTEGER,
        endereco TEXT,
        link TEXT,
        area_m2 REAL,
        valor_total REAL,
        valor_m2 REAL,
        FOREIGN KEY (avaliacao_id) REFERENCES avaliacoes (id)
    )
    ''')

    # Tabela de Mensagens do Chat
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT,
        role TEXT,
        content TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Tabela de Conversas (Threads)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversas (
        id TEXT PRIMARY KEY,
        titulo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    return db_path
