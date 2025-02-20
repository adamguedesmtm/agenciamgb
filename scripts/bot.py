# scripts/bot.py
# Script do bot do Discord

import discord
from discord.ext import commands, tasks
import requests
import os
import sqlite3
import random
from PIL import Image, ImageDraw, ImageFont
import io
import datetime
import subprocess

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
discord_bot_token = decrypt_string(dotenv['DISCORD_BOT_TOKEN'], encryption_key)
steam_api_key = decrypt_string(dotenv['STEAM_API_KEY'], encryption_key)


# Configuração do bot
TOKEN = 'SEU_TOKEN_AQUI'
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs dos canais
TEXT_CHANNEL_ID = 123456789012345678  # ID do canal de texto para mensagens do bot

# IDs dos canais de voz
VOICE_CHANNELS = {
    "5v5": 123456789012345678,  # ID do canal de voz "5v5"
    "2v2": 234567890123456789,  # ID do canal de voz "2v2"
    "Retakes": 345678901234567890  # ID do canal de voz "Retakes"
}

# Variáveis globais
signup_messages = {categoria: None for categoria in VOICE_CHANNELS.keys()}
signed_up_players = {categoria: [] for categoria in VOICE_CHANNELS.keys()}
matches = {}
MAPS = ["de_dust2", "de_mirage", "de_inferno", "de_nuke", "de_overpass", "de_ancient", "de_vertigo"]
ADMIN_IDS = [123456789012345678]  # IDs dos administradores
MAX_PLAYERS = 10

# Conexão com o banco de dados SQLite
DB_PATH = '/var/www/agenciamgb/storage/logs/stats.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_message(mensagem, logFile='/var/www/agenciamgb/storage/logs/general.log'):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(logFile, 'a') as file:
        file.write(f"[{timestamp}] {mensagem}\n")

def select_captains(players, stats):
    sorted_players = sorted(players, key=lambda x: stats.get(x, {}).get('kd_ratio', 0), reverse=True)
    captain1 = sorted_players[0]
    captain2 = sorted_players[1]
    return captain1, captain2

def alternate_pick(players, captain1, captain2):
    team1 = [captain1]
    team2 = [captain2]
    remaining_players = [p for p in players if p not in [captain1, captain2]]
    turn = 1  # 1 para team1, 2 para team2

    while remaining_players:
        if turn == 1:
            team1.append(remaining_players.pop(0))
            turn = 2
        else:
            team2.append(remaining_players.pop(0))
            turn = 1

    return team1, team2

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    log_message("Bot conectado com sucesso.")

@bot.command()
async def signup(ctx, categoria: str):
    global signup_messages, signed_up_players

    if categoria not in signed_up_players:
        await ctx.send("Categoria inválida. Use '5v5', '2v2' ou 'Retakes'.")
        return

    if ctx.author.name not in signed_up_players[categoria]:
        signed_up_players[categoria].append(ctx.author.name)
        await ctx.send(f"{ctx.author.name} foi adicionado à lista de jogadores para {categoria}!")
    else:
        await ctx.send(f"{ctx.author.name}, você já está na lista para {categoria}!")

@bot.command()
async def list_players(ctx, categoria: str):
    if categoria not in signed_up_players:
        await ctx.send("Categoria inválida. Use '5v5', '2v2' ou 'Retakes'.")
        return

    if signed_up_players[categoria]:
        player_list = "\n".join(signed_up_players[categoria])
        await ctx.send(f"Jogadores inscritos para {categoria}:\n{player_list}")
    else:
        await ctx.send(f"Nenhum jogador inscrito ainda para {categoria}.")

