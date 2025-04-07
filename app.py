import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar
from utils import (
    load_students_data, 
    load_payments_data, 
    load_internships_data,
    get_active_students,
    get_canceled_students,
    get_overdue_payments,
    calculate_monthly_revenue,
    format_currency
)
from login import verificar_autenticacao, mostrar_pagina_login, pagina_gerenciar_usuarios, logout
# Set page configuration
st.set_page_config(
    page_title="Sistema de Gestão - Pós-Graduação Libras",
    page_icon="📊",
    layout="wide"
)
# Create the data directory if it doesn't exist
os.makedirs("data", exist_ok=True)
# Create empty data files if they don't exist
if not os.path.exists("data/students.csv"):
    pd.DataFrame({
        "phone": [],
        "name": [],
        "email": [],
        "enrollment_date": [],
        "status": [],
        "cancellation_date": [],
        "cancellation_fee_paid": [],
        "monthly_fee": [],
        "notes": []
    }).to_csv("data/students.csv", index=False)
if not os.path.exists("data/payments.csv"):
    pd.DataFrame({
        "phone": [],
        "payment_date": [],
        "due_date": [],
        "amount": [],
        "month_reference": [],
        "year_reference": [],
        "status": [],
        "notes": []
    }).to_csv("data/payments.csv", index=False)
if not os.path.exists("data/internships.csv"):
    pd.DataFrame({
        "date": [],
        "topic": [],
        "duration_hours": [],
        "students": []
    }).to_csv("data/internships.csv", index=False)
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
# Verificar se o usuário está autenticado
if not verificar_autenticacao():
    mostrar_pagina_login()
