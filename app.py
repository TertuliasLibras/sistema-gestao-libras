import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Configuração da página
st.set_page_config(
    page_title="Tertúlia Libras - Sistema de Gestão",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard simplificado para demonstração
st.title("Dashboard - Tertúlia Libras")
st.subheader("Versão de Demonstração")

st.info("""
Esta é uma versão de demonstração do Sistema de Gestão para Tertúlia Libras.
O sistema completo inclui:
- Gerenciamento de alunos
- Controle de pagamentos
- Registro de estágios
- Relatórios e dashboards
- Sistema de autenticação de usuários

Para acessar a versão completa com dados reais, é necessário conectar ao banco de dados Supabase.
""")

# Estatísticas simuladas para demonstração
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Alunos Ativos", value="42")
with col2:
    st.metric(label="Receita Mensal", value="R$ 12.600,00")
with col3:
    st.metric(label="Horas de Estágio", value="156")

# Formulário de login demonstrativo
with st.sidebar:
    st.subheader("Login")
    with st.form("login_demo"):
        st.text_input("Usuário", value="admin", disabled=True)
        st.text_input("Senha", value="********", disabled=True, type="password")
        st.form_submit_button("Entrar", disabled=True)
    
    st.caption("Usuário: admin / Senha: admin123")
    st.caption("(Login desativado nesta versão de demonstração)")
