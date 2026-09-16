import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = "chave_secreta_loja_refrigerantes"

# Caminho absoluto para garantir que o SQLite crie o arquivo no local correto na Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "loja_refrigerantes.db")

# --- BANCO DE DADOS ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            embalagem TEXT NOT NULL,
            preco_custo REAL NOT NULL,
            preco_venda REAL NOT NULL,
            estoque INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            quantidade INTEGER,
            valor_total REAL,
            lucro_total REAL,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    conn.commit()
    conn.close()

# Executa a criação do banco de dados na inicialização do servidor
with app.app_context():
    init_db()

# --- ROTAS ---
@app.route('/')
def index():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    
    vendas = conn.execute('SELECT SUM(valor_total) as total_faturamento, SUM(lucro_total) as total_lucro FROM vendas').fetchone()
    total_faturamento = vendas['total_faturamento'] or 0.0
    total_lucro = vendas['total_lucro'] or 0.0
    
    conn.close()
    return render_template('index.html', produtos=produtos, total_faturamento=total_faturamento, total_lucro=total_lucro)

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    nome = request.form['nome']
    embalagem = request.form['embalagem']
    preco_custo = float(request.form['preco_custo'])
    preco_venda = float(request.form['preco_venda'])
    estoque = int(request.form['estoque'])

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO produtos (nome, embalagem, preco_custo, preco_venda, estoque)
        VALUES (?, ?, ?, ?, ?)
    ''', (nome, embalagem, preco_custo, preco_venda, estoque))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/vender', methods=['POST'])
def vender():
    produto_id = int(request.form['produto_id'])
    quantidade = int(request.form['quantidade'])

    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()

    if produto and produto['estoque'] >= quantidade:
        valor_total = produto['preco_venda'] * quantidade
        lucro_unitario = produto['preco_venda'] - produto['preco_custo']
        lucro_total = lucro_unitario * quantidade

        conn.execute('''
            INSERT INTO vendas (produto_id, quantidade, valor_total, lucro_total)
            VALUES (?, ?, ?, ?)
        ''', (produto_id, quantidade, valor_total, lucro_total))

        conn.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?', (quantidade, produto_id))
        conn.commit()

    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