else:
    # Menu de navegação com logout
    with st.sidebar:
        st.write(f"Usuário: {st.session_state['usuario_autenticado']['nome']}")
        
        if st.session_state['usuario_autenticado']['nivel'] == "admin":
            st.page_link("app.py", label="Dashboard", icon="📊")
            st.page_link("pages/alunos.py", label="Alunos", icon="👨‍🎓")
            st.page_link("pages/pagamentos.py", label="Pagamentos", icon="💰")
            st.page_link("pages/estagios.py", label="Estágios", icon="⏱️")
            st.page_link("pages/relatorios.py", label="Relatórios", icon="📈")
            
            # Opção de gerenciar usuários (apenas admin)
            if st.button("Gerenciar Usuários"):
                st.session_state["mostrar_gerenciamento_usuarios"] = True
            
            st.divider()
        else:
            st.page_link("app.py", label="Dashboard", icon="📊")
            st.page_link("pages/alunos.py", label="Alunos", icon="👨‍🎓")
            st.page_link("pages/pagamentos.py", label="Pagamentos", icon="💰")
            st.page_link("pages/estagios.py", label="Estágios", icon="⏱️")
            st.page_link("pages/relatorios.py", label="Relatórios", icon="📈")
            st.divider()
        
        # Opção para fazer backup dos dados
        st.subheader("Backup de Dados")
        
        if st.button("Baixar Backup Completo"):
            st.session_state["mostrar_backup"] = True
        
        st.divider()
        
        # Botão de logout
        if st.button("Sair"):
            logout()
            st.rerun()
    
    # Verificar se deve mostrar a página de gerenciamento de usuários
    if st.session_state.get("mostrar_gerenciamento_usuarios", False):
        pagina_gerenciar_usuarios()
        if st.button("Voltar ao Dashboard"):
            st.session_state["mostrar_gerenciamento_usuarios"] = False
            st.rerun()
    
    # Verificar se deve mostrar a página de backup
    elif st.session_state.get("mostrar_backup", False):
        st.subheader("Backup de Dados")
        
        st.write("""
        Aqui você pode baixar todos os dados do sistema em formato CSV para backup ou análise externa.
        """)
        
        col1, col2, col3 = st.columns(3)
        
        # Load data
        students_df = load_students_data()
        payments_df = load_payments_data()
        internships_df = load_internships_data()
        
        with col1:
            if students_df is not None and not students_df.empty:
                csv_students = students_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Baixar Dados de Alunos",
                    csv_students,
                    "alunos_backup.csv",
                    "text/csv",
                    key='download-students'
                )
            else:
                st.info("Não há dados de alunos para exportar.")
        
        with col2:
            if payments_df is not None and not payments_df.empty:
                csv_payments = payments_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Baixar Dados de Pagamentos",
                    csv_payments,
                    "pagamentos_backup.csv",
                    "text/csv",
                    key='download-payments'
                )
            else:
                st.info("Não há dados de pagamentos para exportar.")
        
        with col3:
            if internships_df is not None and not internships_df.empty:
                csv_internships = internships_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Baixar Dados de Estágios",
                    csv_internships,
                    "estagios_backup.csv",
                    "text/csv",
                    key='download-internships'
                )
            else:
                st.info("Não há dados de estágios para exportar.")
        
        # Opção de backup completo
        st.subheader("Backup Completo")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # TODO: Implementar zip de múltiplos arquivos quando necessário
        
        if st.button("Voltar ao Dashboard"):
            st.session_state["mostrar_backup"] = False
            st.rerun()
    
    else:
        # Main app title with logo
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image('assets/images/logo.svg', width=150)
        with col2:
            st.markdown('<div class="logo-text">Sistema de Gestão - Pós-Graduação Libras</div>', unsafe_allow_html=True)
        
        # Load data
        students_df = load_students_data()
        payments_df = load_payments_data()
        internships_df = load_internships_data()
        
        # Dashboard
        st.header("Dashboard")
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        # Get active and canceled students
        active_students = get_active_students(students_df)
        canceled_students = get_canceled_students(students_df)
        overdue_payments = get_overdue_payments(students_df, payments_df)
        # Calculate metrics
        total_students = len(students_df)
        active_count = len(active_students)
        canceled_count = len(canceled_students)
        overdue_count = len(overdue_payments)
        with col1:
            st.metric("Total de Alunos", total_students)
        with col2:
            st.metric("Alunos Ativos", active_count)
        with col3:
            st.metric("Alunos Cancelados", canceled_count)
        with col4:
            st.metric("Pagamentos Atrasados", overdue_count)
        # Financial projection
        st.subheader("Projeção Financeira Mensal")
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_revenue = calculate_monthly_revenue(students_df, payments_df, current_month, current_year)
        st.info(f"Receita projetada para {calendar.month_name[current_month]}/{current_year}: {format_currency(monthly_revenue)}")
        # Create two columns for the charts
        col1, col2 = st.columns(2)
        with col1:
            # Cancellation trend
            if not canceled_students.empty:
                # Convert cancellation dates to datetime
                canceled_students['cancellation_date'] = pd.to_datetime(canceled_students['cancellation_date'])
                
                # Group by month and count cancellations
                cancellations_by_month = canceled_students.groupby(
                    canceled_students['cancellation_date'].dt.strftime('%Y-%m')
                ).size().reset_index(name='count')
                cancellations_by_month.columns = ['Mês', 'Cancelamentos']
                
                # Create bar chart for cancellations
                if not cancellations_by_month.empty:
                    fig = px.bar(
                        cancellations_by_month, 
                        x='Mês', 
                        y='Cancelamentos',
                        title='Cancelamentos por Mês'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("Não há dados de cancelamento para exibir.")
            else:
                st.write("Não há dados de cancelamento para exibir.")
        with col2:
            # Payment status distribution
            if not payments_df.empty:
                payment_status = payments_df['status'].value_counts().reset_index()
                payment_status.columns = ['Status', 'Quantidade']
                
                # Map status to Portuguese
                status_map = {
                    'paid': 'Pago',
                    'pending': 'Pendente',
                    'overdue': 'Atrasado',
                    'canceled': 'Cancelado'
                }
                payment_status['Status'] = payment_status['Status'].map(status_map)
                
                fig = px.pie(
                    payment_status, 
                    names='Status', 
                    values='Quantidade',
                    title='Distribuição de Status de Pagamento',
                    color='Status',
                    color_discrete_map={
                        'Pago': 'green',
                        'Pendente': 'orange',
                        'Atrasado': 'red',
                        'Cancelado': 'gray'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("Não há dados de pagamento para exibir.")
        # Students with overdue payments
        st.subheader("Alunos com Pagamentos Atrasados")
        if not overdue_payments.empty:
            # Display only relevant columns
            display_columns = ['name', 'phone', 'email', 'monthly_fee', 'last_due_date', 'days_overdue']
            st.dataframe(overdue_payments[display_columns], use_container_width=True)
        else:
            st.success("Não há pagamentos atrasados no momento.")
        # Internship summary
        st.subheader("Resumo de Estágios")
        if not internships_df.empty:
            # Calculate total internship hours
            total_hours = internships_df['duration_hours'].sum()
            total_internships = len(internships_df)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total de Estágios", total_internships)
            
            with col2:
                st.metric("Total de Horas de Estágio", f"{total_hours:.1f}h")
            
            # Show recent internships
            st.write("Estágios Recentes:")
            
            # Convert date to datetime
            internships_df['date'] = pd.to_datetime(internships_df['date'])
            
            # Sort by date (most recent first) and show top 5
            recent_internships = internships_df.sort_values('date', ascending=False).head(5)
            
            # Format date for display
            recent_internships['date'] = recent_internships['date'].dt.strftime('%d/%m/%Y')
            
            st.dataframe(recent_internships[['date', 'topic', 'duration_hours']], use_container_width=True)
        else:
            st.info("Não há dados de estágio registrados ainda.")
        st.markdown("""
        ---
        ### Navegação
        Utilize o menu lateral para acessar as diferentes funcionalidades do sistema:
        - **Alunos**: Cadastro e gerenciamento de alunos
        - **Pagamentos**: Registro e controle de pagamentos
        - **Estágios**: Registro e acompanhamento de estágios
        - **Relatórios**: Relatórios detalhados e exportação de dados
        """)
