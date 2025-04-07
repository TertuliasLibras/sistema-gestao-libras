import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from utils import (
    load_students_data, 
    save_students_data,
    load_payments_data,
    save_payments_data,
    format_phone,
    validate_phone,
    generate_monthly_payments,
    get_student_internship_hours,
    load_internships_data
)
from login import verificar_autenticacao

# Check authentication
if not verificar_autenticacao():
    st.error("Você precisa fazer login para acessar esta página.")
    st.stop()

# Set page config
st.set_page_config(
    page_title="Alunos - Sistema de Gestão",
    page_icon="👨‍🎓",
    layout="wide"
)

# Display logo and title
col1, col2 = st.columns([1, 3])
with col1:
    st.image('assets/images/logo.svg', width=100)
with col2:
    st.title("Gestão de Alunos")

# Load data
students_df = load_students_data()
payments_df = load_payments_data()
internships_df = load_internships_data()

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Cadastrar Aluno", "Visualizar Alunos", "Análise de Alunos"])

with tab1:
    st.subheader("Cadastrar Novo Aluno")
    
    # Form for adding new student
    with st.form("student_form"):
        # Basic info
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
        with col2:
            phone = st.text_input("Telefone (DDD + número)")
            monthly_fee = st.number_input("Mensalidade (R$)", min_value=0.0, format="%.2f")
        
        # Enrollment info
        col1, col2 = st.columns(2)
        with col1:
            enrollment_date = st.date_input("Data de Matrícula", datetime.now())
        
        # Notes
        notes = st.text_area("Observações")
        
        # Submit button
        submit = st.form_submit_button("Cadastrar Aluno")
        
        if submit:
            # Validate inputs
            if not name or not email or not phone:
                st.error("Nome, e-mail e telefone são campos obrigatórios.")
            elif not validate_phone(phone):
                st.error("Formato de telefone inválido. Use o formato (DDD) 9XXXX-XXXX ou (DDD) XXXX-XXXX.")
            else:
                # Format phone number
                phone_clean = "".join(filter(str.isdigit, phone))
                
                # Check if phone already exists
                if not students_df.empty and phone_clean in students_df['phone'].values:
                    st.error(f"Já existe um aluno cadastrado com o telefone {phone}.")
                else:
                    # Create new student record
                    new_student = {
                        'phone': phone_clean,
                        'name': name,
                        'email': email,
                        'enrollment_date': enrollment_date,
                        'status': 'active',
                        'cancellation_date': None,
                        'cancellation_fee_paid': False,
                        'monthly_fee': monthly_fee,
                        'notes': notes
                    }
                    
                    # Add to dataframe
                    if students_df.empty:
                        students_df = pd.DataFrame([new_student])
                    else:
                        students_df = pd.concat([students_df, pd.DataFrame([new_student])], ignore_index=True)
                    
                    # Save data
                    if save_students_data(students_df):
                        st.success(f"Aluno {name} cadastrado com sucesso!")
                        
                        # Generate monthly payments for the new student
                        payment_records = generate_monthly_payments(
                            phone_clean, monthly_fee, enrollment_date
                        )
                        
                        if payment_records:
                            # Add to payments dataframe
                            new_payments_df = pd.DataFrame(payment_records)
                            
                            if payments_df.empty:
                                payments_df = new_payments_df
                            else:
                                payments_df = pd.concat([payments_df, new_payments_df], ignore_index=True)
                            
                            # Save payments data
                            save_payments_data(payments_df)
                            
                            st.info(f"Foram gerados {len(payment_records)} registros de pagamento para este aluno.")
                    else:
                        st.error("Erro ao salvar dados do aluno.")

