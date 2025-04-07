import streamlit as st
import pandas as pd
import hashlib
import os
from datetime import datetime

# Initialize session state for authentication
if 'usuario_autenticado' not in st.session_state:
    st.session_state['usuario_autenticado'] = None
if 'tentativas_login' not in st.session_state:
    st.session_state['tentativas_login'] = 0

def hash_senha(senha):
    """Hash a password for security"""
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_usuarios():
    """Load users from CSV file or create default admin if file doesn't exist"""
    users_path = "data/users.csv"
    os.makedirs("data", exist_ok=True)
    
    if not os.path.exists(users_path):
        # Create default admin user
        admin_hash = hash_senha("admin123")
        df = pd.DataFrame({
            'usuario': ['admin'],
            'senha_hash': [admin_hash],
            'nome': ['Administrador'],
            'email': ['admin@example.com'],
            'nivel': ['admin'],
            'data_cadastro': [datetime.now().strftime('%Y-%m-%d')]
        })
        df.to_csv(users_path, index=False)
        return df
    
    try:
        return pd.read_csv(users_path)
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")
        return pd.DataFrame()

def salvar_usuarios(df):
    """Save users to CSV file"""
    users_path = "data/users.csv"
    os.makedirs("data", exist_ok=True)
    
    try:
        df.to_csv(users_path, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuários: {e}")
        return False

def verificar_login(usuario, senha):
    """Verify login credentials"""
    users_df = carregar_usuarios()
    
    if users_df.empty:
        return False
    
    # Check if user exists
    user_row = users_df[users_df['usuario'] == usuario]
    if user_row.empty:
        return False
    
    # Check password
    senha_hash = hash_senha(senha)
    if user_row.iloc[0]['senha_hash'] == senha_hash:
        # Set authenticated user in session state
        st.session_state['usuario_autenticado'] = {
            'usuario': usuario,
            'nome': user_row.iloc[0]['nome'],
            'email': user_row.iloc[0]['email'],
            'nivel': user_row.iloc[0]['nivel']
        }
        st.session_state['tentativas_login'] = 0
        return True
    
    return False

def verificar_autenticacao():
    """Check if a user is authenticated"""
    return st.session_state.get('usuario_autenticado') is not None

def logout():
    """Log out the current user"""
    st.session_state['usuario_autenticado'] = None

def mostrar_pagina_login():
    """Display the login page"""
    st.header("Sistema de Gestão - Pós-Graduação Libras")
    
    # Add logo to login page
    st.image('assets/images/logo.svg', width=250)
    
    st.subheader("Login")
    
    # Login form
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        
        if submitted:
            if verificar_login(usuario, senha):
                st.rerun()
            else:
                st.session_state['tentativas_login'] += 1
                st.error(f"Usuário ou senha incorretos. Tentativa {st.session_state['tentativas_login']} de 5.")
                
                if st.session_state['tentativas_login'] >= 5:
                    st.error("Número máximo de tentativas alcançado. Por favor, tente novamente mais tarde.")
    
    st.markdown("---")
    st.info("Sistema de Gestão para Pós-Graduação em Libras")

def pagina_gerenciar_usuarios():
    """Display the user management page"""
    st.header("Gerenciamento de Usuários")
    
    if st.session_state.get('usuario_autenticado', {}).get('nivel') != 'admin':
        st.error("Você não tem permissão para acessar esta página.")
        return
    
    users_df = carregar_usuarios()
    
    # Create tabs for viewing and adding users
    tab1, tab2 = st.tabs(["Usuários Cadastrados", "Adicionar Usuário"])
    
    with tab1:
        # Display users
        if not users_df.empty:
            # Don't show password hash
            display_df = users_df.drop(columns=['senha_hash'])
            st.dataframe(display_df, use_container_width=True)
            
            # Delete user option
            st.subheader("Remover Usuário")
            user_to_delete = st.selectbox(
                "Selecione um usuário para remover",
                users_df['usuario'].tolist(),
                index=None
            )
            
            if user_to_delete:
                if user_to_delete == 'admin':
                    st.error("O usuário 'admin' não pode ser removido.")
                elif user_to_delete == st.session_state['usuario_autenticado']['usuario']:
                    st.error("Você não pode remover seu próprio usuário.")
                else:
                    if st.button(f"Confirmar remoção de {user_to_delete}"):
                        users_df = users_df[users_df['usuario'] != user_to_delete]
                        if salvar_usuarios(users_df):
                            st.success(f"Usuário {user_to_delete} removido com sucesso.")
                            st.rerun()
                        else:
                            st.error("Erro ao remover usuário.")
            
            # Change password option
            st.subheader("Alterar Senha")
            user_to_change = st.selectbox(
                "Selecione um usuário para alterar a senha",
                users_df['usuario'].tolist(),
                index=None,
                key="change_password_select"
            )
            
            if user_to_change:
                with st.form("change_password_form"):
                    new_password = st.text_input("Nova senha", type="password")
                    confirm_password = st.text_input("Confirme a nova senha", type="password")
                    submit_change = st.form_submit_button("Alterar Senha")
                    
                    if submit_change:
                        if new_password != confirm_password:
                            st.error("As senhas não coincidem.")
                        elif len(new_password) < 6:
                            st.error("A senha deve ter pelo menos 6 caracteres.")
                        else:
                            # Update password
                            user_index = users_df[users_df['usuario'] == user_to_change].index[0]
                            users_df.at[user_index, 'senha_hash'] = hash_senha(new_password)
                            
                            if salvar_usuarios(users_df):
                                st.success(f"Senha do usuário {user_to_change} alterada com sucesso.")
                            else:
                                st.error("Erro ao alterar senha.")
        else:
            st.warning("Não há usuários cadastrados.")
    
    with tab2:
        # Add user form
        st.subheader("Adicionar Novo Usuário")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Nome de usuário")
            new_name = st.text_input("Nome completo")
            new_email = st.text_input("E-mail")
            new_password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirme a senha", type="password")
            new_level = st.selectbox("Nível", ["user", "admin"])
            
            submit_add = st.form_submit_button("Adicionar Usuário")
            
            if submit_add:
                # Validate form
                if not new_username or not new_name or not new_email or not new_password:
                    st.error("Todos os campos são obrigatórios.")
                elif new_password != confirm_password:
                    st.error("As senhas não coincidem.")
                elif len(new_password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                elif not users_df.empty and new_username in users_df['usuario'].values:
                    st.error(f"O usuário '{new_username}' já existe.")
                else:
                    # Add new user
                    new_user = pd.DataFrame({
                        'usuario': [new_username],
                        'senha_hash': [hash_senha(new_password)],
                        'nome': [new_name],
                        'email': [new_email],
                        'nivel': [new_level],
                        'data_cadastro': [datetime.now().strftime('%Y-%m-%d')]
                    })
                    
                    if users_df.empty:
                        users_df = new_user
                    else:
                        users_df = pd.concat([users_df, new_user], ignore_index=True)
                    
                    if salvar_usuarios(users_df):
                        st.success(f"Usuário {new_username} adicionado com sucesso.")
                    else:
                        st.error("Erro ao adicionar usuário.")