@bot.command()
async def create_teams(ctx, categoria: str):
    global signed_up_players

    if categoria not in signed_up_players:
        await ctx.send("Categoria inválida. Use '5v5', '2v2' ou 'Retakes'.")
        return

    if len(signed_up_players[categoria]) < MAX_PLAYERS:
        await ctx.send(f"Não há jogadores suficientes para criar equipes em {categoria}.")
        return

    stats = {jogador: {"kd_ratio": random.uniform(0.5, 3.0)} for jogador in signed_up_players[categoria]}
    captain1, captain2 = select_captains(signed_up_players[categoria], stats)
    team1, team2 = alternate_pick(signed_up_players[categoria], captain1, captain2)

    team1_list = "\n".join(team1)
    team2_list = "\n".join(team2)
    await ctx.send(f"Equipes criadas para {categoria}:\n\n**Time 1:**\n{team1_list}\n\n**Time 2:**\n{team2_list}")

    # Locka os jogadores no canal de voz
    voice_channel = bot.get_channel(VOICE_CHANNELS[categoria])
    if voice_channel:
        for jogador in team1 + team2:
            member = discord.utils.get(voice_channel.guild.members, name=jogador)
            if member:
                await member.move_to(voice_channel)

    # Limpa a lista de jogadores inscritos
    signed_up_players[categoria].clear()

    # Verifica se já existe um servidor ativo
    conn = get_db_connection()
    query = "SELECT * FROM active_servers WHERE status = 'running' LIMIT 1"
    servidor_ativo = conn.execute(query).fetchone()
    conn.close()

    if servidor_ativo:
        await ctx.send(f"Um servidor já está ativo para a categoria {servidor_ativo['categoria']}.\nPlacar: {servidor_ativo['score']}")
    else:
        await start_server(ctx, categoria, team1, team2)

async def start_server(ctx, categoria, team1, team2):
    conn = get_db_connection()
    query = "INSERT INTO active_servers (categoria, status, score) VALUES (?, 'running', '0-0')"
    conn.execute(query, (categoria,))
    conn.commit()
    conn.close()

    await ctx.send(f"Servidor para {categoria} iniciado! Placar inicial: 0-0")

    # Inicia o servidor de CS2 usando RCON ou outro método
    start_cs2_server(categoria)

def start_cs2_server(categoria):
    if categoria == "5v5":
        command = "/home/cs2server/start_cs2_server.sh de_dust2 10 5v5"
    elif categoria == "2v2":
        command = "/home/cs2server/start_cs2_server.sh de_dust2 4 2v2"
    elif categoria == "Retakes":
        command = "/home/cs2server/start_cs2_server.sh de_dust2 10 Retakes"
    
    subprocess.Popen(command, shell=True)

@bot.command()
async def ban_map(ctx, categoria: str, map_name: str):
    if categoria not in matches:
        matches[categoria] = {"banned_maps": []}
    elif "banned_maps" not in matches[categoria]:
        matches[categoria]["banned_maps"] = []

    if map_name.lower() in MAPS:
        if map_name.lower() not in matches[categoria]["banned_maps"]:
            matches[categoria]["banned_maps"].append(map_name.lower())
            await ctx.send(f"Mapa {map_name} foi banido para {categoria}.")
        else:
            await ctx.send(f"{map_name} já foi banido.")
    else:
        await ctx.send(f"{map_name} não está na lista de mapas disponíveis.")

@bot.command()
async def select_final_map(ctx, categoria: str):
    if categoria not in matches or "banned_maps" not in matches[categoria]:
        await ctx.send(f"Nenhum mapa foi banido ainda para {categoria}.")
        return

    available_maps = [mapa for mapa in MAPS if mapa not in matches[categoria]["banned_maps"]]
    if available_maps:
        final_map = random.choice(available_maps)
        await ctx.send(f"O mapa final para {categoria} é: {final_map}")
        # Salva o mapa final no banco de dados
        conn = get_db_connection()
        query = "UPDATE active_servers SET map = ? WHERE categoria = ? AND status = 'running'"
        conn.execute(query, (final_map, categoria))
        conn.commit()
        conn.close()
    else:
        await ctx.send(f"Todos os mapas foram banidos para {categoria}!")

