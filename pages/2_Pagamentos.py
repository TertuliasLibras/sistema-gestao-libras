import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from utils import (
    load_students_data, 
    load_payments_data,
    save_payments_data,
    format_phone,
    format_currency,
    get_active_students
)
from config import get_logo_path

st.set_page_config(
    page_title="Pagamentos - Sistema de Gestão Libras",
    page_icon="💰",
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
    st.title("Gerenciamento de Pagamentos")

# Load data
students_df = load_students_data()
payments_df = load_payments_data()

# Create tabs for different operations
tab1, tab2, tab3 = st.tabs(["Registrar Pagamento", "Listar Pagamentos", "Gerar Pagamentos Mensais"])

with tab1:
    st.subheader("Registrar Novo Pagamento")
    
    if students_df is not None and not students_df.empty:
        # Get active students
        active_students = get_active_students(students_df)
        
        if not active_students.empty:
            with st.form("payment_form"):
                # Student selection
                selected_phone = st.selectbox(
                    "Selecione o aluno:",
                    options=active_students["phone"].tolist(),
                    format_func=lambda x: f"{active_students.loc[active_students['phone'] == x, 'name'].values[0]} ({x})"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Payment information
                    payment_date = st.date_input("Data do Pagamento", datetime.now())
                    due_date = st.date_input("Data de Vencimento", datetime.now())
                    
                with col2:
                    # Get student's monthly fee
                    student_fee = active_students.loc[active_students["phone"] == selected_phone, "monthly_fee"].values[0]
                    amount = st.number_input("Valor (R$)", min_value=0.0, value=float(student_fee), step=10.0, format="%.2f")
                    
                    # Get current month and year for reference
                    current_month = datetime.now().month
                    current_year = datetime.now().year
                    
                    month_options = list(range(1, 13))
                    month_names = [calendar.month_name[m] for m in month_options]
                    
                    selected_month = st.selectbox(
                        "Mês de Referência",
                        options=month_options,
                        format_func=lambda x: calendar.month_name[x],
                        index=current_month - 1
                    )
                    
                    year_options = list(range(current_year - 1, current_year + 3))
                    selected_year = st.selectbox(
                        "Ano de Referência",
                        options=year_options,
                        index=1  # Default to current year
                    )
                
                # Payment status
                status = st.selectbox(
                    "Status do Pagamento",
                    ["paid", "pending", "overdue", "canceled"],
                    format_func=lambda x: {
                        "paid": "Pago",
                        "pending": "Pendente",
                        "overdue": "Atrasado",
                        "canceled": "Cancelado"
                    }.get(x)
                )
                
                notes = st.text_area("Observações")
                
                submit_button = st.form_submit_button("Registrar Pagamento")
            
            if submit_button:
                # Create new payment record
                new_payment = {
                    "phone": selected_phone,
                    "payment_date": payment_date.strftime("%Y-%m-%d") if status == "paid" else None,
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "amount": amount,
                    "month_reference": selected_month,
                    "year_reference": selected_year,
                    "status": status,
                    "notes": notes
                }
                
                # Add to dataframe
                if payments_df is None:
                    payments_df = pd.DataFrame([new_payment])
                else:
                    payments_df = pd.concat([payments_df, pd.DataFrame([new_payment])], ignore_index=True)
                
                # Save to CSV
                save_payments_data(payments_df)
                
                st.success(f"Pagamento registrado com sucesso para o mês {calendar.month_name[selected_month]}/{selected_year}!")
                
                # Check for existing payments for this month/year/student
                existing_payments = payments_df[
                    (payments_df["phone"] == selected_phone) & 
                    (payments_df["month_reference"] == selected_month) & 
                    (payments_df["year_reference"] == selected_year)
                ]
                
                if len(existing_payments) > 1:
                    st.warning(f"Atenção: Existem {len(existing_payments)} pagamentos registrados para este aluno no mês {calendar.month_name[selected_month]}/{selected_year}.")
        else:
            st.warning("Não há alunos ativos no sistema. Cadastre um aluno primeiro.")
    else:
        st.warning("Não há alunos cadastrados no sistema. Cadastre um aluno primeiro.")

with tab2:
    st.subheader("Listar Pagamentos")
    
    if payments_df is not None and not payments_df.empty:
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filtrar por Status",
                ["Todos", "Pago", "Pendente", "Atrasado", "Cancelado"],
                key="status_filter"
            )
            
            status_map = {
                "Pago": "paid",
                "Pendente": "pending",
                "Atrasado": "overdue",
                "Cancelado": "canceled"
            }
        
        with col2:
            if students_df is not None and not students_df.empty:
                student_filter = st.selectbox(
                    "Filtrar por Aluno",
                    ["Todos"] + students_df["name"].tolist(),
                    key="student_filter"
                )
            else:
                student_filter = "Todos"
        
        with col3:
            date_options = ["Todos", "Mês Atual", "Mês Anterior", "Próximo Mês", "Personalizado"]
            date_filter = st.selectbox("Filtrar por Data", date_options, key="date_filter")
            
            if date_filter == "Personalizado":
                date_range = st.date_input(
                    "Selecione o período",
                    value=(
                        datetime.now().replace(day=1),
                        (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                    ),
                    key="date_range"
                )
        
        # Apply filters
        filtered_df = payments_df.copy()
        
        # Status filter
        if status_filter != "Todos":
            filtered_df = filtered_df[filtered_df["status"] == status_map.get(status_filter)]
        
        # Student filter
        if student_filter != "Todos" and students_df is not None:
            student_phone = students_df.loc[students_df["name"] == student_filter, "phone"].values[0]
            filtered_df = filtered_df[filtered_df["phone"] == student_phone]
        
        # Date filter
        if date_filter != "Todos":
            filtered_df["due_date"] = pd.to_datetime(filtered_df["due_date"], errors='coerce')
            
            if date_filter == "Mês Atual":
                start_date = datetime.now().replace(day=1)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                filtered_df = filtered_df[
                    (filtered_df["due_date"] >= pd.Timestamp(start_date)) & 
                    (filtered_df["due_date"] <= pd.Timestamp(end_date))
                ]
            elif date_filter == "Mês Anterior":
                end_date = datetime.now().replace(day=1) - timedelta(days=1)
                start_date = end_date.replace(day=1)
                filtered_df = filtered_df[
                    (filtered_df["due_date"] >= pd.Timestamp(start_date)) & 
                    (filtered_df["due_date"] <= pd.Timestamp(end_date))
                ]
            elif date_filter == "Próximo Mês":
                start_date = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                filtered_df = filtered_df[
                    (filtered_df["due_date"] >= pd.Timestamp(start_date)) & 
                    (filtered_df["due_date"] <= pd.Timestamp(end_date))
                ]
            elif date_filter == "Personalizado" and len(date_range) == 2:
                filtered_df = filtered_df[
                    (filtered_df["due_date"] >= pd.Timestamp(date_range[0])) & 
                    (filtered_df["due_date"] <= pd.Timestamp(date_range[1]))
                ]
        
        # Display data
        if not filtered_df.empty:
            # Add student name to the dataframe for display
            if students_df is not None and not students_df.empty:
                filtered_df = pd.merge(
                    filtered_df,
                    students_df[["phone", "name"]],
                    on="phone",
                    how="left"
                )
            
            # Format dates for display
            filtered_df["payment_date"] = pd.to_datetime(filtered_df["payment_date"], errors='coerce')
            filtered_df["payment_date"] = filtered_df["payment_date"].apply(
                lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
            )
            
            filtered_df["due_date"] = pd.to_datetime(filtered_df["due_date"], errors='coerce')
            filtered_df["due_date"] = filtered_df["due_date"].apply(
                lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
            )
            
            # Add month name for display
            filtered_df["month_name"] = filtered_df["month_reference"].apply(
                lambda x: calendar.month_name[x] if pd.notna(x) and 1 <= x <= 12 else ""
            )
            
            # Format status for display
            filtered_df["status_display"] = filtered_df["status"].map({
                "paid": "Pago",
                "pending": "Pendente",
                "overdue": "Atrasado",
                "canceled": "Cancelado"
            })
            
            # Format amount as currency
            filtered_df["amount_display"] = filtered_df["amount"].apply(lambda x: f"R$ {x:.2f}" if pd.notna(x) else "")
            
            # Choose columns to display
            display_columns = ["name", "phone", "month_name", "year_reference", "amount_display", "due_date", "payment_date", "status_display", "notes"]
            display_df = filtered_df[display_columns].copy()
            
            # Rename columns for display
            display_df.columns = [
                "Aluno", "Telefone", "Mês", "Ano", "Valor", "Vencimento", "Pagamento", "Status", "Observações"
            ]
            
            st.dataframe(display_df, use_container_width=True)
            
            # Summary section
            st.subheader("Resumo")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Pagamentos", len(filtered_df))
            
            with col2:
                total_amount = filtered_df["amount"].sum()
                st.metric("Valor Total", format_currency(total_amount))
            
            with col3:
                paid_amount = filtered_df[filtered_df["status"] == "paid"]["amount"].sum()
                st.metric("Total Pago", format_currency(paid_amount))
            
            with col4:
                pending_amount = filtered_df[filtered_df["status"].isin(["pending", "overdue"])]["amount"].sum()
                st.metric("Total Pendente", format_currency(pending_amount))
            
            # Download option
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Baixar dados filtrados (CSV)",
                csv,
                "pagamentos.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.warning("Nenhum pagamento encontrado com os filtros selecionados.")
    else:
        st.info("Não há pagamentos registrados.")

with tab3:
    st.subheader("Gerar Pagamentos Mensais")
    
    st.write("""
    Utilize esta função para gerar registros de pagamento pendentes para todos os alunos ativos 
    para um mês específico. Isso é útil para criar automaticamente os pagamentos do próximo mês.
    """)
    
    if students_df is not None and not students_df.empty:
        # Get active students
        active_students = get_active_students(students_df)
        
        if not active_students.empty:
            with st.form("generate_payments_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Month and year selection
                    month_options = list(range(1, 13))
                    current_month = (datetime.now().month % 12) + 1  # Default to next month
                    
                    selected_month = st.selectbox(
                        "Mês",
                        options=month_options,
                        format_func=lambda x: calendar.month_name[x],
                        index=current_month - 1
                    )
                    
                    year_options = list(range(datetime.now().year, datetime.now().year + 3))
                    selected_year = st.selectbox("Ano", options=year_options)
                
                with col2:
                    # Due date options
                    due_day = st.number_input("Dia de vencimento", min_value=1, max_value=28, value=10)
                    
                    # Days before due date to generate payments
                    days_before = st.number_input(
                        "Dias antes do vencimento para gerar",
                        min_value=0,
                        max_value=60,
                        value=15,
                        help="Quantos dias antes do vencimento os pagamentos devem ser gerados"
                    )
                
                payment_status = st.selectbox(
                    "Status inicial dos pagamentos",
                    ["pending", "overdue"],
                    format_func=lambda x: "Pendente" if x == "pending" else "Atrasado"
                )
                
                override_existing = st.checkbox(
                    "Sobrescrever pagamentos existentes",
                    help="Se marcado, pagamentos existentes para o mês/ano serão substituídos"
                )
                
                submit_button = st.form_submit_button("Gerar Pagamentos")
                
                if submit_button:
                    # Calculate due date
                    if selected_month == 2 and due_day > 28:
                        due_day = 28
                    
                    try:
                        due_date = datetime(selected_year, selected_month, due_day).date()
                    except ValueError:
                        # Handle invalid dates (like Feb 30)
                        st.error("Data de vencimento inválida. Por favor, selecione outro dia.")
                        due_date = None
                    
                    if due_date:
                        # Count how many payments will be generated
                        total_students = len(active_students)
                        
                        # Check for existing payments for this month/year
                        existing_payments = 0
                        
                        if payments_df is not None and not payments_df.empty:
                            for phone in active_students["phone"]:
                                has_payment = (
                                    (payments_df["phone"] == phone) & 
                                    (payments_df["month_reference"] == selected_month) & 
                                    (payments_df["year_reference"] == selected_year)
                                ).any()
                                
                                if has_payment:
                                    existing_payments += 1
                        
                        st.info(f"Serão gerados pagamentos para {total_students} alunos ativos para {calendar.month_name[selected_month]}/{selected_year}.")
                        
                        if existing_payments > 0:
                            st.warning(f"{existing_payments} alunos já possuem pagamentos para este mês. " + 
                                      ("Esses registros serão substituídos." if override_existing else "Novos registros não serão criados para estes alunos."))
                        
                        # Confirm generation
                        confirm = st.checkbox("Confirmar geração de pagamentos")
                        
                        if confirm:
                            # Generate payments
                            new_payments = []
                            updated_count = 0
                            
                            for _, student in active_students.iterrows():
                                phone = student["phone"]
                                
                                # Check if payment already exists
                                has_existing = False
                                
                                if payments_df is not None and not payments_df.empty:
                                    has_existing = (
                                        (payments_df["phone"] == phone) & 
                                        (payments_df["month_reference"] == selected_month) & 
                                        (payments_df["year_reference"] == selected_year)
                                    ).any()
                                
                                if override_existing or not has_existing:
                                    # If should override, remove existing payments first
                                    if override_existing and has_existing and payments_df is not None:
                                        payments_df = payments_df[
                                            ~((payments_df["phone"] == phone) & 
                                            (payments_df["month_reference"] == selected_month) & 
                                            (payments_df["year_reference"] == selected_year))
                                        ]
                                        updated_count += 1
                                    
                                    # Create new payment record
                                    new_payment = {
                                        "phone": phone,
                                        "payment_date": None,
                                        "due_date": due_date.strftime("%Y-%m-%d"),
                                        "amount": student["monthly_fee"],
                                        "month_reference": selected_month,
                                        "year_reference": selected_year,
                                        "status": payment_status,
                                        "notes": f"Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y')}"
                                    }
                                    
                                    new_payments.append(new_payment)
                            
                            # Add to dataframe
                            if new_payments:
                                if payments_df is None:
                                    payments_df = pd.DataFrame(new_payments)
                                else:
                                    payments_df = pd.concat([payments_df, pd.DataFrame(new_payments)], ignore_index=True)
                                
                                # Save to CSV
                                save_payments_data(payments_df)
                                
                                st.success(f"{len(new_payments)} novos pagamentos gerados e {updated_count} atualizados com sucesso!")
                            else:
                                st.warning("Nenhum novo pagamento foi gerado.")
        else:
            st.warning("Não há alunos ativos no sistema. Cadastre um aluno primeiro.")
    else:
        st.warning("Não há alunos cadastrados no sistema. Cadastre um aluno primeiro.")

# Help section at bottom
with st.expander("Ajuda"):
    st.write("""
    ### Como gerenciar pagamentos
    
    - **Registrar Pagamento**: Registre novos pagamentos manualmente para alunos ativos.
    - **Listar Pagamentos**: Visualize, filtre e exporte todos os pagamentos registrados.
    - **Gerar Pagamentos Mensais**: Crie automaticamente registros de pagamento pendentes para todos os alunos ativos para um mês específico.
    
    ### Status de pagamento
    
    - **Pago**: O pagamento foi confirmado.
    - **Pendente**: O pagamento está aguardando confirmação.
    - **Atrasado**: O prazo de pagamento foi excedido.
    - **Cancelado**: O pagamento foi cancelado.
    """)
