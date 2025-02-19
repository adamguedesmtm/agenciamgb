from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = '/var/www/stats/stats.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/gsi', methods=['POST'])
def gsi():
    data = request.json
    conn = get_db_connection()
    # Processa os dados recebidos e salva no banco de dados
    # Exemplo: Salvar informações de kills, mortes, headshots, etc.
    conn.close()
    return jsonify({"status": "sucesso"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)