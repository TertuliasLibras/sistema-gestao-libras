import os
import json
import streamlit as st

# Caminho para o arquivo de configurações
CONFIG_FILE = "data/system_config.json"

# Configurações padrão
DEFAULT_CONFIG = {
    "logo_path": "assets/images/logo.png",
    "system_name": "Sistema de Gestão - Pós-Graduação Libras",
    "theme_color": "#1E88E5"
}

def load_config():
    """Carregar configurações do sistema"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar configurações: {e}")
            return DEFAULT_CONFIG
    else:
        # Se o arquivo não existir, criar com configurações padrão
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config_data):
    """Salvar configurações do sistema"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {e}")
        return False

def get_logo_path():
    """Obter o caminho da logo atual"""
    config = load_config()
    return config.get("logo_path", DEFAULT_CONFIG["logo_path"])

def save_uploaded_logo(uploaded_file):
    """Salvar logo enviada pelo usuário"""
    try:
        # Criar diretório se não existir
        logo_dir = "assets/images"
        os.makedirs(logo_dir, exist_ok=True)
        
        # Definir caminho do arquivo
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        file_path = f"{logo_dir}/custom_logo{file_extension}"
        
        # Salvar arquivo
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Atualizar configuração
        config = load_config()
        config["logo_path"] = file_path
        save_config(config)
        
        return file_path
    except Exception as e:
        st.error(f"Erro ao salvar logo: {e}")
        return None
