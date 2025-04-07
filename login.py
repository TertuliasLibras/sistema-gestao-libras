import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime, timedelta
from config import get_logo_path

# Nome da variável de sessão para login
LOGIN_SESSION_VAR = "usuario_autenticado"
LOGIN_EXPIRY_VAR = "login_expiracao"
# Tempo de expiração da sessão em horas
LOGIN_EXPIRY_HOURS = 12

# Função para hash de senha
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Função para carregar usuários
def carregar_usuarios():
    # Criar o diretório de dados se não existir
    os.makedirs("data", exist_ok=True)
    
    # Verificar se o arquivo existe
    if os.path.exists("data/usuarios.csv"):
        return pd.read_csv("data/usuarios.csv")
    else:
        # Criar arquivo com usuário admin padrão
        usuarios_df = pd.DataFrame([{
            "usuario": "admin",
            "senha_hash": hash_senha("admin123"),
            "nome": "Administrador",
            "nivel": "admin"
        }])
        usuarios_df.to_csv("data/usuarios.csv", index=False)
        return usuarios_df

def salvar_usuarios(df):
    df.to_csv("data/usuarios.csv", index=False)

# Função para verificar login
def verificar_login(usuario, senha):
    usuarios_df = carregar_usuarios()
    
    # Verificar se o usuário existe
    if usuario in usuarios_df["usuario"].values:
        # Obter o hash da senha armazenada
        senha_hash = usuarios_df.loc[usuarios_df["usuario"] == usuario, "senha_hash"].values[0]
        
        # Verificar se a senha corresponde
        if senha_hash == hash_senha(senha):
            # Obter o nível de acesso
            nivel = usuarios_df.loc[usuarios_df["usuario"] == usuario, "nivel"].values[0]
            nome = usuarios_df.loc[usuarios_df["usuario"] == usuario, "nome"].values[0]
            
            # Definir expiração
            expiracao = datetime.now() + timedelta(hours=LOGIN_EXPIRY_HOURS)
            
            return True, nivel, nome, expiracao
    
    return False, None, None, None

# Função para verificar se o usuário está logado
def verificar_autenticacao():
    if LOGIN_SESSION_VAR in st.session_state and LOGIN_EXPIRY_VAR in st.session_state:
        # Verificar se o login expirou
        if datetime.now() < st.session_state[LOGIN_EXPIRY_VAR]:
            return True
    
    return False

# Função para fazer logout
def logout():
    if LOGIN_SESSION_VAR in st.session_state:
        del st.session_state[LOGIN_SESSION_VAR]
    
    if LOGIN_EXPIRY_VAR in st.session_state:
        del st.session_state[LOGIN_EXPIRY_VAR]