@bot.command()
async def stats(ctx, jogador_nome: str):
    conn = get_db_connection()
    query = "SELECT * FROM players WHERE nome = ?"
    jogador = conn.execute(query, (jogador_nome,)).fetchone()
    conn.close()

    if jogador:
        stats = {
            "nome": jogador['nome'],
            "kills": jogador['kills'],
            "mortes": jogador['mortes'],
            "headshots": jogador['headshots'],
            "kd_ratio": round(jogador['kd_ratio'], 2),
            "headshot_percentage": round(jogador['headshot_percentage'], 2),
            "elo": jogador['elo'],
            "avatar_url": "https://example.com/avatar.png"  # Substitua pelo URL real do avatar
        }

        # Busca as roles do jogador
        roles_query = "SELECT role, emoji FROM roles WHERE user_id = (SELECT id FROM players WHERE nome = ?)"
        roles_stmt = conn.execute(roles_query, (jogador_nome,))
        roles = roles_stmt.fetchall()
        conn.close()

        roles_list = "\n".join([f"{role['emoji']} {role['role']}" for role in roles])

        # Gera a imagem do cartão do jogador
        card_path = generate_player_card(jogador_nome, stats, roles_list)

        with open(card_path, 'rb') as f:
            await ctx.send(file=discord.File(f, filename=f"{jogador_nome}_card.png"))
    else:
        await ctx.send("Jogador não encontrado ou erro ao buscar estatísticas.")

