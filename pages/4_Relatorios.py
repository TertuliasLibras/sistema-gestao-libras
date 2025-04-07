from login import verificar_autenticacao, mostrar_pagina_login

# Verificar autenticação
if not verificar_autenticacao():
    mostrar_pagina_login()
    st.stop()  # Parar a execução do restante da página
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar
from utils import (
    load_students_data, 
    load_payments_data,
    load_internships_data,
    format_phone,
    format_currency,
    get_active_students,
    get_canceled_students,
    get_student_internship_hours,
    get_student_internship_topics
)
from config import get_logo_path

st.set_page_config(
    page_title="Relatórios - Sistema de Gestão Libras",
    page_icon="📊",
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
    st.title("Relatórios")

# Load data
students_df = load_students_data()
payments_df = load_payments_data()
internships_df = load_internships_data()

# Create tabs for different reports
tab1, tab2, tab3, tab4 = st.tabs(["Financeiro", "Alunos", "Estágios", "Exportar Dados"])

with tab1:
    st.subheader("Relatório Financeiro")
    
    if payments_df is not None and not payments_df.empty:
        # Date range filter
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Data inicial",
                value=datetime.now().replace(day=1, month=1),
                key="finance_start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "Data final",
                value=datetime.now(),
                key="finance_end_date"
            )
        
        # Filter by date range
        payments_df["due_date"] = pd.to_datetime(payments_df["due_date"], errors='coerce')
        filtered_payments = payments_df[
            (payments_df["due_date"] >= pd.Timestamp(start_date)) & 
            (payments_df["due_date"] <= pd.Timestamp(end_date))
        ]
        
        if not filtered_payments.empty:
            # Monthly revenue chart
            st.subheader("Receita Mensal")
            
            # Prepare data for chart
            filtered_payments["month_year"] = filtered_payments["due_date"].dt.strftime('%Y-%m')
            
            # Group by month and sum amounts
            monthly_revenue = filtered_payments.groupby("month_year").agg(
                total_amount=("amount", "sum"),
                paid_amount=("amount", lambda x: filtered_payments.loc[filtered_payments["status"] == "paid", "amount"].sum())
            ).reset_index()
            
            # Create chart
            fig = px.bar(
                monthly_revenue,
                x="month_year",
                y=["total_amount", "paid_amount"],
                title="Receita Mensal",
                labels={
                    "month_year": "Mês",
                    "value": "Valor (R$)",
                    "variable": "Tipo"
                },
                color_discrete_map={
                    "total_amount": "blue",
                    "paid_amount": "green"
                }
            )
            
            # Update legend names
            fig.for_each_trace(lambda t: t.update(name = {
                "total_amount": "Total",
                "paid_amount": "Pago"
            }[t.name]))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Payment status breakdown
            st.subheader("Status de Pagamentos")
            
            # Group by status
            status_counts = filtered_payments["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            
            # Map status to Portuguese
            status_map = {
                "paid": "Pago",
                "pending": "Pendente",
                "overdue": "Atrasado",
                "canceled": "Cancelado"
            }
            status_counts["status"] = status_counts["status"].map(status_map)
            
            # Create pie chart
            fig = px.pie(
                status_counts,
                values="count",
                names="status",
                title="Distribuição de Status de Pagamento",
                color="status",
                color_discrete_map={
                    "Pago": "green",
                    "Pendente": "blue",
                    "Atrasado": "red",
                    "Cancelado": "gray"
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary metrics
            st.subheader("Resumo Financeiro")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_revenue = filtered_payments["amount"].sum()
            paid_revenue = filtered_payments[filtered_payments["status"] == "paid"]["amount"].sum()
            pending_revenue = filtered_payments[filtered_payments["status"] == "pending"]["amount"].sum()
            overdue_revenue = filtered_payments[filtered_payments["status"] == "overdue"]["amount"].sum()
            
            with col1:
                st.metric("Receita Total", format_currency(total_revenue))
            
            with col2:
                st.metric("Receita Recebida", format_currency(paid_revenue))
            
            with col3:
                st.metric("Receita Pendente", format_currency(pending_revenue))
            
            with col4:
                st.metric("Receita Atrasada", format_currency(overdue_revenue))
            
            # Detailed table
            st.subheader("Detalhamento por Mês")
            
            # Group by month/year
            monthly_detail = filtered_payments.groupby(["month_reference", "year_reference"]).agg(
                total=("amount", "sum"),
                paid=("amount", lambda x: filtered_payments.loc[filtered_payments["status"] == "paid", "amount"].sum()),
                pending=("amount", lambda x: filtered_payments.loc[filtered_payments["status"] == "pending", "amount"].sum()),
                overdue=("amount", lambda x: filtered_payments.loc[filtered_payments["status"] == "overdue", "amount"].sum()),
                count=("amount", "count")
            ).reset_index()
            
            # Add month name
            monthly_detail["month_name"] = monthly_detail["month_reference"].apply(
                lambda x: calendar.month_name[x] if pd.notna(x) and 1 <= x <= 12 else ""
            )
            
            # Format currency
            for col in ["total", "paid", "pending", "overdue"]:
                monthly_detail[col] = monthly_detail[col].apply(format_currency)
            
            # Select columns for display
            display_columns = ["month_name", "year_reference", "total", "paid", "pending", "overdue", "count"]
            display_df = monthly_detail[display_columns].copy()
            
            # Rename columns
            display_df.columns = ["Mês", "Ano", "Total", "Pago", "Pendente", "Atrasado", "Qtd. Pagamentos"]
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("Não há dados de pagamento para o período selecionado.")
    else:
        st.info("Não há dados de pagamento para gerar o relatório.")

with tab2:
    st.subheader("Relatório de Alunos")
    
    if students_df is not None and not students_df.empty:
        # Status breakdown
        st.subheader("Status dos Alunos")
        
        # Count active and canceled students
        active_count = len(get_active_students(students_df))
        canceled_count = len(get_canceled_students(students_df))
        
        # Create data for chart
        status_data = pd.DataFrame({
            "Status": ["Ativo", "Cancelado"],
            "Quantidade": [active_count, canceled_count]
        })
        
        # Create pie chart
        fig = px.pie(
            status_data,
            values="Quantidade",
            names="Status",
            title="Distribuição de Status dos Alunos",
            color="Status",
            color_discrete_map={
                "Ativo": "green",
                "Cancelado": "red"
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Enrollment trend
        st.subheader("Tendência de Matrículas")
        
        # Convert enrollment dates to datetime
        students_df["enrollment_date"] = pd.to_datetime(students_df["enrollment_date"], errors='coerce')
        
        # Group by month
        students_df["enrollment_month"] = students_df["enrollment_date"].dt.strftime('%Y-%m')
        enrollments_by_month = students_df["enrollment_month"].value_counts().reset_index()
        enrollments_by_month.columns = ["Mês", "Quantidade"]
        enrollments_by_month = enrollments_by_month.sort_values("Mês")
        
        # Create bar chart
        fig = px.bar(
            enrollments_by_month,
            x="Mês",
            y="Quantidade",
            title="Matrículas por Mês"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Cancellation trend (if any)
        canceled_students = get_canceled_students(students_df)
        
        if not canceled_students.empty:
            st.subheader("Tendência de Cancelamentos")
            
            # Convert cancellation dates to datetime
            canceled_students["cancellation_date"] = pd.to_datetime(canceled_students["cancellation_date"], errors='coerce')
            
            # Group by month
            canceled_students["cancellation_month"] = canceled_students["cancellation_date"].dt.strftime('%Y-%m')
            cancellations_by_month = canceled_students["cancellation_month"].value_counts().reset_index()
            cancellations_by_month.columns = ["Mês", "Quantidade"]
            cancellations_by_month = cancellations_by_month.sort_values("Mês")
            
            # Create bar chart
            fig = px.bar(
                cancellations_by_month,
                x="Mês",
                y="Quantidade",
                title="Cancelamentos por Mês",
                color_discrete_sequence=["red"]
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Course type breakdown (if available)
        if 'course_type' in students_df.columns:
            st.subheader("Tipos de Curso")
            
            # Count by course type
            course_counts = students_df["course_type"].value_counts().reset_index()
            course_counts.columns = ["Tipo de Curso", "Quantidade"]
            
            # Create pie chart
            fig = px.pie(
                course_counts,
                values="Quantidade",
                names="Tipo de Curso",
                title="Distribuição por Tipo de Curso"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Summary metrics
        st.subheader("Resumo de Alunos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Alunos", len(students_df))
        
        with col2:
            st.metric("Alunos Ativos", active_count)
        
        with col3:
            st.metric("Alunos Cancelados", canceled_count)
    else:
        st.info("Não há dados de alunos para gerar o relatório.")

with tab3:
    st.subheader("Relatório de Estágios")
    
    if internships_df is not None and not internships_df.empty and students_df is not None and not students_df.empty:
        # Total internship hours by month
        st.subheader("Horas de Estágio por Mês")
        
        # Convert dates to datetime
        internships_df["date"] = pd.to_datetime(internships_df["date"], errors='coerce')
        
        # Group by month
        internships_df["month"] = internships_df["date"].dt.strftime('%Y-%m')
        hours_by_month = internships_df.groupby("month")["duration_hours"].sum().reset_index()
        hours_by_month.columns = ["Mês", "Horas"]
        hours_by_month = hours_by_month.sort_values("Mês")
        
        # Create bar chart
        fig = px.bar(
            hours_by_month,
            x="Mês",
            y="Horas",
            title="Horas de Estágio por Mês"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Student participation
        st.subheader("Participação dos Alunos")
        
        # Count internships for each student
        active_students = get_active_students(students_df)
        
        if not active_students.empty:
            student_hours = []
            
            for _, student in active_students.iterrows():
                phone = student["phone"]
                name = student["name"]
                total_hours = get_student_internship_hours(internships_df, phone)
                
                student_hours.append({
                    "Nome": name,
                    "Telefone": phone,
                    "Total de Horas": total_hours
                })
            
            # Convert to dataframe
            student_hours_df = pd.DataFrame(student_hours)
            
            # Create bar chart
            if not student_hours_df.empty:
                # Sort by hours (descending)
                student_hours_df = student_hours_df.sort_values("Total de Horas", ascending=False)
                
                fig = px.bar(
                    student_hours_df,
                    x="Nome",
                    y="Total de Horas",
                    title="Horas de Estágio por Aluno",
                    hover_data=["Telefone"]
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Top 5 students
                st.subheader("Top 5 Alunos com Mais Horas de Estágio")
                
                top_students = student_hours_df.head(5).copy()
                top_students["Total de Horas"] = top_students["Total de Horas"].apply(lambda x: f"{x:.1f}h")
                
                st.table(top_students)
        
        # Topic distribution
        st.subheader("Distribuição de Temas de Estágio")
        
        # Count internships by topic
        topic_counts = internships_df["topic"].value_counts().reset_index()
        topic_counts.columns = ["Tema", "Quantidade"]
        
        # Limit to top 10 topics for readability
        top_topics = topic_counts.head(10)
        
        # Create bar chart
        fig = px.bar(
            top_topics,
            x="Tema",
            y="Quantidade",
            title="Top 10 Temas de Estágio"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary metrics
        st.subheader("Resumo de Estágios")
        
        col1, col2, col3 = st.columns(3)
        
        total_internships = len(internships_df)
        total_hours = internships_df["duration_hours"].sum()
        
        with col1:
            st.metric("Total de Estágios", total_internships)
        
        with col2:
            st.metric("Total de Horas", f"{total_hours:.1f}h")
        
        with col3:
            active_count = len(active_students)
            if active_count > 0:
                avg_hours = total_hours / active_count
                st.metric("Média de Horas por Aluno", f"{avg_hours:.1f}h")
            else:
                st.metric("Média de Horas por Aluno", "N/A")
    else:
        st.info("Não há dados de estágio para gerar o relatório.")

with tab4:
    st.subheader("Exportar Dados")
    
    st.write("""
    Aqui você pode exportar todos os dados do sistema em formato CSV para backup ou análise externa.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if students_df is not None and not students_df.empty:
            # Convert to CSV
            csv = students_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "Exportar Alunos (CSV)",
                csv,
                "alunos_completo.csv",
                "text/csv",
                key='download-students-csv'
            )
        else:
            st.info("Não há dados de alunos para exportar.")
    
    with col2:
        if payments_df is not None and not payments_df.empty:
            # Convert to CSV
            csv = payments_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "Exportar Pagamentos (CSV)",
                csv,
                "pagamentos_completo.csv",
                "text/csv",
                key='download-payments-csv'
            )
        else:
            st.info("Não há dados de pagamentos para exportar.")
    
    with col3:
        if internships_df is not None and not internships_df.empty:
            # Convert to CSV
            csv = internships_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "Exportar Estágios (CSV)",
                csv,
                "estagios_completo.csv",
                "text/csv",
                key='download-internships-csv'
            )
        else:
            st.info("Não há dados de estágios para exportar.")
    
    # Export report of student hours
    st.subheader("Relatório de Horas de Estágio")
    
    if internships_df is not None and not internships_df.empty and students_df is not None and not students_df.empty:
        # Get active students
        active_students = get_active_students(students_df)
        
        if not active_students.empty:
            # Compute hours for each student
            student_hours = []
            
            for _, student in active_students.iterrows():
                phone = student["phone"]
                name = student["name"]
                total_hours = get_student_internship_hours(internships_df, phone)
                topics = get_student_internship_topics(internships_df, phone)
                
                student_hours.append({
                    "Nome": name,
                    "Telefone": phone,
                    "Total de Horas": f"{total_hours:.1f}",
                    "Temas": ", ".join(topics[:5]) + ("..." if len(topics) > 5 else "")
                })
            
            # Convert to dataframe for export
            student_hours_df = pd.DataFrame(student_hours)
            
            # Option to download
            csv = student_hours_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "Exportar Relatório de Horas (CSV)",
                csv,
                "relatorio_horas_estagio.csv",
                "text/csv",
                key='download-hours-csv'
            )
        else:
            st.info("Não há alunos ativos para gerar o relatório.")
    else:
        st.info("Não há dados suficientes para gerar o relatório de horas.")
