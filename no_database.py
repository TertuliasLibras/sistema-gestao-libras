import os
import pandas as pd
import streamlit as st
from datetime import datetime

# Simulação das funções de database.py para o Streamlit Cloud
def load_students():
    """Carrega todos os estudantes"""
    try:
        if os.path.exists("data/students.csv"):
            df = pd.read_csv("data/students.csv")
            # Converter para formato similar ao Supabase
            return df.to_dict("records")
        return []
    except Exception as e:
        st.error(f"Erro ao carregar estudantes: {e}")
        return []

def load_payments():
    """Carrega todos os pagamentos"""
    try:
        if os.path.exists("data/payments.csv"):
            df = pd.read_csv("data/payments.csv")
            return df.to_dict("records")
        return []
    except Exception as e:
        st.error(f"Erro ao carregar pagamentos: {e}")
        return []

def load_internships():
    """Carrega todos os estágios"""
    try:
        if os.path.exists("data/internships.csv"):
            df = pd.read_csv("data/internships.csv")
            return df.to_dict("records")
        return []
    except Exception as e:
        st.error(f"Erro ao carregar estágios: {e}")
        return []

def save_student(student_data):
    """Salva um novo estudante"""
    try:
        students = load_students()
        # Verificar se já existe pelo telefone
        exists = False
        for i, student in enumerate(students):
            if student.get("phone") == student_data.get("phone"):
                students[i] = student_data
                exists = True
                break
        
        if not exists:
            students.append(student_data)
        
        # Salvar como CSV
        pd.DataFrame(students).to_csv("data/students.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar estudante: {e}")
        return False

def update_student(phone, student_data):
    """Atualiza os dados de um estudante existente"""
    return save_student(student_data)

def delete_student(phone):
    """Exclui um estudante"""
    try:
        students = load_students()
        students = [s for s in students if s.get("phone") != phone]
        pd.DataFrame(students).to_csv("data/students.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao excluir estudante: {e}")
        return False

def save_payment(payment_data):
    """Salva um novo pagamento"""
    try:
        payments = load_payments()
        # Adicionar ID se não existir
        if "id" not in payment_data:
            max_id = 0
            for payment in payments:
                if payment.get("id", 0) > max_id:
                    max_id = payment.get("id")
            payment_data["id"] = max_id + 1
        
        payments.append(payment_data)
        pd.DataFrame(payments).to_csv("data/payments.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar pagamento: {e}")
        return False

def update_payment(payment_id, payment_data):
    """Atualiza os dados de um pagamento existente"""
    try:
        payments = load_payments()
        for i, payment in enumerate(payments):
            if payment.get("id") == payment_id:
                payments[i] = payment_data
                break
        
        pd.DataFrame(payments).to_csv("data/payments.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar pagamento: {e}")
        return False

def delete_payment(payment_id):
    """Exclui um pagamento"""
    try:
        payments = load_payments()
        payments = [p for p in payments if p.get("id") != payment_id]
        pd.DataFrame(payments).to_csv("data/payments.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao excluir pagamento: {e}")
        return False

def delete_student_payments(phone):
    """Exclui todos os pagamentos de um estudante"""
    try:
        payments = load_payments()
        payments = [p for p in payments if p.get("phone") != phone]
        pd.DataFrame(payments).to_csv("data/payments.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao excluir pagamentos do estudante: {e}")
        return False

def save_internship(internship_data):
    """Salva um novo estágio"""
    try:
        internships = load_internships()
        # Adicionar ID se não existir
        if "id" not in internship_data:
            max_id = 0
            for internship in internships:
                if internship.get("id", 0) > max_id:
                    max_id = internship.get("id")
            internship_data["id"] = max_id + 1
        
        internships.append(internship_data)
        pd.DataFrame(internships).to_csv("data/internships.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar estágio: {e}")
        return False

def update_internship(internship_id, internship_data):
    """Atualiza os dados de um estágio existente"""
    try:
        internships = load_internships()
        for i, internship in enumerate(internships):
            if internship.get("id") == internship_id:
                internships[i] = internship_data
                break
        
        pd.DataFrame(internships).to_csv("data/internships.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar estágio: {e}")
        return False

def delete_internship(internship_id):
    """Exclui um estágio"""
    try:
        internships = load_internships()
        internships = [i for i in internships if i.get("id") != internship_id]
        pd.DataFrame(internships).to_csv("data/internships.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao excluir estágio: {e}")
        return False

# Funções para autenticação
def authenticate_user(username, password_hash):
    """Autentica um usuário"""
    try:
        users = load_users()
        for user in users:
            if user.get("username") == username and user.get("password_hash") == password_hash:
                return user
        return None
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return None

def load_users():
    """Carrega todos os usuários"""
    try:
        if os.path.exists("data/users.csv"):
            df = pd.read_csv("data/users.csv")
            return df.to_dict("records")
        # Criar usuário admin padrão se não existir
        admin_data = {
            "id": 1,
            "username": "admin",
            "password_hash": "0192023a7bbd73250516f069df18b500",  # md5 hash de "admin123"
            "name": "Administrador",
            "level": "admin",
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        pd.DataFrame([admin_data]).to_csv("data/users.csv", index=False)
        return [admin_data]
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")
        return []

def save_user(user_data):
    """Salva um novo usuário"""
    try:
        users = load_users()
        # Adicionar ID se não existir
        if "id" not in user_data:
            max_id = 0
            for user in users:
                if user.get("id", 0) > max_id:
                    max_id = user.get("id")
            user_data["id"] = max_id + 1
        
        users.append(user_data)
        pd.DataFrame(users).to_csv("data/users.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuário: {e}")
        return False

def update_user(user_id, user_data):
    """Atualiza os dados de um usuário existente"""
    try:
        users = load_users()
        for i, user in enumerate(users):
            if user.get("id") == user_id:
                users[i] = user_data
                break
        
        pd.DataFrame(users).to_csv("data/users.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar usuário: {e}")
        return False

def delete_user(user_id):
    """Exclui um usuário"""
    try:
        users = load_users()
        users = [u for u in users if u.get("id") != user_id]
        pd.DataFrame(users).to_csv("data/users.csv", index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao excluir usuário: {e}")
        return False

# Inicialização
def init_database():
    """Cria diretório de dados se não existir"""
    os.makedirs("data", exist_ok=True)
    # Verificar se há arquivos CSV e criar se não existirem
    if not os.path.exists("data/students.csv"):
        pd.DataFrame(columns=["name", "phone", "cpf", "email", "course_type", "status", "enrollment_date", "monthly_fee", "payment_plan", "due_day", "address", "city", "state", "origin"]).to_csv("data/students.csv", index=False)
    
    if not os.path.exists("data/payments.csv"):
        pd.DataFrame(columns=["id", "phone", "student_name", "payment_date", "due_date", "amount", "status", "month", "year", "payment_method", "notes"]).to_csv("data/payments.csv", index=False)
    
    if not os.path.exists("data/internships.csv"):
        pd.DataFrame(columns=["id", "phone", "student_name", "date", "hours", "topic", "supervisor", "location", "notes", "status"]).to_csv("data/internships.csv", index=False)
    
    # Usuários
    load_users()  # Isso já cria o usuário admin se não existir

# Inicializar banco de dados na inicialização
init_database()
