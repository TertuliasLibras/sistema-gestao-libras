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
    format_phone,
    get_student_internship_hours
)
from login import verificar_autenticacao

# Check authentication
if not verificar_autenticacao():
    st.error("Você precisa fazer login para acessar esta página.")
    st.stop()

# Set page config
st.set_page_config(
    page_title="Relatórios - Sistema de Gestão",
    page_icon="📈",
    layout="wide"
)

# Display logo and title
col1, col2 = st.columns([1, 3])
with col1:
    st.image('assets/images/logo.svg', width=100)
with col2:
    st.title("Relatórios")

# Load data
students_df = load_students_data()
payments_df = load_payments_data()
internships_df = load_internships_data()

# Create tabs for different reports
tab1, tab2, tab3, tab4 = st.tabs([
    "Resumo Geral", 
    "Relatório de Alunos", 
    "Relatório Financeiro",
    "Relatório de Estágios"
])

with tab1:
    st.subheader("Resumo Geral do Sistema")
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)

    # Get active and canceled students
    active_students = get_active_students(students_df)
    canceled_students = get_canceled_students(students_df)
    overdue_payments = get_overdue_payments(students_df, payments_df)

    # Calculate metrics
    total_students = len(students_df) if not students_df.empty else 0
    active_count = len(active_students) if not active_students.empty else 0
    canceled_count = len(canceled_students) if not canceled_students.empty else 0
    overdue_count = len(overdue_payments) if not overdue_payments.empty else 0

    with col1:
        st.metric("Total de Alunos", total_students)

    with col2:
        st.metric("Alunos Ativos", active_count)

    with col3:
        st.metric("Alunos Cancelados", canceled_count)

    with col4:
        st.metric("Pagamentos Atrasados", overdue_count)
    
    # Financial metrics
    st.subheader("Métricas Financeiras")
    
    if not payments_df.empty:
        # Calculate metrics
        total_paid = payments_df[payments_df['status'] == 'paid']['amount'].sum()
        total_pending = payments_df[payments_df['status'] == 'pending']['amount'].sum()
        
        # Current month payments
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        current_month_payments = payments_df[
            (payments_df['month_reference'] == current_month) & 
            (payments_df['year_reference'] == current_year) & 
            (payments_df['status'] == 'paid')
        ]
        
        current_month_paid = current_month_payments['amount'].sum() if not current_month_payments.empty else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Recebido (Histórico)", f"R$ {total_paid:.2f}")
        
        with col2:
            st.metric("Total Pendente", f"R$ {total_pending:.2f}")
        
        with col3:
            st.metric(f"Recebido em {calendar.month_name[current_month]}/{current_year}", f"R$ {current_month_paid:.2f}")
    else:
        st.info("Não há dados de pagamentos para exibir métricas financeiras.")
    
    # Internship metrics
    st.subheader("Métricas de Estágios")
    
    if not internships_df.empty:
        # Calculate metrics
        total_internships = len(internships_df)
        total_hours = internships_df['duration_hours'].sum()
        
        # Average students per internship
        avg_students = 0
        if 'students' in internships_df.columns:
            student_counts = internships_df['students'].apply(lambda x: len(str(x).split(',')) if pd.notna(x) else 0)
            avg_students = student_counts.mean()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Estágios", total_internships)
        
        with col2:
            st.metric("Total de Horas", f"{total_hours:.1f}h")
        
        with col3:
            st.metric("Média de Alunos por Estágio", f"{avg_students:.1f}")
    else:
        st.info("Não há dados de estágios para exibir métricas.")

