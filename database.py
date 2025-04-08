import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar conexão com o Supabase (priorizar variáveis do Streamlit Secrets)
def init_connection():
    # Tentar usar variáveis do Streamlit Secrets primeiro
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        # Cair para variáveis de ambiente se Secrets não estiver disponível
        try:
            # Obter as variáveis de ambiente diretamente
            url = "https://apgjdytrovjdhnutkzqp.supabase.co"
            key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFwZ2pkeXRyb3ZqZGhudXRrenFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxMTkxMDcsImV4cCI6MjA1OTY5NTEwN30.mSmjrkoc5DaFAIwek5VThxX_GQwsWWGFif5rgDjoIr8"
            
            if not url or not key:
                # Usando mensagem de erro mais amigável para o usuário
                st.error("Configuração do banco de dados não encontrada. Por favor, configure as credenciais do Supabase.")
                return None
            
            # Verificar formato da URL
            if url and not url.startswith("https://"):
                st.error(f"URL do Supabase inválida. Deve começar com https://")
                return None
                
            return create_client(url, key)
        except Exception as e:
            st.error(f"Erro ao conectar com o banco de dados: {e}")
            return None

# Inicializar cliente do Supabase (usando caching para melhor desempenho)
@st.cache_resource
def get_connection():
    return init_connection()

# Operações de CRUD para a tabela students

def load_students():
    """Carrega todos os estudantes do banco de dados"""
    supabase = get_connection()
    if not supabase:
        return []
    
    try:
        response = supabase.table("students").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao carregar dados de estudantes: {e}")
        return []

def save_student(student_data):
    """Salva um novo estudante no banco de dados"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        # Verificar se o estudante já existe (pelo phone)
        existing = supabase.table("students").select("*").eq("phone", student_data["phone"]).execute()
        
        if existing.data:
            # Atualiza se existir
            supabase.table("students").update(student_data).eq("phone", student_data["phone"]).execute()
        else:
            # Insere se não existir
            supabase.table("students").insert(student_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar estudante: {e}")
        return False

def update_student(phone, student_data):
    """Atualiza os dados de um estudante existente"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("students").update(student_data).eq("phone", phone).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar estudante: {e}")
        return False

def delete_student(phone):
    """Exclui um estudante do banco de dados"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("students").delete().eq("phone", phone).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir estudante: {e}")
        return False

# Operações de CRUD para a tabela payments

def load_payments():
    """Carrega todos os pagamentos do banco de dados"""
    supabase = get_connection()
    if not supabase:
        return []
    
    try:
        response = supabase.table("payments").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao carregar dados de pagamentos: {e}")
        return []

def save_payment(payment_data):
    """Salva um novo pagamento no banco de dados"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("payments").insert(payment_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar pagamento: {e}")
        return False

def update_payment(payment_id, payment_data):
    """Atualiza os dados de um pagamento existente"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("payments").update(payment_data).eq("id", payment_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar pagamento: {e}")
        return False

def delete_payment(payment_id):
    """Exclui um pagamento do banco de dados"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("payments").delete().eq("id", payment_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir pagamento: {e}")
        return False

def delete_student_payments(phone):
    """Exclui todos os pagamentos associados a um estudante"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("payments").delete().eq("phone", phone).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir pagamentos do estudante: {e}")
        return False

# Operações de CRUD para a tabela internships

def load_internships():
    """Carrega todos os estágios do banco de dados"""
    supabase = get_connection()
    if not supabase:
        return []
    
    try:
        response = supabase.table("internships").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao carregar dados de estágios: {e}")
        return []

def save_internship(internship_data):
    """Salva um novo estágio no banco de dados"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("internships").insert(internship_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar estágio: {e}")
        return False

def update_internship(internship_id, internship_data):
    """Atualiza os dados de um estágio existente"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("internships").update(internship_data).eq("id", internship_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar estágio: {e}")
        return False

def delete_internship(internship_id):
    """Exclui um estágio do banco de dados"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("internships").delete().eq("id", internship_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir estágio: {e}")
        return False

# Operações para a tabela de usuários

def authenticate_user(username, password_hash):
    """Autentica um usuário com base no nome de usuário e senha hasheada"""
    supabase = get_connection()
    if not supabase:
        return None
    
    try:
        response = supabase.table("users").select("*").eq("username", username).eq("password_hash", password_hash).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erro ao autenticar usuário: {e}")
        return None

def load_users():
    """Carrega todos os usuários do banco de dados"""
    supabase = get_connection()
    if not supabase:
        return []
    
    try:
        response = supabase.table("users").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao carregar dados de usuários: {e}")
        return []

def save_user(user_data):
    """Salva um novo usuário no banco de dados"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("users").insert(user_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuário: {e}")
        return False

def update_user(user_id, user_data):
    """Atualiza os dados de um usuário existente"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("users").update(user_data).eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar usuário: {e}")
        return False

def delete_user(user_id):
    """Exclui um usuário do banco de dados"""
    supabase = get_connection()
    if not supabase:
        return False
    
    try:
        supabase.table("users").delete().eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir usuário: {e}")
        return False