# Página de login
def mostrar_pagina_login():
    # Custom CSS para estilizar o logo
    st.markdown("""
    <style>
        .logo-container {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
        }
        .logo-text {
            margin-left: 1rem;
            font-size: 1.5rem;
        }
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stButton > button {
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header com logo
    col1, col2 = st.columns([1, 3])
    with col1:
        try:
            # Tentar usar a logo configurada
            logo_path = get_logo_path()
            
            # Verificar se o arquivo existe
            if os.path.exists(logo_path):
                st.image(logo_path, width=120)
            else:
                # Tentar alternativas
                if os.path.exists('assets/images/logo.svg'):
                    st.image('assets/images/logo.svg', width=120)
                elif os.path.exists('assets/images/logo.png'):
                    st.image('assets/images/logo.png', width=120)
                else:
                    st.markdown("**LOGO**")
        except Exception as e:
            # Em caso de erro, mostrar mensagem e tentar logo padrão
            if os.path.exists('assets/images/logo.svg'):
                st.image('assets/images/logo.svg', width=120)
            else:
                st.markdown("**LOGO**")
    with col2:
        st.title("Sistema de Gestão Libras")

    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    
    st.subheader("Login")
    
    # Formulário de login
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        submetido = st.form_submit_button("Entrar")
        
        if submetido:
            if usuario and senha:
                autenticado, nivel, nome, expiracao = verificar_login(usuario, senha)
                
                if autenticado:
                    # Armazenar informações na sessão
                    st.session_state[LOGIN_SESSION_VAR] = {
                        "usuario": usuario,
                        "nivel": nivel,
                        "nome": nome
                    }
                    st.session_state[LOGIN_EXPIRY_VAR] = expiracao
                    
                    st.success(f"Bem-vindo, {nome}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")
            else:
                st.warning("Por favor, informe o usuário e a senha")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Rodapé
    st.markdown("<div style='text-align: center; margin-top: 50px; opacity: 0.7;'>© 2025 Sistema de Gestão Libras</div>", unsafe_allow_html=True)

# Função para gerenciar usuários (somente para admin)
def pagina_gerenciar_usuarios():
    if (LOGIN_SESSION_VAR in st.session_state and 
        st.session_state[LOGIN_SESSION_VAR]["nivel"] == "admin"):
        
        st.subheader("Gerenciar Usuários")
        
        usuarios_df = carregar_usuarios()
        
        # Criar novo usuário
        with st.expander("Adicionar Novo Usuário"):
            with st.form("novo_usuario_form"):
                novo_usuario = st.text_input("Nome de Usuário")
                nova_senha = st.text_input("Senha", type="password")
                confirmar_senha = st.text_input("Confirmar Senha", type="password")
                nome_completo = st.text_input("Nome Completo")
                nivel = st.selectbox("Nível de Acesso", ["usuario", "admin"])
                
                submetido = st.form_submit_button("Adicionar Usuário")
                
                if submetido:
                    if not novo_usuario or not nova_senha or not nome_completo:
                        st.warning("Todos os campos são obrigatórios")
                    elif nova_senha != confirmar_senha:
                        st.error("As senhas não coincidem")
                    elif novo_usuario in usuarios_df["usuario"].values:
                        st.error("Este nome de usuário já existe")
                    else:
                        # Adicionar novo usuário
                        novo_df = pd.DataFrame([{
                            "usuario": novo_usuario,
                            "senha_hash": hash_senha(nova_senha),
                            "nome": nome_completo,
                            "nivel": nivel
                        }])
                        
                        usuarios_df = pd.concat([usuarios_df, novo_df], ignore_index=True)
                        salvar_usuarios(usuarios_df)
                        st.success("Usuário adicionado com sucesso!")
                        st.rerun()
        
        # Listar usuários
        if not usuarios_df.empty:
            st.subheader("Usuários Cadastrados")
            
            # Criar cópia para exibição (sem mostrar hash)
            usuarios_exibicao = usuarios_df[["usuario", "nome", "nivel"]].copy()
            
            # Renomear colunas para exibição
            usuarios_exibicao.columns = ["Usuário", "Nome", "Nível de Acesso"]
            
            st.dataframe(usuarios_exibicao, use_container_width=True)
            
            # Alterar senha
            with st.expander("Alterar Senha de Usuário"):
                with st.form("alterar_senha_form"):
                    usuario_selecionado = st.selectbox(
                        "Selecione o Usuário",
                        options=usuarios_df["usuario"].tolist()
                    )
                    
                    nova_senha = st.text_input("Nova Senha", type="password")
                    confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
                    
                    submetido = st.form_submit_button("Alterar Senha")
                    
                    if submetido:
                        if not nova_senha:
                            st.warning("Informe a nova senha")
                        elif nova_senha != confirmar_senha:
                            st.error("As senhas não coincidem")
                        else:
                            # Atualizar senha
                            usuarios_df.loc[usuarios_df["usuario"] == usuario_selecionado, "senha_hash"] = hash_senha(nova_senha)
                            salvar_usuarios(usuarios_df)
                            st.success("Senha alterada com sucesso!")
            
            # Remover usuário
            with st.expander("Remover Usuário"):
                with st.form("remover_usuario_form"):
                    usuario_remover = st.selectbox(
                        "Selecione o Usuário para Remover",
                        options=usuarios_df[usuarios_df["usuario"] != "admin"]["usuario"].tolist()
                    )
                    
                    st.warning("Esta ação não pode ser desfeita!")
                    confirmacao = st.checkbox("Confirmo que desejo remover este usuário")
                    
                    submetido = st.form_submit_button("Remover Usuário")
                    
                    if submetido:
                        if not confirmacao:
                            st.error("Você precisa confirmar a remoção")
                        else:
                            # Remover usuário
                            usuarios_df = usuarios_df[usuarios_df["usuario"] != usuario_remover]
                            salvar_usuarios(usuarios_df)
                            st.success("Usuário removido com sucesso!")
                            st.rerun()
    else:
        st.error("Acesso negado. Você não tem permissão para gerenciar usuários.")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Login - Sistema de Gestão Libras",
        page_icon="🔐",
        layout="wide"
    )
    
    mostrar_pagina_login()