with tab2:
    st.subheader("Relatório de Alunos")
    
    if not students_df.empty:
        # Date range selection
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Data Inicial de Matrícula",
                value=datetime.now().replace(day=1, month=1)
            )
        
        with col2:
            end_date = st.date_input(
                "Data Final de Matrícula",
                value=datetime.now()
            )
        
        # Convert dates to datetime
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        
        # Convert enrollment date to datetime
        students_df['enrollment_date'] = pd.to_datetime(students_df['enrollment_date'])
        
        # Filter students by enrollment date
        filtered_students = students_df[
            (students_df['enrollment_date'] >= start_datetime) & 
            (students_df['enrollment_date'] <= end_datetime)
        ]
        
        if not filtered_students.empty:
            # Status filter
            status_filter = st.selectbox(
                "Status",
                ["Todos", "Ativos", "Cancelados"]
            )
            
            # Apply status filter
            if status_filter == "Ativos":
                filtered_students = filtered_students[filtered_students['status'] == 'active']
            elif status_filter == "Cancelados":
                filtered_students = filtered_students[filtered_students['status'] == 'canceled']
            
            # Count by status
            status_counts = filtered_students['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Quantidade']
            
            # Map status to Portuguese
            status_map = {'active': 'Ativo', 'canceled': 'Cancelado'}
            status_counts['Status'] = status_counts['Status'].map(status_map)
            
            # Create pie chart
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
            
            # Group by month and count enrollments
            enrollments_by_month = filtered_students.groupby(
                filtered_students['enrollment_date'].dt.strftime('%Y-%m')
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
            
            # Student details
            st.subheader("Detalhes dos Alunos")
            
            # Format data for display
            display_df = filtered_students.copy()
            
            # Format phone
            display_df['telefone_formatado'] = display_df['phone'].apply(format_phone)
            
            # Format date
            display_df['data_matricula'] = display_df['enrollment_date'].dt.strftime('%d/%m/%Y')
            
            # Map status to Portuguese
            display_df['status_pt'] = display_df['status'].map(status_map)
            
            # Format cancellation date
            if 'cancellation_date' in display_df.columns:
                display_df['data_cancelamento'] = pd.to_datetime(display_df['cancellation_date']).apply(
                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
                )
            
            # Calculate internship hours
            if not internships_df.empty:
                display_df['horas_estagio'] = display_df['phone'].apply(
                    lambda x: get_student_internship_hours(internships_df, x)
                )
            else:
                display_df['horas_estagio'] = 0
            
            # Select and rename columns for display
            display_columns = [
                'name', 'telefone_formatado', 'email', 'data_matricula', 
                'status_pt', 'monthly_fee', 'horas_estagio'
            ]
            
            if 'data_cancelamento' in display_df.columns:
                display_columns.append('data_cancelamento')
            
            column_names = [
                'Nome', 'Telefone', 'Email', 'Data de Matrícula', 
                'Status', 'Mensalidade (R$)', 'Horas de Estágio'
            ]
            
            if 'data_cancelamento' in display_df.columns:
                column_names.append('Data de Cancelamento')
            
            final_display_df = display_df[display_columns].rename(
                columns=dict(zip(display_columns, column_names))
            )
            
            st.dataframe(final_display_df, use_container_width=True)
            
            # Export option
            st.subheader("Exportar Dados")
            
            csv_export = final_display_df.to_csv(index=False).encode('utf-8')
            
            filename = f"alunos_{start_date.strftime('%Y%m%d')}_a_{end_date.strftime('%Y%m%d')}.csv"
            
            st.download_button(
                "Baixar Relatório (CSV)",
                csv_export,
                filename,
                "text/csv",
                key='download-students-report'
            )
        else:
            st.info("Não há alunos matriculados no período selecionado.")
    else:
        st.info("Não há dados de alunos para gerar relatório.")

with tab3:
    st.subheader("Relatório Financeiro")
    
    if not payments_df.empty:
        # Date range selection
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Data Inicial",
                value=datetime.now().replace(day=1, month=1),
                key="finance_start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "Data Final",
                value=datetime.now(),
                key="finance_end_date"
            )
        
        # Convert dates to datetime
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        
        # Convert payment dates to datetime
        for col in ['payment_date', 'due_date']:
            if col in payments_df.columns:
                payments_df[col] = pd.to_datetime(payments_df[col], errors='coerce')
        
        # Filter by due date
        filtered_payments = payments_df[
            (payments_df['due_date'] >= start_datetime) & 
            (payments_df['due_date'] <= end_datetime)
        ]
        
        if not filtered_payments.empty:
            # Status filter
            status_filter = st.selectbox(
                "Status",
                ["Todos", "Pago", "Pendente", "Atrasado", "Cancelado"],
                key="finance_status_filter"
            )
            
            # Apply status filter
            if status_filter != "Todos":
                status_map = {
                    "Pago": "paid",
                    "Pendente": "pending",
                    "Atrasado": "overdue",
                    "Cancelado": "canceled"
                }
                filtered_payments = filtered_payments[filtered_payments['status'] == status_map[status_filter]]
            
            # Monthly revenue analysis
            st.subheader("Análise de Receita Mensal")
            
            # Group by month/year reference
            reference_df = filtered_payments.copy()
            reference_df['month_year'] = reference_df.apply(
                lambda x: f"{x['year_reference']}-{x['month_reference']:02d}", axis=1
            )
            
            # Group by reference and status
            monthly_status = reference_df.groupby(['month_year', 'status'])['amount'].sum().reset_index()
            
            # Pivot to have status as columns
            monthly_pivot = monthly_status.pivot(
                index='month_year',
                columns='status',
                values='amount'
            ).fillna(0).reset_index()
            
            # Ensure all status columns exist
            for status in ['paid', 'pending', 'overdue', 'canceled']:
                if status not in monthly_pivot.columns:
                    monthly_pivot[status] = 0
            
            # Create stacked bar chart
            fig = px.bar(
                monthly_pivot,
                x='month_year',
                y=['paid', 'pending', 'overdue', 'canceled'],
                title='Valores Mensais por Status de Pagamento',
                labels={'month_year': 'Mês/Ano', 'value': 'Valor (R$)', 'variable': 'Status'},
                color_discrete_map={
                    'paid': 'green',
                    'pending': 'orange',
                    'overdue': 'red',
                    'canceled': 'gray'
                }
            )
            
            # Rename legend items
            fig.update_layout(
                legend_title="Status",
                xaxis_title="Mês/Ano",
                yaxis_title="Valor (R$)"
            )
            
            # Update names in legend
            newnames = {'paid': 'Pago', 'pending': 'Pendente', 'overdue': 'Atrasado', 'canceled': 'Cancelado'}
            fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Total values by status
            st.subheader("Valores Totais por Status")
            
            # Calculate totals
            total_paid = filtered_payments[filtered_payments['status'] == 'paid']['amount'].sum()
            total_pending = filtered_payments[filtered_payments['status'] == 'pending']['amount'].sum()
            total_overdue = filtered_payments[filtered_payments['status'] == 'overdue']['amount'].sum()
            total_canceled = filtered_payments[filtered_payments['status'] == 'canceled']['amount'].sum()
            
            # Create columns for metrics
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.metric("Pago", f"R$ {total_paid:.2f}")
            
            with c2:
                st.metric("Pendente", f"R$ {total_pending:.2f}")
            
            with c3:
                st.metric("Atrasado", f"R$ {total_overdue:.2f}")
            
            with c4:
                st.metric("Cancelado", f"R$ {total_canceled:.2f}")
            
            # Payment status distribution
            st.subheader("Distribuição de Status de Pagamento")
            
            # Count by status
            status_counts = filtered_payments['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Quantidade']
            
            # Map status to Portuguese
            status_map = {
                'paid': 'Pago',
                'pending': 'Pendente',
                'overdue': 'Atrasado',
                'canceled': 'Cancelado'
            }
            status_counts['Status'] = status_counts['Status'].map(status_map)
            
            # Create pie chart
            fig = px.pie(
                status_counts,
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
            
            # Payment details
            st.subheader("Detalhes dos Pagamentos")
            
            # Add student name
            if not students_df.empty:
                filtered_payments = filtered_payments.merge(
                    students_df[['phone', 'name']],
                    on='phone',
                    how='left'
                )
            
            # Format for display
            display_df = filtered_payments.copy()
            
            # Format phone
            display_df['telefone_formatado'] = display_df['phone'].apply(format_phone)
            
            # Format dates
            display_df['data_pagamento'] = pd.to_datetime(display_df['payment_date']).apply(
                lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
            )
            display_df['data_vencimento'] = pd.to_datetime(display_df['due_date']).dt.strftime('%d/%m/%Y')
            
            # Format reference
            display_df['referencia'] = display_df.apply(
                lambda x: f"{x['month_reference']}/{x['year_reference']}", axis=1
            )
            
            # Map status to Portuguese
            display_df['status_pt'] = display_df['status'].map(status_map)
            
            # Select columns for display
            display_columns = [
                'name', 'telefone_formatado', 'referencia', 
                'data_vencimento', 'data_pagamento', 'amount', 'status_pt'
            ]
            
            column_names = [
                'Nome', 'Telefone', 'Referência', 
                'Vencimento', 'Pagamento', 'Valor (R$)', 'Status'
            ]
            
            final_display_df = display_df[display_columns].rename(
                columns=dict(zip(display_columns, column_names))
            )
            
            st.dataframe(final_display_df, use_container_width=True)
            
            # Export option
            st.subheader("Exportar Dados")
            
            csv_export = final_display_df.to_csv(index=False).encode('utf-8')
            
            filename = f"financeiro_{start_date.strftime('%Y%m%d')}_a_{end_date.strftime('%Y%m%d')}.csv"
            
            st.download_button(
                "Baixar Relatório (CSV)",
                csv_export,
                filename,
                "text/csv",
                key='download-finance-report'
            )
        else:
            st.info("Não há pagamentos no período selecionado.")
    else:
        st.info("Não há dados de pagamentos para gerar relatório.")

with tab4:
    st.subheader("Relatório de Estágios")
    
    if not internships_df.empty:
        # Date range selection
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Data Inicial",
                value=datetime.now().replace(day=1, month=1),
                key="internship_start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "Data Final",
                value=datetime.now(),
                key="internship_end_date"
            )
        
        # Convert dates to datetime
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        
        # Convert internship date to datetime
        internships_df['date'] = pd.to_datetime(internships_df['date'])
        
        # Filter internships by date
        filtered_internships = internships_df[
            (internships_df['date'] >= start_datetime) & 
            (internships_df['date'] <= end_datetime)
        ]
        
        if not filtered_internships.empty:
            # Total metrics
            total_internships = len(filtered_internships)
            total_hours = filtered_internships['duration_hours'].sum()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total de Estágios", total_internships)
            
            with col2:
                st.metric("Total de Horas", f"{total_hours:.1f}h")
            
            # Monthly distribution
            st.subheader("Distribuição Mensal")
            
            # Format date as month/year
            filtered_internships['month_year'] = filtered_internships['date'].dt.strftime('%Y-%m')
            
            # Group by month and count
            monthly_counts = filtered_internships.groupby('month_year').size().reset_index(name='count')
            monthly_counts.columns = ['Mês', 'Quantidade']
            
            # Group by month and sum hours
            monthly_hours = filtered_internships.groupby('month_year')['duration_hours'].sum().reset_index()
            monthly_hours.columns = ['Mês', 'Horas']
            
            # Merge counts and hours
            monthly_data = monthly_counts.merge(monthly_hours, on='Mês')
            
            # Create bar chart
            fig = px.bar(
                monthly_data,
                x='Mês',
                y=['Quantidade', 'Horas'],
                title='Distribuição Mensal de Estágios',
                barmode='group',
                labels={'value': 'Valor', 'variable': 'Métrica'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Topics distribution
            st.subheader("Distribuição de Temas")
            
            topics = filtered_internships['topic'].value_counts().reset_index()
            topics.columns = ['Tema', 'Quantidade']
            
            fig = px.pie(
                topics,
                names='Tema',
                values='Quantidade',
                title='Distribuição de Temas de Estágio'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Student participation (if student data is available)
            if not students_df.empty:
                st.subheader("Participação dos Alunos")
                
                # Get unique students from all internships
                unique_students = set()
                for students_str in filtered_internships['students']:
                    if pd.notna(students_str):
                        student_phones = str(students_str).split(',')
                        for phone in student_phones:
                            if phone:  # Ensure phone is not empty
                                unique_students.add(phone)
                
                # Student participation data
                participation_data = []
                
                for phone in unique_students:
                    student_row = students_df[students_df['phone'] == phone]
                    
                    if not student_row.empty:
                        student = student_row.iloc[0]
                        
                        # Count internships this student participated in
                        internship_count = 0
                        total_student_hours = 0
                        
                        for _, internship in filtered_internships.iterrows():
                            if pd.notna(internship['students']) and phone in str(internship['students']).split(','):
                                internship_count += 1
                                total_student_hours += float(internship['duration_hours'])
                        
                        participation_data.append({
                            'name': student['name'],
                            'phone': phone,
                            'internship_count': internship_count,
                            'total_hours': total_student_hours
                        })
                
                if participation_data:
                    # Create dataframe from participation data
                    participation_df = pd.DataFrame(participation_data)
                    
                    # Sort by total hours (descending)
                    participation_df = participation_df.sort_values('total_hours', ascending=False)
                    
                    # Format phone for display
                    participation_df['phone_formatted'] = participation_df['phone'].apply(format_phone)
                    
                    # Display as dataframe
                    display_columns = ['name', 'phone_formatted', 'internship_count', 'total_hours']
                    display_df = participation_df[display_columns].copy()
                    display_df.columns = ['Nome', 'Telefone', 'Nº de Estágios', 'Total de Horas']
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Visualization - Top students by hours
                    st.subheader("Top Alunos por Horas de Estágio")
                    
                    # Take top 10 students
                    top_students = participation_df.head(10)
                    
                    fig = px.bar(
                        top_students,
                        x='name',
                        y='total_hours',
                        title='Top 10 Alunos por Horas de Estágio',
                        labels={'name': 'Aluno', 'total_hours': 'Total de Horas'},
                        color='total_hours',
                        color_continuous_scale='blues'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não há dados de participação para exibir.")
            
            # Internship details
            st.subheader("Detalhes dos Estágios")
            
            # Format date for display
            display_internships = filtered_internships.copy()
            display_internships['data'] = display_internships['date'].dt.strftime('%d/%m/%Y')
            
            # Order by date (descending)
            display_internships = display_internships.sort_values('date', ascending=False)
            
            # Select columns for display
            display_columns = ['data', 'topic', 'duration_hours']
            display_internships = display_internships[display_columns].rename(
                columns={'data': 'Data', 'topic': 'Tema', 'duration_hours': 'Duração (horas)'}
            )
            
            st.dataframe(display_internships, use_container_width=True)
            
            # Export options
            st.subheader("Exportar Dados")
            
            # Download button for internships
            csv_internships = display_internships.to_csv(index=False).encode('utf-8')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    "Baixar Dados de Estágios",
                    csv_internships,
                    f"estagios_{start_date.strftime('%Y%m%d')}_a_{end_date.strftime('%Y%m%d')}.csv",
                    "text/csv",
                    key='download-internships-report'
                )
            
            # Download button for student participation if available
            if 'participation_df' in locals() and not participation_df.empty:
                csv_participation = participation_df.to_csv(index=False).encode('utf-8')
                
                with col2:
                    st.download_button(
                        "Baixar Dados de Participação",
                        csv_participation,
                        f"participacao_{start_date.strftime('%Y%m%d')}_a_{end_date.strftime('%Y%m%d')}.csv",
                        "text/csv",
                        key='download-participation-report'
                    )
        else:
            st.info("Não há estágios no período selecionado.")
    else:
        st.info("Não há dados de estágios para gerar relatório.")
