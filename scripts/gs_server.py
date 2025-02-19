# scripts/gs_server.py
# Servidor Flask para processar dados em tempo real do GSI do MatchZy

from flask import Flask, request, jsonify
import sqlite3
import json
import os

app = Flask(__name__)
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