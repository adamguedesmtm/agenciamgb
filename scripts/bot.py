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

# Comandos e eventos adicionais...