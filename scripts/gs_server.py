# scripts/gs_server.py
# Servidor Flask para processar dados em tempo real do GSI do MatchZy

from flask import Flask, request, jsonify
import sqlite3
import json
import os
import subprocess

app = Flask(__name__)

# Função para descriptografar uma string
def decrypt_string(encrypted_string, encryption_key):
    command = f"echo -n \"{encrypted_string}\" | openssl enc -aes-256-cbc -a -d -salt -pass pass:\"{encryption_key}\""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

# Carregar as credenciais do .env
dotenv = {}
with open('../.env', 'r') as file:
    for line in file:
        key, value = line.strip().split('=', 1)
        dotenv[key] = value

# Descriptografar as credenciais
encryption_key = dotenv['ENCRYPTION_KEY']
db_host = decrypt_string(dotenv['DB_HOST'], encryption_key)
db_name = decrypt_string(dotenv['DB_NAME'], encryption_key)
db_user = decrypt_string(dotenv['DB_USER'], encryption_key)
db_pass = decrypt_string(dotenv['DB_PASS'], encryption_key)
discord_bot_token = decrypt_string(dotenv['DISCORD_BOT_TOKEN'], encryption_key)
steam_api_key = decrypt_string(dotenv['STEAM_API_KEY'], encryption_key)

# Conexão com o banco de dados SQLite
DB_PATH = '/var/www/agenciamgb/storage/logs/stats.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/gsi', methods=['POST'])
def handle_gsi():
    data = request.json
    map_name = data['map']['name']
    phase = data['map']['phase']
    team_ct_score = data['map']['team_ct']['score']
    team_t_score = data['map']['team_t']['score']

    conn = get_db_connection()
    query = "UPDATE active_servers SET score = ?, map = ? WHERE status = 'running'"
    conn.execute(query, (f"{team_ct_score}-{team_t_score}", map_name))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)