import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from utils import (
    load_students_data, 
    load_payments_data, 
    save_payments_data,
    format_phone,
    format_currency
)
from login import verificar_autenticacao

# Check authentication
if not verificar_autenticacao():
    st.error("Você precisa fazer login para acessar esta página.")
    st.stop()

# Set page config
st.set_page_config(
    page_title="Pagamentos - Sistema de Gestão",
    page_icon="💰",
    layout="wide"
)

# Display logo and title
col1, col2 = st.columns([1, 3])
with col1:
    st.image('assets/images/logo.svg', width=100)
with col2:
    st.title("Gestão de Pagamentos")

# Load data
students_df = load_students_data()
payments_df = load_payments_data()

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Registrar Pagamento", "Visualizar Pagamentos", "Relatório Financeiro"])

with tab1:
    st.subheader("Registrar Novo Pagamento")
    
    if not students_df.empty:
        # Get only active students
        active_students = students_df[students_df['status'] == 'active']
        
        if not active_students.empty:
            # Show student selection
            selected_student = st.selectbox(
                "Selecione o Aluno",
                active_students['phone'].tolist(),
                format_func=lambda x: f"{active_students[active_students['phone'] == x]['name'].iloc[0]} ({format_phone(x)})"
            )
            
            if selected_student:
                student = active_students[active_students['phone'] == selected_student].iloc[0]
                
                # Get pending payments for this student
                student_payments = payments_df[
                    (payments_df['phone'] == selected_student) & 
                    (payments_df['status'] == 'pending')
                ]
                
                if not student_payments.empty:
                    # Sort by due date
                    student_payments = student_payments.sort_values('due_date')
                    
                    # Format due date and reference for display
                    student_payments['due_date_formatted'] = pd.to_datetime(student_payments['due_date']).dt.strftime('%d/%m/%Y')
                    student_payments['reference'] = student_payments.apply(
                        lambda x: f"{x['month_reference']}/{x['year_reference']}", axis=1
                    )
                    
                    st.subheader(f"Pagamentos Pendentes para {student['name']}")
                    
                    # Show pending payments
                    for i, payment in student_payments.iterrows():
                        with st.expander(f"Referência: {payment['reference']} - Vencimento: {payment['due_date_formatted']}"):
                            with st.form(f"payment_form_{i}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    payment_date = st.date_input("Data do Pagamento", datetime.now())
                                    status = st.selectbox(
                                        "Status",
                                        ["paid", "pending", "canceled"],
                                        format_func=lambda x: {
                                            "paid": "Pago",
                                            "pending": "Pendente",
                                            "canceled": "Cancelado"
                                        }[x],
                                        index=0  # Default to 'paid'
                                    )
                                
                                with col2:
                                    amount = st.number_input(
                                        "Valor (R$)",
                                        min_value=0.0,
                                        value=float(payment['amount']),
                                        format="%.2f"
                                    )
                                    notes = st.text_input("Observações")
                                
                                submit = st.form_submit_button("Registrar Pagamento")
                                
                                if submit:
                                    # Update payment record
                                    payments_df.at[i, 'payment_date'] = payment_date
                                    payments_df.at[i, 'status'] = status
                                    payments_df.at[i, 'amount'] = amount
                                    payments_df.at[i, 'notes'] = notes
                                    
                                    # Save data
                                    if save_payments_data(payments_df):
                                        st.success(f"Pagamento registrado com sucesso para {student['name']}!")
                                        st.rerun()
                                    else:
                                        st.error("Erro ao registrar pagamento.")
                else:
                    st.info(f"Não há pagamentos pendentes para {student['name']}.")
                    
                    # Option to add new payment
                    st.subheader("Adicionar Novo Pagamento")
                    
                    with st.form("new_payment_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            payment_date = st.date_input("Data do Pagamento", datetime.now())
                            due_date = st.date_input("Data de Vencimento", datetime.now())
                            status = st.selectbox(
                                "Status",
                                ["paid", "pending", "canceled"],
                                format_func=lambda x: {
                                    "paid": "Pago",
                                    "pending": "Pendente",
                                    "canceled": "Cancelado"
                                }[x]
                            )
                        
                        with col2:
                            month_reference = st.selectbox(
                                "Mês de Referência",
                                range(1, 13),
                                format_func=lambda x: {
                                    1: "Janeiro", 2: "Fevereiro", 3: "Março",
                                    4: "Abril", 5: "Maio", 6: "Junho", 
                                    7: "Julho", 8: "Agosto", 9: "Setembro",
                                    10: "Outubro", 11: "Novembro", 12: "Dezembro"
                                }[x]
                            )
                            year_reference = st.selectbox(
                                "Ano de Referência",
                                range(datetime.now().year - 1, datetime.now().year + 2)
                            )
                            amount = st.number_input(
                                "Valor (R$)",
                                min_value=0.0,
                                value=float(student['monthly_fee']),
                                format="%.2f"
                            )
                        
                        notes = st.text_input("Observações")
                        
                        submit = st.form_submit_button("Adicionar Pagamento")
                        
                        if submit:
                            # Create new payment record
                            new_payment = {
                                'phone': selected_student,
                                'payment_date': payment_date if status == 'paid' else None,
                                'due_date': due_date,
                                'amount': amount,
                                'month_reference': month_reference,
                                'year_reference': year_reference,
                                'status': status,
                                'notes': notes
                            }
                            
                            # Add to dataframe
                            if payments_df.empty:
                                payments_df = pd.DataFrame([new_payment])
                            else:
                                payments_df = pd.concat([payments_df, pd.DataFrame([new_payment])], ignore_index=True)
                            
                            # Save data
                            if save_payments_data(payments_df):
                                st.success(f"Pagamento adicionado com sucesso para {student['name']}!")
                                st.rerun()
                            else:
                                st.error("Erro ao adicionar pagamento.")
        else:
            st.warning("Não há alunos ativos para registrar pagamentos.")
    else:
        st.warning("Não há alunos cadastrados para registrar pagamentos.")

with tab2:
    st.subheader("Visualizar Pagamentos")
    
    if not payments_df.empty:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["Todos", "Pago", "Pendente", "Atrasado", "Cancelado"],
                index=0
            )
        
        with col2:
            month_filter = st.selectbox(
                "Mês de Referência",
                [0] + list(range(1, 13)),
                format_func=lambda x: {
                    0: "Todos",
                    1: "Janeiro", 2: "Fevereiro", 3: "Março",
                    4: "Abril", 5: "Maio", 6: "Junho", 
                    7: "Julho", 8: "Agosto", 9: "Setembro",
                    10: "Outubro", 11: "Novembro", 12: "Dezembro"
                }[x]
            )
        
        with col3:
            year_filter = st.selectbox(
                "Ano de Referência",
                [0] + list(range(datetime.now().year - 2, datetime.now().year + 2)),
                format_func=lambda x: "Todos" if x == 0 else x,
                index=0
            )
        
        # Apply filters
        filtered_df = payments_df.copy()
        
        # Status filter
        if status_filter != "Todos":
            status_map = {
                "Pago": "paid",
                "Pendente": "pending",
                "Atrasado": "overdue",
                "Cancelado": "canceled"
            }
            filtered_df = filtered_df[filtered_df['status'] == status_map[status_filter]]
        
        # Month filter
        if month_filter != 0:
            filtered_df = filtered_df[filtered_df['month_reference'] == month_filter]
        
        # Year filter
        if year_filter != 0:
            filtered_df = filtered_df[filtered_df['year_reference'] == year_filter]
        
        if not filtered_df.empty:
            # Process data for display
            display_df = filtered_df.copy()
            
            # Add student name from students_df
            display_df = display_df.merge(
                students_df[['phone', 'name']],
                on='phone',
                how='left'
            )
            
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
            status_map = {
                'paid': 'Pago',
                'pending': 'Pendente',
                'overdue': 'Atrasado',
                'canceled': 'Cancelado'
            }
            display_df['status_pt'] = display_df['status'].map(status_map)
            
            # Reorder and select columns for display
            display_columns = [
                'name', 'telefone_formatado', 'referencia', 
                'data_vencimento', 'data_pagamento', 'amount', 'status_pt'
            ]
            
            column_names = [
                'Nome', 'Telefone', 'Referência', 
                'Vencimento', 'Pagamento', 'Valor (R$)', 'Status'
            ]
            
            st.dataframe(
                display_df[display_columns].rename(columns=dict(zip(display_columns, column_names))),
                use_container_width=True
            )
            
            # Payment selection for details
            st.subheader("Detalhes do Pagamento")
            
            # Create a unique identifier for each payment
            display_df['payment_id'] = display_df.index
            display_df['payment_label'] = display_df.apply(
                lambda x: f"{x['name']} - {x['referencia']} ({x['status_pt']})", 
                axis=1
            )
            
            selected_payment_id = st.selectbox(
                "Selecione um pagamento para ver/editar",
                display_df['payment_id'].tolist(),
                format_func=lambda x: display_df[display_df['payment_id'] == x]['payment_label'].iloc[0]
            )
            
            if selected_payment_id is not None:
                # Get selected payment
                payment_idx = selected_payment_id
                payment = display_df[display_df['payment_id'] == selected_payment_id].iloc[0]
                
                # Display payment details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Aluno:** {payment['name']}")
                    st.markdown(f"**Telefone:** {payment['telefone_formatado']}")
                    st.markdown(f"**Referência:** {payment['referencia']}")
                    st.markdown(f"**Status:** {payment['status_pt']}")
                
                with col2:
                    st.markdown(f"**Valor:** R$ {payment['amount']:.2f}")
                    st.markdown(f"**Vencimento:** {payment['data_vencimento']}")
                    
                    if payment['status'] == 'paid':
                        st.markdown(f"**Data de Pagamento:** {payment['data_pagamento']}")
                
                # Display notes
                if pd.notna(payment['notes']) and payment['notes']:
                    st.subheader("Observações")
                    st.write(payment['notes'])
                
                # Edit payment
                st.subheader("Editar Pagamento")
                
                with st.form("edit_payment_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        payment_date = st.date_input(
                            "Data do Pagamento",
                            pd.to_datetime(payment['payment_date']) if pd.notna(payment['payment_date']) else datetime.now()
                        )
                        status = st.selectbox(
                            "Status",
                            ["paid", "pending", "canceled"],
                            format_func=lambda x: {
                                "paid": "Pago",
                                "pending": "Pendente",
                                "canceled": "Cancelado"
                            }[x],
                            index=["paid", "pending", "canceled"].index(payment['status']) 
                                if payment['status'] in ["paid", "pending", "canceled"] else 0
                        )
                    
                    with col2:
                        amount = st.number_input(
                            "Valor (R$)",
                            min_value=0.0,
                            value=float(payment['amount']),
                            format="%.2f"
                        )
                        notes = st.text_input("Observações", value=payment['notes'] if pd.notna(payment['notes']) else "")
                    
                    submit = st.form_submit_button("Atualizar Pagamento")
                    
                    if submit:
                        # Update payment record
                        payments_df.at[payment_idx, 'payment_date'] = payment_date if status == 'paid' else None
                        payments_df.at[payment_idx, 'status'] = status
                        payments_df.at[payment_idx, 'amount'] = amount
                        payments_df.at[payment_idx, 'notes'] = notes
                        
                        # Save data
                        if save_payments_data(payments_df):
                            st.success("Pagamento atualizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar pagamento.")
        else:
            st.info("Não há pagamentos que correspondam aos filtros selecionados.")
    else:
        st.info("Não há pagamentos registrados.")

with tab3:
    st.subheader("Relatório Financeiro")
    
    if not payments_df.empty:
        # Date range selection
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Data Inicial", value=datetime.now().replace(day=1, month=1))
        
        with col2:
            end_date = st.date_input("Data Final", value=datetime.now())
        
        # Convert dates to datetime
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        
        # Filter payments by date
        date_filtered_df = payments_df[
            (pd.to_datetime(payments_df['due_date']) >= start_datetime) & 
            (pd.to_datetime(payments_df['due_date']) <= end_datetime)
        ]
        
        if not date_filtered_df.empty:
            # Total values by status
            st.subheader("Valores Totais por Status")
            
            # Calculate totals
            total_paid = date_filtered_df[date_filtered_df['status'] == 'paid']['amount'].sum()
            total_pending = date_filtered_df[date_filtered_df['status'] == 'pending']['amount'].sum()
            total_overdue = date_filtered_df[date_filtered_df['status'] == 'overdue']['amount'].sum()
            total_canceled = date_filtered_df[date_filtered_df['status'] == 'canceled']['amount'].sum()
            total_all = date_filtered_df['amount'].sum()
            
            # Create columns for metrics
            c1, c2, c3, c4, c5 = st.columns(5)
            
            with c1:
                st.metric("Total", format_currency(total_all))
            
            with c2:
                st.metric("Pago", format_currency(total_paid))
            
            with c3:
                st.metric("Pendente", format_currency(total_pending))
            
            with c4:
                st.metric("Atrasado", format_currency(total_overdue))
            
            with c5:
                st.metric("Cancelado", format_currency(total_canceled))
            
            # Monthly distribution
            st.subheader("Distribuição Mensal")
            
            # Convert due date to month/year
            date_filtered_df['month_year'] = pd.to_datetime(date_filtered_df['due_date']).dt.strftime('%Y-%m')
            
            # Group by month and status
            monthly_status = date_filtered_df.groupby(['month_year', 'status'])['amount'].sum().reset_index()
            
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
                title='Valores Mensais por Status',
                labels={'month_year': 'Mês', 'value': 'Valor (R$)', 'variable': 'Status'},
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
            
            # Payment status distribution
            st.subheader("Distribuição de Status de Pagamento")
            
            # Count by status
            status_counts = date_filtered_df['status'].value_counts().reset_index()
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
            
            # Export data option
            st.subheader("Exportar Dados")
            
            # Create export dataframe
            export_df = date_filtered_df.copy()
            
            # Add student name
            export_df = export_df.merge(
                students_df[['phone', 'name']],
                on='phone',
                how='left'
            )
            
            # Format columns for export
            export_df['payment_date'] = pd.to_datetime(export_df['payment_date']).apply(
                lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
            )
            export_df['due_date'] = pd.to_datetime(export_df['due_date']).dt.strftime('%d/%m/%Y')
            
            # Map status to Portuguese
            export_df['status'] = export_df['status'].map(status_map)
            
            # Select and rename columns
            export_columns = [
                'name', 'phone', 'month_reference', 'year_reference',
                'due_date', 'payment_date', 'amount', 'status', 'notes'
            ]
            export_column_names = [
                'Nome', 'Telefone', 'Mês', 'Ano',
                'Vencimento', 'Pagamento', 'Valor', 'Status', 'Observações'
            ]
            
            final_export_df = export_df[export_columns].rename(
                columns=dict(zip(export_columns, export_column_names))
            )
            
            # Download button
            csv_export = final_export_df.to_csv(index=False).encode('utf-8')
            
            filename = f"pagamentos_{start_date.strftime('%Y%m%d')}_a_{end_date.strftime('%Y%m%d')}.csv"
            
            st.download_button(
                "Baixar Relatório (CSV)",
                csv_export,
                filename,
                "text/csv",
                key='download-payments-report'
            )
        else:
            st.info("Não há pagamentos no período selecionado.")
    else:
        st.info("Não há pagamentos registrados para gerar relatório.")