@bot.command()
async def lastmatch(ctx):
    conn = get_db_connection()
    query = "SELECT * FROM demos WHERE status = 'processed' ORDER BY id DESC LIMIT 1"
    demo = conn.execute(query).fetchone()
    conn.close()

    if demo:
        embed = discord.Embed(title="Última Partida", color=discord.Color.green())
        embed.add_field(name="Arquivo", value=demo['file_path'], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Nenhuma partida processada ainda.")

@bot.command()
async def top10(ctx):
    conn = get_db_connection()
    query = "SELECT nome, kills, mortes, kd_ratio, elo FROM players ORDER BY kd_ratio DESC LIMIT 10"
    jogadores = conn.execute(query).fetchall()
    conn.close()

    if jogadores:
        leaderboard = "\n".join([f"{i+1}. {jogador['nome']} - Elo: {jogador['elo']} - K/D: {jogador['kd_ratio']}" for i, jogador in enumerate(jogadores)])
        await ctx.send(f"Top 10 Jogadores:\n{leaderboard}")
    else:
        await ctx.send("Nenhum jogador registrado ainda.")

@bot.command()
async def upload_demo(ctx, attachment: discord.Attachment):
    if not attachment.filename.endswith('.dem'):
        await ctx.send("Por favor, envie um arquivo .dem válido.")
        return

    # Salva o arquivo no servidor
    demo_path = f"/var/www/agenciamgb/storage/uploads/{attachment.filename}"
    await attachment.save(demo_path)

    # Adiciona à fila de processamento
    conn = get_db_connection()
    query = "INSERT INTO demos (file_path, status) VALUES (?, 'pending')"
    conn.execute(query, (demo_path,))
    conn.commit()
    conn.close()

    await ctx.send(f"Arquivo {attachment.filename} enviado com sucesso! Aguarde o processamento.")

@bot.command()
async def update_map_pool(ctx, categoria: str, *mapas: str):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("Você não tem permissão para atualizar a map pool.")
        return

    conn = get_db_connection()
    query = "DELETE FROM map_pool WHERE categoria = ?"
    conn.execute(query, (categoria,))
    conn.commit()

    for mapa in mapas:
        insert_query = "INSERT INTO map_pool (map_name, categoria) VALUES (?, ?)"
        conn.execute(insert_query, (mapa, categoria))
    conn.commit()
    conn.close()

    await ctx.send(f"Map pool para {categoria} atualizada com sucesso.")

@bot.event
async def on_voice_state_update(member, before, after):
    for categoria, voice_channel_id in VOICE_CHANNELS.items():
        voice_channel = bot.get_channel(voice_channel_id)
        text_channel = bot.get_channel(TEXT_CHANNEL_ID)

        if voice_channel is None or text_channel is None:
            log_message(f"Canal não encontrado para a categoria {categoria}!")
            continue

        membros_no_canal = len(voice_channel.members)
        try:
            await voice_channel.edit(name=f"{categoria} ({membros_no_canal}/{MAX_PLAYERS})")
            log_message(f"Nome do canal atualizado para: {categoria} ({membros_no_canal}/{MAX_PLAYERS})")
        except Exception as e:
            log_message(f"Erro ao atualizar o nome do canal: {e}")

        if membros_no_canal == MAX_PLAYERS:
            await check_active_server(text_channel, categoria)

async def check_active_server(text_channel, categoria):
    conn = get_db_connection()
    query = "SELECT * FROM active_servers WHERE status = 'running' LIMIT 1"
    servidor_ativo = conn.execute(query).fetchone()
    conn.close()

    if servidor_ativo:
        await text_channel.send(f"Um servidor já está ativo para a categoria {servidor_ativo['categoria']}.\nPlacar: {servidor_ativo['score']}")
    else:
        await start_server(text_channel, categoria)

async def start_server(ctx, categoria):
    conn = get_db_connection()
    query = "INSERT INTO active_servers (categoria, status, score) VALUES (?, 'running', '0-0')"
    conn.execute(query, (categoria,))
    conn.commit()
    conn.close()

    await ctx.send(f"Servidor para {categoria} iniciado! Placar inicial: 0-0")

    # Inicia o servidor de CS2 usando RCON ou outro método
    start_cs2_server(categoria)

def start_cs2_server(categoria):
    if categoria == "5v5":
        command = "/home/cs2server/start_cs2_server.sh de_dust2 10 5v5"
    elif categoria == "2v2":
        command = "/home/cs2server/start_cs2_server.sh de_dust2 4 2v2"
    elif categoria == "Retakes":
        command = "/home/cs2server/start_cs2_server.sh de_dust2 10 Retakes"
    
    subprocess.Popen(command, shell=True)

def generate_player_card(jogador_nome, stats, roles_list):
    avatar_url = stats.get("avatar_url")
    response = requests.get(avatar_url)
    avatar = Image.open(io.BytesIO(response.content)).resize((100, 100))

    img = Image.new("RGB", (400, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    draw.text((140, 20), f"Nome: {jogador_nome}", fill=(0, 0, 0), font=font)
    draw.text((140, 50), f"Elo: {stats['elo']}", fill=(0, 0, 0), font=font)
    draw.text((140, 80), f"Kills: {stats['kills']}", fill=(0, 0, 0), font=font)
    draw.text((140, 110), f"Mortes: {stats['mortes']}", fill=(0, 0, 0), font=font)
    draw.text((140, 140), f"K/D: {stats['kd_ratio']}", fill=(0, 0, 0), font=font)
    draw.text((140, 170), f"Headshots: {stats['headshots']}", fill=(0, 0, 0), font=font)
    draw.text((140, 200), f"Headshot %: {stats['headshot_percentage']}%", fill=(0, 0, 0), font=font)
    draw.text((140, 230), f"Roles:\n{roles_list}", fill=(0, 0, 0), font=font)

    card_path = f"/var/www/agenciamgb/storage/player_cards/{jogador_nome}_card.png"
    img.save(card_path)
    return card_path

def assign_unique_roles(user_id, nome, stats):
    conn = get_db_connection()

    # Define as roles únicas com base nas estatísticas e emojis
    roles = [
        ("In-Game Leader", stats['assists'], "👑"),
        ("Tactical Genius", stats['tactical_kills'], "💡"),
        ("Strategist", stats['flank_kills'], "🗺️"),
        ("Entry King", stats['entry_kills'], "🔑"),
        ("Rush Master", stats['first_seconds_kills'], "🏃‍♂️"),
        ("Fearless Fragger", stats['duels_initiated'], "🗡️"),
        ("AWP Master", stats['awp_kills'], "狙"),
        ("AWP Thief", stats['awp_purchases'], "💰"),
        ("Headshot Machine", stats['headshot_percentage'], "💥"),
        ("The Wall", stats['defensive_multi_kills'], "🛡️"),
        ("Clutch God", stats['clutch_wins'], "💪"),
        ("Survivor", stats['survival_rate'], "🧍‍♂️"),
        ("Utility King", stats['grenade_damage'], "💣"),
        ("Flashbang King", stats['blinded_enemies'], "⚡"),
        ("Molotov Magician", stats['molotov_damage'], "⚗️"),
        ("Grenade Master", stats['he_kills'], "🔥"),
        ("Silent Killer", stats['backstab_kills'], "👻"),
        ("Connector King", stats['control_zone_kills'], "📍"),
        ("Camp King", stats['stationary_kills'], "🌲"),
        ("Speedster", stats['rotation_time'], "💨"),
        ("Eco King", stats['eco_rounds_won'], " Đề"),
        ("Pistol Expert", stats['pistol_rounds_won'], "🔫"),
        ("Money Saver", stats['money_saved'], "💸"),
        ("Bullet Sponge", stats['total_damage_taken'], "🤕"),
        ("Silver Elite", stats['lowest_kills'], "🥈"),
        ("Bot Eco", stats['bot_eco_deaths'], "🤖"),
        ("Entry Feeder", stats['first_kill_deaths'], "新人玩家"),
        ("CS Tourist", stats['inactive_time'], "🚶‍♂️"),
        ("Wall Sprayer", stats['missed_shots'], "🔫"),
        ("1vX Choker", stats['clutch_losses'], "💔"),
        ("Last Alive, First to Die", stats['last_alive_first_die'], "😱"),
        ("Baited Again", stats['no_trade_deaths'], "🐟"),
        ("Whiffmaster", stats['missed_before_hit'], "💨"),
        ("AWP No-Scope Enjoyer", stats['awp_noscope_misses'], "🤷‍♂️"),
        ("Leg Shot Lord", stats['leg_shots'], "🦵"),
        ("Can't Spray, Won't Spray", stats['wasted_shots'], "💦"),
        ("Fake Defuse Believer", stats['fake_defuse_deaths'], "🎩"),
        ("Lost on the Map", stats['wandering_time'], "🗺️"),
        ("Flash Myself Pro", stats['self_blinded'], "👁️‍🗨️"),
        ("Terrorist CT", stats['teamkills'], "😡"),
        ("Bomberman", stats['exploded_by_c4'], "💣"),
        ("Nade Magnet", stats['nade_damage_taken'], "💫")
    ]

    # Remove todas as roles existentes para o jogador
    delete_query = "DELETE FROM roles WHERE user_id = ?"
    conn.execute(delete_query, (user_id,))
    conn.commit()

    # Atribui roles únicas com base nas estatísticas
    for role, value, emoji in roles:
        if value is not None:
            insert_query = "INSERT INTO roles (user_id, role, emoji) VALUES (?, ?, ?)"
            conn.execute(insert_query, (user_id, role, emoji))
            conn.commit()
            log_message(f"Role atribuída para {nome}: {emoji} {role}")

    conn.close()

def assign_generic_roles(user_id, nome, stats):
    conn = get_db_connection()

    # Define as roles genéricas com base nas estatísticas e emojis
    roles = [
        ("Top Killer", stats['kills'], "🏆"),
        ("Top Mortes", stats['mortes'], "☠️"),
        ("Top Headshots", stats['headshots'], "🎯"),
        ("Top KD Ratio", stats['kd_ratio'], "📈")
    ]

    # Remove todas as roles genéricas existentes para o jogador
    delete_query = "DELETE FROM roles WHERE user_id = ? AND role IN ('Top Killer', 'Top Mortes', 'Top Headshots', 'Top KD Ratio')"
    conn.execute(delete_query, (user_id,))
    conn.commit()

    # Atribui roles genéricas com base nas estatísticas
    for role, value, emoji in roles:
        if value is not None:
            insert_query = "INSERT INTO roles (user_id, role, emoji) VALUES (?, ?, ?)"
            conn.execute(insert_query, (user_id, role, emoji))
            conn.commit()
            log_message(f"Role genérica atribuída para {nome}: {emoji} {role}")

    conn.close()

def calculate_elo(current_elo, kills, mortes):
    # Parâmetros para o cálculo do elo
    base_elo_gain = 10  # Elo base ganho por vitória
    base_elo_loss = 10  # Elo base perdido por derrota
    elo_adjustment_factor = 0.01  # Fator de ajuste para elo baseado no desempenho

    # Cálculo do elo baseado no desempenho
    elo_change = (kills - mortes) * elo_adjustment_factor

    # Ajusta o elo baseado no desempenho
    if kills > mortes:
        # Vitória
        new_elo = current_elo + (base_elo_gain + elo_change)
    elif kills < mortes:
        # Derrota
        new_elo = current_elo - (base_elo_loss - elo_change)
    else:
        # Empate
        new_elo = current_elo

    # Garante que o elo não seja negativo
    if new_elo < 0:
        new_elo = 0

    return int(new_elo)

@bot.command()
async def start_match(ctx, categoria: str):
    global signed_up_players

    if categoria not in signed_up_players:
        await ctx.send("Categoria inválida. Use '5v5', '2v2' ou 'Retakes'.")
        return

    if len(signed_up_players[categoria]) < MAX_PLAYERS:
        await ctx.send(f"Não há jogadores suficientes para iniciar a partida em {categoria}.")
        return

    stats = {jogador: {"kd_ratio": random.uniform(0.5, 3.0)} for jogador in signed_up_players[categoria]}
    captain1, captain2 = select_captains(signed_up_players[categoria], stats)
    team1, team2 = alternate_pick(signed_up_players[categoria], captain1, captain2)

    team1_list = "\n".join(team1)
    team2_list = "\n".join(team2)
    await ctx.send(f"Equipes criadas para {categoria}:\n\n**Time 1:**\n{team1_list}\n\n**Time 2:**\n{team2_list}")

    # Locka os jogadores no canal de voz
    voice_channel = bot.get_channel(VOICE_CHANNELS[categoria])
    if voice_channel:
        for jogador in team1 + team2:
            member = discord.utils.get(voice_channel.guild.members, name=jogador)
            if member:
                await member.move_to(voice_channel)

    # Limpa a lista de jogadores inscritos
    signed_up_players[categoria].clear()

    # Verifica se já existe um servidor ativo
    conn = get_db_connection()
    query = "SELECT * FROM active_servers WHERE status = 'running' LIMIT 1"
    servidor_ativo = conn.execute(query).fetchone()
    conn.close()

    if servidor_ativo:
        await ctx.send(f"Um servidor já está ativo para a categoria {servidor_ativo['categoria']}.\nPlacar: {servidor_ativo['score']}")
    else:
        await start_server(ctx, categoria, team1, team2)

@bot.command()
async def vote_map(ctx, categoria: str, map_name: str):
    if categoria not in matches:
        matches[categoria] = {"votes": {}}
    elif "votes" not in matches[categoria]:
        matches[categoria]["votes"] = {}

    if map_name.lower() in MAPS:
        if ctx.author.name not in matches[categoria]["votes"]:
            matches[categoria]["votes"][ctx.author.name] = map_name.lower()
            await ctx.send(f"{ctx.author.name} votou no mapa {map_name}.")
        else:
            await ctx.send(f"{ctx.author.name}, você já votou em um mapa.")
    else:
        await ctx.send(f"{map_name} não está na lista de mapas disponíveis.")

@bot.command()
async def show_votes(ctx, categoria: str):
    if categoria not in matches or "votes" not in matches[categoria]:
        await ctx.send(f"Nenhum voto registrado ainda para {categoria}.")
        return

    votes = matches[categoria]["votes"]
    vote_counts = {mapa: votes.count(mapa) for mapa in set(votes)}

    vote_list = "\n".join([f"{mapa}: {count} voto(s)" for mapa, count in vote_counts.items()])
    await ctx.send(f"Votos para {categoria}:\n{vote_list}")

@bot.command()
async def select_voted_map(ctx, categoria: str):
    if categoria not in matches or "votes" not in matches[categoria]:
        await ctx.send(f"Nenhum voto registrado ainda para {categoria}.")
        return

    votes = matches[categoria]["votes"]
    vote_counts = {mapa: votes.count(mapa) for mapa in set(votes)}

    if not vote_counts:
        await ctx.send(f"Nenhum voto registrado ainda para {categoria}.")
        return

    # Seleciona o mapa com mais votos
    final_map = max(vote_counts, key=vote_counts.get)
    await ctx.send(f"O mapa final para {categoria} é: {final_map}")

    # Salva o mapa final no banco de dados
    conn = get_db_connection()
    query = "UPDATE active_servers SET map = ? WHERE categoria = ? AND status = 'running'"
    conn.execute(query, (final_map, categoria))
    conn.commit()
    conn.close()

# Sistema de RCON para controlar o servidor de CS2
from valve.rcon import RCON

SERVER_IP = "127.0.0.1"
SERVER_PORT = 27015
RCON_PASSWORD = "sua_senha_rcon"

def execute_rcon_command(command):
    with RCON((SERVER_IP, SERVER_PORT), RCON_PASSWORD) as rcon:
        response = rcon(command)
        return response

@bot.command()
async def start_server(ctx, categoria: str, team1, team2):
    conn = get_db_connection()
    query = "INSERT INTO active_servers (categoria, status, score) VALUES (?, 'running', '0-0')"
    conn.execute(query, (categoria,))
    conn.commit()
    conn.close()

    await ctx.send(f"Servidor para {categoria} iniciado! Placar inicial: 0-0")

    # Inicia o servidor de CS2 usando RCON ou outro método
    start_cs2_server(categoria)

def start_cs2_server(categoria):
    if categoria == "5v5":
        command = "/home/cs2server/start_cs2_server.sh de_dust2 10 5v5"
    elif categoria == "2v2":
        command = "/home/cs2server/start_cs2_server.sh de_dust2 4 2v2"
    elif categoria == "Retakes":
        command = "/home/cs2server/start_cs2_server.sh de_dust2 10 Retakes"
    
    subprocess.Popen(command, shell=True)

@bot.command()
async def end_match(ctx, categoria: str):
    if categoria not in matches:
        await ctx.send(f"Nenhuma partida em andamento para {categoria}.")
        return

    # Simula o fim da partida com um placar aleatório
    score = f"{random.randint(0, 16)}-{random.randint(0, 16)}"
    await ctx.send(f"Partida de {categoria} encerrada! Placar final: {score}")

    # Atualiza o placar no banco de dados
    conn = get_db_connection()
    query = "UPDATE active_servers SET score = ? WHERE categoria = ? AND status = 'running'"
    conn.execute(query, (score, categoria))
    conn.commit()
    conn.close()

    # Encerra o servidor
    execute_rcon_command("quit")

    # Limpa os votos da partida
    if categoria in matches:
        del matches[categoria]

@bot.command()
async def get_elo(ctx, jogador_nome: str):
    conn = get_db_connection()
    query = "SELECT elo FROM players WHERE nome = ?"
    jogador = conn.execute(query, (jogador_nome,)).fetchone()
    conn.close()

    if jogador:
        await ctx.send(f"Elo de {jogador_nome}: {jogador['elo']}")
    else:
        await ctx.send("Jogador não encontrado.")

# Inicia o bot
bot.run(TOKEN)