with tab2:
    st.subheader("Alunos Cadastrados")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Status",
            ["Todos", "Ativos", "Cancelados"],
            index=1  # Default to Active
        )
    
    # Apply filters
    filtered_df = students_df.copy()
    
    if status_filter == "Ativos":
        filtered_df = filtered_df[filtered_df['status'] == 'active']
    elif status_filter == "Cancelados":
        filtered_df = filtered_df[filtered_df['status'] == 'canceled']
    
    # Display student data
    if not filtered_df.empty:
        # Format phone numbers for display
        filtered_df['telefone_formatado'] = filtered_df['phone'].apply(format_phone)
        
        # Convert enrollment date to string for display
        filtered_df['data_matricula'] = pd.to_datetime(filtered_df['enrollment_date']).dt.strftime('%d/%m/%Y')
        
        # Map status to Portuguese
        status_map = {'active': 'Ativo', 'canceled': 'Cancelado'}
        filtered_df['status_pt'] = filtered_df['status'].map(status_map)
        
        # Reorder and select columns for display
        display_df = filtered_df[['name', 'telefone_formatado', 'email', 'data_matricula', 'status_pt', 'monthly_fee']]
        display_df.columns = ['Nome', 'Telefone', 'Email', 'Data de Matrícula', 'Status', 'Mensalidade (R$)']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Student selection for details
        st.subheader("Detalhes do Aluno")
        
        selected_phone = st.selectbox(
            "Selecione um aluno para ver detalhes",
            filtered_df['phone'].tolist(),
            format_func=lambda x: filtered_df[filtered_df['phone'] == x]['name'].iloc[0]
        )
        
        if selected_phone:
            # Get selected student
            student = filtered_df[filtered_df['phone'] == selected_phone].iloc[0]
            
            # Display student details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Nome:** {student['name']}")
                st.markdown(f"**Telefone:** {format_phone(student['phone'])}")
                st.markdown(f"**Email:** {student['email']}")
                st.markdown(f"**Data de Matrícula:** {student['data_matricula']}")
            
            with col2:
                st.markdown(f"**Status:** {student['status_pt']}")
                st.markdown(f"**Mensalidade:** R$ {student['monthly_fee']:.2f}")
                
                # Display cancellation date if canceled
                if student['status'] == 'canceled':
                    cancellation_date = pd.to_datetime(student['cancellation_date']).strftime('%d/%m/%Y')
                    st.markdown(f"**Data de Cancelamento:** {cancellation_date}")
                    
                    cancellation_fee_paid = "Sim" if student['cancellation_fee_paid'] else "Não"
                    st.markdown(f"**Multa Paga:** {cancellation_fee_paid}")
            
            # Display internship hours
            internship_hours = get_student_internship_hours(internships_df, selected_phone)
            st.markdown(f"**Total de Horas de Estágio:** {internship_hours:.1f}h")
            
            # Display notes
            if pd.notna(student['notes']) and student['notes']:
                st.subheader("Observações")
                st.write(student['notes'])
            
            # Edit/Cancel options
            st.subheader("Editar Aluno")
            
            # Create tabs for edit and cancel
            edit_tab, cancel_tab = st.tabs(["Atualizar Dados", "Cancelar Matrícula"])
            
            with edit_tab:
                with st.form("edit_student_form"):
                    # Basic info
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("Nome Completo", value=student['name'])
                        edit_email = st.text_input("E-mail", value=student['email'])
                    with col2:
                        edit_phone_display = st.text_input("Telefone", value=format_phone(student['phone']), disabled=True)
                        edit_monthly_fee = st.number_input("Mensalidade (R$)", value=float(student['monthly_fee']), min_value=0.0, format="%.2f")
                    
                    # Notes
                    edit_notes = st.text_area("Observações", value=student['notes'] if pd.notna(student['notes']) else "")
                    
                    # Submit button
                    edit_submit = st.form_submit_button("Atualizar Dados")
                    
                    if edit_submit:
                        # Update student record
                        students_df.loc[students_df['phone'] == selected_phone, 'name'] = edit_name
                        students_df.loc[students_df['phone'] == selected_phone, 'email'] = edit_email
                        students_df.loc[students_df['phone'] == selected_phone, 'monthly_fee'] = edit_monthly_fee
                        students_df.loc[students_df['phone'] == selected_phone, 'notes'] = edit_notes
                        
                        # Save data
                        if save_students_data(students_df):
                            st.success("Dados do aluno atualizados com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar dados do aluno.")
            
            with cancel_tab:
                # Only show cancel options for active students
                if student['status'] == 'active':
                    with st.form("cancel_student_form"):
                        cancellation_date = st.date_input("Data de Cancelamento", datetime.now())
                        cancellation_fee_paid = st.checkbox("Multa de Cancelamento Paga")
                        
                        cancel_notes = st.text_area("Motivo do Cancelamento")
                        
                        cancel_submit = st.form_submit_button("Confirmar Cancelamento")
                        
                        if cancel_submit:
                            # Confirm cancellation
                            confirm = st.warning("Tem certeza que deseja cancelar a matrícula deste aluno?")
                            
                            # Update student record
                            students_df.loc[students_df['phone'] == selected_phone, 'status'] = 'canceled'
                            students_df.loc[students_df['phone'] == selected_phone, 'cancellation_date'] = cancellation_date
                            students_df.loc[students_df['phone'] == selected_phone, 'cancellation_fee_paid'] = cancellation_fee_paid
                            
                            # Append cancellation notes to existing notes
                            current_notes = student['notes'] if pd.notna(student['notes']) else ""
                            new_notes = f"{current_notes}\n\nCANCELAMENTO ({cancellation_date.strftime('%d/%m/%Y')}):\n{cancel_notes}"
                            students_df.loc[students_df['phone'] == selected_phone, 'notes'] = new_notes
                            
                            # Save data
                            if save_students_data(students_df):
                                st.success("Matrícula do aluno cancelada com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao cancelar matrícula do aluno.")
                else:
                    st.info("Este aluno já está com a matrícula cancelada.")
                    
                    # Option to reactivate
                    if st.button("Reativar Matrícula"):
                        # Update student record
                        students_df.loc[students_df['phone'] == selected_phone, 'status'] = 'active'
                        students_df.loc[students_df['phone'] == selected_phone, 'cancellation_date'] = None
                        students_df.loc[students_df['phone'] == selected_phone, 'cancellation_fee_paid'] = False
                        
                        # Save data
                        if save_students_data(students_df):
                            st.success("Matrícula do aluno reativada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao reativar matrícula do aluno.")
    else:
        st.info("Não há alunos cadastrados.")

