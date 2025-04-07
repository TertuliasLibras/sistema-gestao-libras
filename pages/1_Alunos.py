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
from login import verificar_autenticacao, mostrar_pagina_login

# Verificar autenticação
if not verificar_autenticacao():
    mostrar_pagina_login()
    st.stop()  # Parar a execução do restante da página

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
        from config import get_logo_path
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
                                      options=["Pós-Graduação", "Aperfeiçoamento Profissional"],
                                      help="Selecione o tipo de curso")
            source = st.selectbox("Origem do Cadastro",
                                 options=["Evento online", "Venda direta WhatsApp", "Indicação"],
                                 help="Selecione como o aluno conheceu o curso")
        
        with col2:
            enrollment_date = st.date_input("Data de Matrícula", datetime.now())
            monthly_fee = st.number_input("Mensalidade (R$)", min_value=0.0, value=300.0, step=10.0)
            payment_plan = st.number_input("Quantidade de Parcelas", min_value=1, value=12, step=1, 
                                         help="Número total de parcelas do plano de pagamento")
            due_day = st.number_input("Dia de Vencimento", min_value=1, max_value=28, value=10, step=1,
                                     help="Dia do mês para vencimento das parcelas")
            notes = st.text_area("Observações", height=80)
        
        submitted = st.form_submit_button("Cadastrar Aluno")
        
        if submitted:
            if not phone or not name:
                st.error("Telefone e nome são campos obrigatórios!")
            elif not validate_phone(phone):
                st.error("Formato de telefone inválido!")
            elif students_df is not None and not students_df.empty and phone in students_df['phone'].values:
                st.error(f"Aluno com telefone {phone} já está cadastrado!")
            else:
                # Create new student record
                new_student = {
                    'phone': phone,
                    'name': name,
                    'cpf': cpf,
                    'enrollment_date': enrollment_date.strftime('%Y-%m-%d'),
                    'status': 'active',
                    'cancellation_date': None,
                    'cancellation_fee_paid': None,
                    'monthly_fee': monthly_fee,
                    'course_type': course_type,
                    'payment_plan': payment_plan,
                    'due_day': due_day,
                    'source': source,
                    'notes': notes
                }
                
                # Add to dataframe
                if students_df is None or students_df.empty:
                    students_df = pd.DataFrame([new_student])
                else:
                    students_df = pd.concat([students_df, pd.DataFrame([new_student])], ignore_index=True)
                
                # Generate payment records
                payment_records = generate_monthly_payments(
                    phone,
                    monthly_fee,
                    enrollment_date,
                    payment_plan,
                    None,  # end_date
                    due_day
                )
                                # Add payment records to dataframe
                if payments_df is None or payments_df.empty:
                    payments_df = pd.DataFrame(payment_records)
                else:
                    payments_df = pd.concat([payments_df, pd.DataFrame(payment_records)], ignore_index=True)
                
                # Save data
                save_students_data(students_df)
                save_payments_data(payments_df)
                
                st.success(f"Aluno {name} cadastrado com sucesso!")

