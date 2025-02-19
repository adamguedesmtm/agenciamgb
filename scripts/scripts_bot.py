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
DB_PATH = '/var/www/stats/stats.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    sorted_players = sorted(signed_up_players[categoria], key=lambda x: stats[x]['kd_ratio'], reverse=True)
    team1 = sorted_players[:5]
    team2 = sorted_players[5:]

    team1_list = "\n".join(team1)
    team2_list = "\n".join(team2)
    await ctx.send(f"Equipes criadas para {categoria}:\n\n**Time 1:**\n{team1_list}\n\n**Time 2:**\n{team2_list}")

    # Limpa a lista de jogadores inscritos
    signed_up_players[categoria].clear()

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
async def pick_player(ctx, categoria: str, jogador_nome: str):
    if categoria not in matches:
        matches[categoria] = {"picked_players": []}
    elif "picked_players" not in matches[categoria]:
        matches[categoria]["picked_players"] = []

    if jogador_nome in signed_up_players[categoria]:
        if jogador_nome not in matches[categoria]["picked_players"]:
            matches[categoria]["picked_players"].append(jogador_nome)
            await ctx.send(f"Jogador {jogador_nome} foi escolhido para {categoria}.")
        else:
            await ctx.send(f"Jogador {jogador_nome} já foi escolhido.")
    else:
        await ctx.send(f"Jogador {jogador_nome} não está inscrito para {categoria}.")

@bot.command()
async def ban_player(ctx, categoria: str, jogador_nome: str):
    if categoria not in matches:
        matches[categoria] = {"banned_players": []}
    elif "banned_players" not in matches[categoria]:
        matches[categoria]["banned_players"] = []

    if jogador_nome in signed_up_players[categoria]:
        if jogador_nome not in matches[categoria]["banned_players"]:
            matches[categoria]["banned_players"].append(jogador_nome)
            await ctx.send(f"Jogador {jogador_nome} foi banido para {categoria}.")
        else:
            await ctx.send(f"Jogador {jogador_nome} já foi banido.")
    else:
        await ctx.send(f"Jogador {jogador_nome} não está inscrito para {categoria}.")

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
            "kd_ratio": round(jogador['kd_ratio'], 2),
            "headshots": jogador['headshots'],
            "avatar_url": "https://example.com/avatar.png"  # Substitua pelo URL real do avatar
        }
        card_path = generate_player_card(jogador_nome, stats)

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
    query = "SELECT * FROM players ORDER BY kd_ratio DESC LIMIT 10"
    jogadores = conn.execute(query).fetchall()
    conn.close()

    if jogadores:
        leaderboard = "\n".join([f"{i+1}. {jogador['nome']}: {jogador['kd_ratio']}" for i, jogador in enumerate(jogadores)])
        await ctx.send(f"Top 10 Jogadores:\n{leaderboard}")
    else:
        await ctx.send("Nenhum jogador registrado ainda.")

@bot.command()
async def upload_demo(ctx, attachment: discord.Attachment):
    if not attachment.filename.endswith('.dem'):
        await ctx.send("Por favor, envie um arquivo .dem válido.")
        return

    # Salva o arquivo no servidor
    demo_path = f"/var/www/stats/demos/{attachment.filename}"
    await attachment.save(demo_path)

    # Adiciona à fila de processamento
    conn = get_db_connection()
    query = "INSERT INTO demos (file_path, status) VALUES (?, 'pending')"
    conn.execute(query, (demo_path,))
    conn.commit()
    conn.close()

    await ctx.send(f"Arquivo {attachment.filename} enviado com sucesso! Aguardando processamento.")

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

        if membros no canal == MAX_PLAYERS:
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

async def start_server(text_channel, categoria):
    conn = get_db_connection()
    query = "INSERT INTO active_servers (categoria, status, score) VALUES (?, 'running', '0-0')"
    conn.execute(query, (categoria,))
    conn.commit()
    conn.close()

    await text_channel.send(f"Servidor para {categoria} iniciado! Placar inicial: 0-0")

    # Inicia o servidor de CS2 usando RCON ou outro método
    start_cs2_server(categoria)

def start_cs2_server(categoria):
    # Exemplo de comando para iniciar o servidor de CS2
    # Substitua pelo comando real para iniciar o servidor
    if categoria == "5v5":
        command = "/caminho/para/start_cs2_5v5.sh"
    elif categoria == "2v2":
        command = "/caminho/para/start_cs2_2v2.sh"
    elif categoria == "Retakes":
        command = "/caminho/para/start_cs2_retakes.sh"
    
    subprocess.Popen(command, shell=True)

def generate_player_card(jogador_nome, stats):
    # Carrega o avatar do jogador
    avatar_url = stats.get("avatar_url")
    response = requests.get(avatar_url)
    avatar = Image.open(io.BytesIO(response.content)).resize((100, 100))

    # Cria a imagem
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Adiciona o avatar
    img.paste(avatar, (20, 20))

    # Adiciona texto
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    draw.text((140, 20), f"Nome: {jogador_nome}", fill=(0, 0, 0), font=font)
    draw.text((140, 50), f"Kills: {stats['kills']}", fill=(0, 0, 0), font=font)
    draw.text((140, 80), f"Mortes: {stats['mortes']}", fill=(0, 0, 0), font=font)
    draw.text((140, 110), f"K/D: {stats['kd_ratio']}", fill=(0, 0, 0), font=font)
    draw.text((140, 140), f"Headshots: {stats['headshots']}", fill=(0, 0, 0), font=font)

    # Salva a imagem
    card_path = f"/var/www/stats/player_cards/{jogador_nome}_card.png"
    img.save(card_path)
    return card_path

def log_message(mensagem, logFile='/var/www/stats/logs/general.log'):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(logFile, 'a') as file:
        file.write(f"[{timestamp}] {mensagem}\n")

# Executa o bot
bot.run(TOKEN)