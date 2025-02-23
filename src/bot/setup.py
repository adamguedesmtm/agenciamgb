import os
import json
from pathlib import Path

def main():
    print("⚙️ Configuração Inicial do CS2 Discord Bot")
    print("Este script irá configurar todos os parâmetros necessários para o funcionamento do bot.")
    print("Certifique-se de ter todas as informações antes de continuar.\n")

    # Diretório base
    base_dir = Path(__file__).parent.parent / "config"
    base_dir.mkdir(parents=True, exist_ok=True)
    config_file = base_dir / "config.json"

    # Configurações principais
    config = {}

    # 1. Configurações do Discord
    print("⏳ Configurando Discord...")
    discord_token = input("Insira o token do bot Discord: ").strip()
    with open(".env", "w") as env_file:
        env_file.write(f"DISCORD_TOKEN={discord_token}\n")

    config['discord'] = {}
    config['discord']['prefix'] = input("Insira o prefixo dos comandos (! por padrão): ").strip() or "!"
    config['discord']['admin_role'] = input("Insira o nome da role administradora (Admin por padrão): ").strip() or "Admin"

    # 2. Configurações do Banco de Dados
    print("\n⏳ Configurando Banco de Dados...")
    config['database'] = {}
    config['database']['host'] = input("Insira o host do banco de dados (localhost por padrão): ").strip() or "localhost"
    config['database']['port'] = int(input("Insira a porta do banco de dados (5432 por padrão): ").strip() or 5432)
    config['database']['name'] = input("Insira o nome do banco de dados: ").strip()
    config['database']['user'] = input("Insira o usuário do banco de dados: ").strip()
    config['database']['password'] = input("Insira a senha do banco de dados: ").strip()

    # 3. Configurações dos Servidores CS2
    print("\n⏳ Configurando Servidores CS2...")
    config['servers'] = {}

    competitive = {}
    competitive['host'] = input("Insira o host do servidor competitivo (localhost por padrão): ").strip() or "localhost"
    competitive['port'] = int(input("Insira a porta do servidor competitivo (27015 por padrão): ").strip() or 27015)
    competitive['rcon_password'] = input("Insira a senha RCON do servidor competitivo: ").strip()
    competitive['server_password'] = input("Insira a senha do servidor competitivo (deixe em branco se não houver): ").strip()
    competitive['maps'] = input("Insira os mapas disponíveis para o modo competitivo (separados por vírgula): ").strip().split(",")
    competitive['maps'] = [m.strip() for m in competitive['maps']]
    config['servers']['competitive'] = competitive

    wingman = {}
    wingman['host'] = input("Insira o host do servidor Wingman (localhost por padrão): ").strip() or "localhost"
    wingman['port'] = int(input("Insira a porta do servidor Wingman (27016 por padrão): ").strip() or 27016)
    wingman['rcon_password'] = input("Insira a senha RCON do servidor Wingman: ").strip()
    wingman['server_password'] = input("Insira a senha do servidor Wingman (deixe em branco se não houver): ").strip()
    wingman['maps'] = input("Insira os mapas disponíveis para o modo Wingman (separados por vírgula): ").strip().split(",")
    wingman['maps'] = [m.strip() for m in wingman['maps']]
    config['servers']['wingman'] = wingman

    retake = {}
    retake['host'] = input("Insira o host do servidor Retake (localhost por padrão): ").strip() or "localhost"
    retake['port'] = int(input("Insira a porta do servidor Retake (27017 por padrão): ").strip() or 27017)
    retake['rcon_password'] = input("Insira a senha RCON do servidor Retake: ").strip()
    retake['server_password'] = input("Insira a senha do servidor Retake (deixe em branco se não houver): ").strip()
    retake['maps'] = input("Insira os mapas disponíveis para o modo Retake (separados por vírgula): ").strip().split(",")
    retake['maps'] = [m.strip() for m in retake['maps']]
    config['servers']['retake'] = retake

    # Salvar configurações no arquivo JSON
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)

    print(f"\n✅ Configurações salvas em {config_file}")
    print("Você pode agora iniciar o bot usando o arquivo principal.")


if __name__ == "__main__":
    main()