with tab2:
    st.subheader("Lista de Alunos")
    
    # Filter options
    st.write("Filtros:")
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.multiselect(
            "Status", 
            options=["Todos", "Ativos", "Cancelados"],
            default=["Todos"]
        )
    
    with col2:
        search_term = st.text_input("Buscar por nome ou telefone")
    
    if students_df is not None and not students_df.empty:
        # Apply filters
        filtered_df = students_df.copy()
        
        # Status filter
        if "Todos" not in status_filter:
            if "Ativos" in status_filter and "Cancelados" in status_filter:
                pass  # Show all statuses
            elif "Ativos" in status_filter:
                filtered_df = filtered_df[filtered_df['status'] == 'active']
            elif "Cancelados" in status_filter:
                filtered_df = filtered_df[filtered_df['status'] == 'canceled']
        
        # Search filter
        if search_term:
            search_term = search_term.lower()
            filtered_df = filtered_df[
                filtered_df['name'].str.lower().str.contains(search_term, na=False) |
                filtered_df['phone'].str.lower().str.contains(search_term, na=False)
            ]
        
        # Display dataframe
        if not filtered_df.empty:
            # Create a copy with formatted data for display
            display_df = filtered_df.copy()
            
            # Format phone numbers
            display_df['phone'] = display_df['phone'].apply(format_phone)
            
            # Format status
            display_df['status'] = display_df['status'].map({
                'active': 'Ativo',
                'canceled': 'Cancelado'
            })
            
            # Format monthly fee
            display_df['monthly_fee'] = display_df['monthly_fee'].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
            
            # Check which columns are available in the dataframe
            available_columns = []
            column_config = {}
            
            # Always include these basic columns
            if 'phone' in display_df.columns:
                available_columns.append('phone')
                column_config['phone'] = 'Telefone'
                
            if 'name' in display_df.columns:
                available_columns.append('name')
                column_config['name'] = 'Nome'
            
            # Check for new columns (might not exist in older data)
            if 'cpf' in display_df.columns:
                available_columns.append('cpf')
                column_config['cpf'] = 'CPF'
            elif 'email' in display_df.columns:  # Backward compatibility
                available_columns.append('email')
                column_config['email'] = 'Email'
                
            if 'course_type' in display_df.columns:
                available_columns.append('course_type')
                column_config['course_type'] = 'Tipo de Curso'
                
            if 'enrollment_date' in display_df.columns:
                available_columns.append('enrollment_date')
                column_config['enrollment_date'] = 'Data de Matrícula'
                
            if 'status' in display_df.columns:
                available_columns.append('status')
                column_config['status'] = 'Status'
                
            if 'monthly_fee' in display_df.columns:
                available_columns.append('monthly_fee')
                column_config['monthly_fee'] = 'Mensalidade'
                
            if 'payment_plan' in display_df.columns:
                available_columns.append('payment_plan')
                column_config['payment_plan'] = 'Parcelas'
                
            if 'due_day' in display_df.columns:
                available_columns.append('due_day')
                column_config['due_day'] = 'Dia de Vencimento'
                
            if 'source' in display_df.columns:
                available_columns.append('source')
                column_config['source'] = 'Origem do Cadastro'
            
            # Display only relevant columns that exist
            st.dataframe(
                display_df[available_columns],
                use_container_width=True,
                column_config=column_config
            )
            
            st.info(f"Total de alunos: {len(filtered_df)}")
            
            # Export option
            if st.button("Exportar Lista (CSV)"):
                export_df = filtered_df.copy()
                # Convert to CSV
                csv = export_df.to_csv(index=False).encode('utf-8')
                
                # Create download button
                st.download_button(
                    "Baixar CSV",
                    csv,
                    "alunos.csv",
                    "text/csv",
                    key='download-csv'
                )
        else:
            st.warning("Nenhum aluno encontrado com os filtros selecionados.")
    else:
        st.info("Não há alunos cadastrados ainda.")
        with tab3:
    st.subheader("Editar ou Excluir Aluno")
    
    if students_df is not None and not students_df.empty:
        # Select student to edit
        selected_phone = st.selectbox(
            "Selecione o aluno pelo telefone:",
            options=students_df['phone'].tolist(),
            format_func=lambda x: f"{format_phone(x)} - {students_df[students_df['phone'] == x]['name'].values[0]}"
        )
        
        if selected_phone:
            # Get selected student data
            student = students_df[students_df['phone'] == selected_phone].iloc[0]
            
            # Create edit form
            with st.form("edit_student_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Nome Completo", value=student['name'])
                    cpf = st.text_input("CPF", value=student['cpf'] if 'cpf' in student else "")
                    phone = st.text_input("Telefone/WhatsApp", value=student['phone'], disabled=True,
                                         help="O telefone não pode ser alterado pois é o identificador do aluno")
                    
                    course_type = st.selectbox(
                        "Tipo de Curso",
                        options=["Pós-Graduação", "Aperfeiçoamento Profissional"],
                        index=0 if 'course_type' not in student or student['course_type'] == "Pós-Graduação" else 1
                    )
                    
                    source = st.selectbox(
                        "Origem do Cadastro",
                        options=["Evento online", "Venda direta WhatsApp", "Indicação"],
                        index=0 if 'source' not in student else 
                              (0 if student['source'] == "Evento online" else 
                               1 if student['source'] == "Venda direta WhatsApp" else 2)
                    )
                
                with col2:
                    enrollment_date = st.date_input(
                        "Data de Matrícula", 
                        pd.to_datetime(student['enrollment_date']).date() if pd.notna(student['enrollment_date']) else datetime.now()
                    )
                    
                    monthly_fee = st.number_input(
                        "Mensalidade (R$)", 
                        min_value=0.0, 
                        value=float(student['monthly_fee']), 
                        step=10.0
                    )
                    
                    payment_plan = st.number_input(
                        "Quantidade de Parcelas", 
                        min_value=1, 
                        value=int(student['payment_plan']) if 'payment_plan' in student else 12, 
                        step=1
                    )
                    
                    due_day = st.number_input(
                        "Dia de Vencimento", 
                        min_value=1, 
                        max_value=28, 
                        value=int(student['due_day']) if 'due_day' in student else 10, 
                        step=1
                    )
                    
                    status = st.selectbox(
                        "Status",
                        options=['active', 'canceled'],
                        format_func=lambda x: 'Ativo' if x == 'active' else 'Cancelado',
                        index=0 if student['status'] == 'active' else 1
                    )
                    
                    cancellation_date = None
                    cancellation_fee_paid = None
                    
                    if status == 'canceled':
                        cancellation_date = st.date_input(
                            "Data de Cancelamento",
                            pd.to_datetime(student['cancellation_date']).date() if pd.notna(student['cancellation_date']) else datetime.now()
                        )
                        
                        cancellation_fee_paid = st.selectbox(
                            "Multa de Cancelamento Paga?",
                            options=[True, False],
                            format_func=lambda x: 'Sim' if x else 'Não',
                            index=0 if student['cancellation_fee_paid'] == True else 1
                        )
                
                notes = st.text_area("Observações", value=student['notes'] if pd.notna(student['notes']) else "", height=100)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    update_button = st.form_submit_button("Atualizar Dados")
                
                with col2:
                    delete_button = st.form_submit_button("Excluir Aluno", type="primary", use_container_width=True)
                
                if update_button:
                    # Update student record
                    students_df.loc[students_df['phone'] == selected_phone, 'name'] = name
                    
                    # Ensure required columns exist
                    for column in ['cpf', 'course_type', 'payment_plan', 'due_day', 'source']:
                        if column not in students_df.columns:
                            students_df[column] = None
                    
                    students_df.loc[students_df['phone'] == selected_phone, 'cpf'] = cpf
                    students_df.loc[students_df['phone'] == selected_phone, 'course_type'] = course_type
                    students_df.loc[students_df['phone'] == selected_phone, 'payment_plan'] = payment_plan
                    students_df.loc[students_df['phone'] == selected_phone, 'enrollment_date'] = enrollment_date.strftime('%Y-%m-%d')
                    students_df.loc[students_df['phone'] == selected_phone, 'monthly_fee'] = monthly_fee
                    students_df.loc[students_df['phone'] == selected_phone, 'status'] = status
                    students_df.loc[students_df['phone'] == selected_phone, 'notes'] = notes
                    students_df.loc[students_df['phone'] == selected_phone, 'due_day'] = due_day
                    students_df.loc[students_df['phone'] == selected_phone, 'source'] = source
                    
                    if status == 'canceled':
                        students_df.loc[students_df['phone'] == selected_phone, 'cancellation_date'] = cancellation_date.strftime('%Y-%m-%d')
                        students_df.loc[students_df['phone'] == selected_phone, 'cancellation_fee_paid'] = cancellation_fee_paid
                    
                    # Save data
                    save_students_data(students_df)
                    
                    # Update monthly fee in pending payments if it changed
                    if monthly_fee != student['monthly_fee'] and not payments_df.empty:
                        pending_payments = payments_df[
                            (payments_df['phone'] == selected_phone) & 
                            (payments_df['status'] == 'pending')
                        ]
                        
                        if not pending_payments.empty:
                            payments_df.loc[
                                (payments_df['phone'] == selected_phone) & 
                                (payments_df['status'] == 'pending'),
                                'amount'
                            ] = monthly_fee
                            
                            save_payments_data(payments_df)
                    
                    st.success("Dados do aluno atualizados com sucesso!")
                    st.rerun()
                
                if delete_button:
                    # Confirm deletion
                    if st.warning("Tem certeza que deseja excluir este aluno? Esta ação não pode ser desfeita."):
                        # Remove student from dataframe
                        students_df = students_df[students_df['phone'] != selected_phone]
                        
                        # Remove associated payments
                        if not payments_df.empty:
                            payments_df = payments_df[payments_df['phone'] != selected_phone]
                        
                        # Save data
                        save_students_data(students_df)
                        save_payments_data(payments_df)
                        
                        st.success("Aluno excluído com sucesso!")
                        st.rerun()
    else:
        st.info("Não há alunos cadastrados ainda.")