with tab3:
    st.subheader("Análise de Alunos")
    
    if not students_df.empty:
        # Count students by status
        status_counts = students_df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Quantidade']
        
        # Map status to Portuguese
        status_map = {'active': 'Ativo', 'canceled': 'Cancelado'}
        status_counts['Status'] = status_counts['Status'].map(status_map)
        
        # Display pie chart
        fig = px.pie(
            status_counts, 
            names='Status', 
            values='Quantidade',
            title='Distribuição de Alunos por Status',
            color='Status',
            color_discrete_map={'Ativo': 'green', 'Cancelado': 'red'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly enrollments
        st.subheader("Matrículas por Mês")
        
        # Convert enrollment date to datetime
        students_df['enrollment_date'] = pd.to_datetime(students_df['enrollment_date'])
        
        # Group by month and count enrollments
        enrollments_by_month = students_df.groupby(
            students_df['enrollment_date'].dt.strftime('%Y-%m')
        ).size().reset_index(name='count')
        enrollments_by_month.columns = ['Mês', 'Novas Matrículas']
        
        # Create bar chart for enrollments
        if not enrollments_by_month.empty:
            fig = px.bar(
                enrollments_by_month, 
                x='Mês', 
                y='Novas Matrículas',
                title='Novas Matrículas por Mês',
                color_discrete_sequence=['#1E88E5']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Não há dados de matrícula para exibir.")
            
        # If there are canceled students, show cancellation reasons
        canceled_df = students_df[students_df['status'] == 'canceled']
        if not canceled_df.empty:
            st.subheader("Motivos de Cancelamento")
            
            # Extract cancellation notes
            cancellation_notes = []
            for _, student in canceled_df.iterrows():
                notes = student['notes'] if pd.notna(student['notes']) else ""
                if "CANCELAMENTO" in notes:
                    cancellation_notes.append({
                        'name': student['name'],
                        'date': pd.to_datetime(student['cancellation_date']).strftime('%d/%m/%Y'),
                        'notes': notes.split("CANCELAMENTO")[1]
                    })
            
            if cancellation_notes:
                for note in cancellation_notes:
                    with st.expander(f"{note['name']} - {note['date']}"):
                        st.write(note['notes'])
            else:
                st.info("Não há motivos de cancelamento registrados.")
    else:
        st.info("Não há dados de alunos para análise.")
