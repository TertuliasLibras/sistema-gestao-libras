from login import verificar_autenticacao, mostrar_pagina_login

# Verificar autenticação
if not verificar_autenticacao():
    mostrar_pagina_login()
    st.stop()  # Parar a execução do restante da página
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils import (
    load_students_data, 
    load_payments_data,
    save_students_data, 
    save_payments_data,
    format_phone,
    validate_phone,
    generate_monthly_payments
)
from config import get_logo_path

st.set_page_config(
    page_title="Alunos - Sistema de Gestão Libras",
    page_icon="👨‍🎓",
    layout="wide"
)

# Custom CSS to style the logo
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
</style>
""", unsafe_allow_html=True)

# Header with logo
col1, col2 = st.columns([1, 3])
with col1:
    try:
        # Usar função para obter o caminho da logo
        logo_path = get_logo_path()
        st.image(logo_path, width=120)
    except Exception as e:
        st.warning(f"Erro ao carregar a logo: {e}")
        st.image('assets/images/logo.svg', width=120)
with col2:
    st.title("Gerenciamento de Alunos")

# Load data
students_df = load_students_data()
payments_df = load_payments_data()

# Create tabs for different operations
tab1, tab2, tab3 = st.tabs(["Cadastrar Alunos", "Listar Alunos", "Editar/Excluir Alunos"])

with tab1:
    st.subheader("Cadastrar Novo Aluno")
    
    with st.form("student_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            phone = st.text_input("Telefone/WhatsApp (Formato: XX XXXXX-XXXX)", help="Este será o identificador principal do aluno")
            name = st.text_input("Nome Completo")
            cpf = st.text_input("CPF", help="CPF do aluno para consulta no portal da faculdade")
            course_type = st.selectbox("Tipo de Curso", 
                                     ["Pós-Graduação", "Aperfeiçoamento Profissional"],
                                     help="Tipo de curso que o aluno está matriculado")
            
        with col2:
            enrollment_date = st.date_input("Data da Matrícula", datetime.now())
            monthly_fee = st.number_input("Mensalidade (R$)", min_value=0.0, step=10.0, format="%.2f")
            payment_plan = st.selectbox("Plano de Pagamento",
                                      [6, 12, 18, 24],
                                      help="Número de parcelas do curso")
            notes = st.text_area("Observações")
        
        submit_button = st.form_submit_button("Cadastrar Aluno")
        
        if submit_button:
            if phone and name and monthly_fee:
                # Validate phone format
                if validate_phone(phone):
                    # Format phone to standard format
                    formatted_phone = format_phone(phone)
                    
                    # Check if phone already exists
                    if students_df is not None and formatted_phone in students_df["phone"].values:
                        st.error(f"Aluno com telefone {formatted_phone} já existe!")
                    else:
                        # Create new student record
                        new_student = {
                            "phone": formatted_phone,
                            "name": name,
                            "cpf": cpf,
                            "course_type": course_type,
                            "enrollment_date": enrollment_date.strftime("%Y-%m-%d"),
                            "status": "active",
                            "cancellation_date": None,
                            "cancellation_fee_paid": False,
                            "monthly_fee": monthly_fee,
                            "payment_plan": payment_plan,  # Adicionando o plano de pagamento
                            "notes": notes
                        }
                        
                        # Add to dataframe
                        if students_df is None:
                            students_df = pd.DataFrame([new_student])
                        else:
                            students_df = pd.concat([students_df, pd.DataFrame([new_student])], ignore_index=True)
                        
                        # Save to CSV
                        save_students_data(students_df)
                        
                        # Generate payment records
                        payment_records = generate_monthly_payments(
                            formatted_phone, 
                            monthly_fee, 
                            enrollment_date,
                            payment_plan=payment_plan  # Usando o plano selecionado
                        )
                        
                        # Add to payments dataframe
                        if payments_df is None:
                            payments_df = pd.DataFrame(payment_records)
                        else:
                            payments_df = pd.concat([payments_df, pd.DataFrame(payment_records)], ignore_index=True)
                        
                        # Save to CSV
                        save_payments_data(payments_df)
                        
                        st.success(f"Aluno {name} cadastrado com sucesso!")
                        st.info(f"Geradas {payment_plan} parcelas mensais no valor de R$ {monthly_fee:.2f}")
                else:
                    st.error("Formato de telefone inválido. Use o formato XX XXXXX-XXXX.")
            else:
                st.error("Preencha todos os campos obrigatórios!")

with tab2:
    st.subheader("Listar Alunos")
    
    if students_df is not None and not students_df.empty:
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filtrar por Status",
                ["Todos", "Ativos", "Cancelados"]
            )
        
        with col2:
            search_name = st.text_input("Buscar por Nome")
        
        with col3:
            if 'course_type' in students_df.columns:
                course_filter = st.selectbox(
                    "Filtrar por Tipo de Curso",
                    ["Todos"] + list(students_df['course_type'].unique())
                )
            else:
                course_filter = "Todos"
        
        # Apply filters
        filtered_df = students_df.copy()
        
        if status_filter == "Ativos":
            filtered_df = filtered_df[filtered_df["status"] == "active"]
        elif status_filter == "Cancelados":
            filtered_df = filtered_df[filtered_df["status"] == "canceled"]
        
        if search_name:
            filtered_df = filtered_df[filtered_df["name"].str.contains(search_name, case=False)]
        
        if course_filter != "Todos" and 'course_type' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["course_type"] == course_filter]
        
        # Display data
        if not filtered_df.empty:
            # Format date columns for display
            if 'enrollment_date' in filtered_df.columns:
                filtered_df['enrollment_date'] = pd.to_datetime(filtered_df['enrollment_date']).dt.strftime('%d/%m/%Y')
            
            if 'cancellation_date' in filtered_df.columns:
                # Handle NaT values before formatting
                filtered_df['cancellation_date'] = pd.to_datetime(filtered_df['cancellation_date'], errors='coerce')
                filtered_df['cancellation_date'] = filtered_df['cancellation_date'].apply(
                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
                )
            
            # Format status for display
            filtered_df['status'] = filtered_df['status'].map({
                'active': 'Ativo',
                'canceled': 'Cancelado'
            })
            
            # Choose columns to display
            display_columns = ['name', 'phone', 'status', 'enrollment_date', 'monthly_fee']
            
            # Add course_type if available
            if 'course_type' in filtered_df.columns:
                display_columns.insert(3, 'course_type')
                
            # Add CPF if available
            if 'cpf' in filtered_df.columns:
                display_columns.insert(3, 'cpf')
                
            # Add payment_plan if available
            if 'payment_plan' in filtered_df.columns:
                display_columns.append('payment_plan')
            
            # Format monthly_fee as currency
            filtered_df['monthly_fee'] = filtered_df['monthly_fee'].apply(lambda x: f"R$ {x:.2f}")
            
            # Create a copy with renamed columns for display
            column_names = {
                'name': 'Nome',
                'phone': 'Telefone',
                'cpf': 'CPF',
                'course_type': 'Tipo de Curso',
                'status': 'Status',
                'enrollment_date': 'Data de Matrícula',
                'monthly_fee': 'Mensalidade',
                'payment_plan': 'Parcelas'
            }
            
            display_df = filtered_df[display_columns].copy()
            display_df.columns = [column_names[col] for col in display_columns]
            
            st.dataframe(display_df, use_container_width=True)
            
            # Download option
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Baixar dados filtrados (CSV)",
                csv,
                "alunos_filtrados.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.warning("Nenhum aluno encontrado com os filtros selecionados.")
    else:
        st.info("Não há alunos cadastrados.")

with tab3:
    st.subheader("Editar/Excluir Alunos")
    
    if students_df is not None and not students_df.empty:
        # Select student to edit
        selected_phone = st.selectbox(
            "Selecione o aluno para editar/excluir",
            options=students_df["phone"].tolist(),
            format_func=lambda x: f"{students_df.loc[students_df['phone'] == x, 'name'].values[0]} ({x})"
        )
        
        # Get selected student data
        student_data = students_df[students_df["phone"] == selected_phone].iloc[0]
        
        # Create edit form
        with st.form("edit_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nome Completo", value=student_data["name"])
                
                # Handle CPF - may not exist in older records
                cpf = ""
                if "cpf" in student_data and pd.notna(student_data["cpf"]):
                    cpf = student_data["cpf"]
                cpf = st.text_input("CPF", value=cpf)
                
                # Handle course type - may not exist in older records
                course_type_options = ["Pós-Graduação", "Aperfeiçoamento Profissional"]
                course_type_index = 0
                if "course_type" in student_data and pd.notna(student_data["course_type"]):
                    try:
                        course_type_index = course_type_options.index(student_data["course_type"])
                    except ValueError:
                        # If value is not in list, default to first option
                        course_type_index = 0
                
                course_type = st.selectbox(
                    "Tipo de Curso", 
                    course_type_options,
                    index=course_type_index
                )
                
                status = st.selectbox(
                    "Status",
                    ["active", "canceled"],
                    index=0 if student_data["status"] == "active" else 1,
                    format_func=lambda x: "Ativo" if x == "active" else "Cancelado"
                )
                
                if status == "canceled":
                    cancellation_date = student_data.get("cancellation_date")
                    if cancellation_date and pd.notna(cancellation_date):
                        cancellation_date = pd.to_datetime(cancellation_date).date()
                    else:
                        cancellation_date = datetime.now().date()
                    
                    cancellation_date = st.date_input("Data de Cancelamento", cancellation_date)
                    cancellation_fee_paid = st.checkbox(
                        "Multa de cancelamento paga",
                        value=bool(student_data.get("cancellation_fee_paid", False))
                    )
                else:
                    cancellation_date = None
                    cancellation_fee_paid = False
            
            with col2:
                # Convert enrollment_date to datetime
                enrollment_date = pd.to_datetime(student_data["enrollment_date"]).date()
                enrollment_date = st.date_input("Data da Matrícula", enrollment_date)
                
                monthly_fee = st.number_input(
                    "Mensalidade (R$)",
                    min_value=0.0,
                    value=float(student_data["monthly_fee"]),
                    step=10.0,
                    format="%.2f"
                )
                
                # Handle payment plan - may not exist in older records
                payment_plan_options = [6, 12, 18, 24]
                payment_plan_index = 1  # Default to 12 parcelas
                if "payment_plan" in student_data and pd.notna(student_data["payment_plan"]):
                    try:
                        payment_plan_index = payment_plan_options.index(int(student_data["payment_plan"]))
                    except (ValueError, TypeError):
                        # If value is not in list or is not an integer, default to 12 parcelas
                        payment_plan_index = 1
                
                payment_plan = st.selectbox(
                    "Plano de Pagamento",
                    payment_plan_options,
                    index=payment_plan_index,
                    help="Número de parcelas do curso"
                )
                
                notes = st.text_area("Observações", value=student_data.get("notes", ""))
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit_button = st.form_submit_button("Atualizar Dados")
            
            with col2:
                delete_button = st.form_submit_button("Excluir Aluno", use_container_width=True)
        
        if submit_button:
            # Update student data
            updated_student = {
                "phone": selected_phone,
                "name": name,
                "cpf": cpf,
                "course_type": course_type,
                "enrollment_date": enrollment_date.strftime("%Y-%m-%d"),
                "status": status,
                "monthly_fee": monthly_fee,
                "payment_plan": payment_plan,
                "notes": notes
            }
            
            if status == "canceled":
                updated_student["cancellation_date"] = cancellation_date.strftime("%Y-%m-%d")
                updated_student["cancellation_fee_paid"] = cancellation_fee_paid
            else:
                updated_student["cancellation_date"] = None
                updated_student["cancellation_fee_paid"] = False
            
            # Update dataframe
            students_df.loc[students_df["phone"] == selected_phone] = pd.Series(updated_student)
            
            # Save to CSV
            save_students_data(students_df)
            
            st.success(f"Dados do aluno {name} atualizados com sucesso!")
            st.rerun()
        
        if delete_button:
            # Confirm deletion
            delete_confirmed = st.checkbox("Confirmar exclusão (esta ação não pode ser desfeita!)")
            
            if delete_confirmed:
                # Remove student from dataframe
                students_df = students_df[students_df["phone"] != selected_phone]
                
                # Save to CSV
                save_students_data(students_df)
                
                # Option to delete related payments
                delete_payments = st.checkbox("Excluir também os pagamentos deste aluno?")
                
                if delete_payments and payments_df is not None and not payments_df.empty:
                    # Remove payments for this student
                    payments_df = payments_df[payments_df["phone"] != selected_phone]
                    
                    # Save to CSV
                    save_payments_data(payments_df)
                    
                    st.success(f"Aluno {student_data['name']} e seus pagamentos foram excluídos com sucesso!")
                else:
                    st.success(f"Aluno {student_data['name']} excluído com sucesso!")
                
                st.rerun()
    else:
        st.info("Não há alunos cadastrados.")
