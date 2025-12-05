from flask import Flask, render_template, g, request, jsonify
import sqlite3
import os
import uuid
from database import init_db
from graph import graph

app = Flask(__name__)

# Inicializa o banco de dados na inicialização da aplicação
init_db()

DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'imoveis.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    db = get_db()
    # Join avaliacoes with imoveis_avaliados to get address
    query = """
        SELECT a.id, i.endereco, a.valor_medio_m2, a.preco_estimado, a.finalidade, a.data_avaliacao, i.area_m2
        FROM avaliacoes a
        JOIN imoveis_avaliados i ON a.imovel_id = i.id
        ORDER BY a.data_avaliacao DESC
    """
    cur = db.execute(query)
    avaliacoes = cur.fetchall()
    return render_template('index.html', avaliacoes=avaliacoes)

@app.route('/avaliacao/<int:id>')
def detalhes_avaliacao(id):
    db = get_db()
    
    # Get evaluation details
    query_avaliacao = """
        SELECT a.id, i.endereco, a.valor_medio_m2, a.preco_estimado, a.finalidade, a.data_avaliacao, i.area_m2
        FROM avaliacoes a
        JOIN imoveis_avaliados i ON a.imovel_id = i.id
        WHERE a.id = ?
    """
    cur = db.execute(query_avaliacao, (id,))
    avaliacao = cur.fetchone()
    
    if avaliacao is None:
        return "Avaliação não encontrada", 404
        
    # Get comparables
    query_comparativos = """
        SELECT endereco, link, area_m2, valor_total, valor_m2
        FROM imoveis_comparativos
        WHERE avaliacao_id = ?
    """
    cur = db.execute(query_comparativos, (id,))
    comparativos = cur.fetchall()
    
    return render_template('avaliacao.html', avaliacao=avaliacao, comparativos=comparativos)

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/api/chat/threads', methods=['GET'])
def list_threads():
    db = get_db()
    cur = db.execute("SELECT id, titulo, created_at FROM conversas ORDER BY created_at DESC")
    threads = [{'id': row['id'], 'titulo': row['titulo'], 'created_at': row['created_at']} for row in cur.fetchall()]
    return jsonify(threads)

@app.route('/api/chat/threads', methods=['POST'])
def create_thread():
    db = get_db()
    thread_id = str(uuid.uuid4())
    titulo = "Nova Conversa"
    
    db.execute("INSERT INTO conversas (id, titulo) VALUES (?, ?)", (thread_id, titulo))
    db.commit()
    
    return jsonify({'id': thread_id, 'titulo': titulo})

@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    data = request.json
    user_message = data.get('message')
    thread_id = data.get('thread_id')
    
    if not user_message:
        return jsonify({'error': 'Mensagem vazia'}), 400
    
    if not thread_id:
        return jsonify({'error': 'Thread ID não fornecido'}), 400
        
    db = get_db()
    
    # Atualiza título se for a primeira mensagem
    cur = db.execute("SELECT count(*) FROM mensagens WHERE thread_id = ?", (thread_id,))
    count = cur.fetchone()[0]
    if count == 0:
        # Tenta gerar um título melhor baseado na primeira mensagem (simplificado aqui)
        titulo = user_message[:30] + "..." if len(user_message) > 30 else user_message
        db.execute("UPDATE conversas SET titulo = ? WHERE id = ?", (titulo, thread_id))
    
    # Salvar mensagem do usuário
    db.execute(
        "INSERT INTO mensagens (thread_id, role, content) VALUES (?, ?, ?)",
        (thread_id, 'user', user_message)
    )
    db.commit()
    
    # Configuração dinâmica para o LangGraph
    config = {"configurable": {"thread_id": thread_id}}
    
    # Invocar o agente
    try:
        response = graph.invoke({"messages": user_message}, config)
        ai_message = response['messages'][-1].content
        
        # Salvar resposta da IA
        db.execute(
            "INSERT INTO mensagens (thread_id, role, content) VALUES (?, ?, ?)",
            (thread_id, 'ai', ai_message)
        )
        db.commit()
        
        return jsonify({'response': ai_message})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history')
def chat_history():
    thread_id = request.args.get('thread_id')
    if not thread_id:
        return jsonify([])
        
    db = get_db()
    cur = db.execute(
        "SELECT role, content FROM mensagens WHERE thread_id = ? ORDER BY timestamp ASC",
        (thread_id,)
    )
    messages = [{'role': row['role'], 'content': row['content']} for row in cur.fetchall()]
    return jsonify(messages)

@app.route('/api/chat/history/<thread_id>', methods=['DELETE'])
def clear_chat_history(thread_id):
    db = get_db()
    db.execute("DELETE FROM mensagens WHERE thread_id = ?", (thread_id,))
    db.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
