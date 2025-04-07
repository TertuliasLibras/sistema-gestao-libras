import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from utils import (
    load_students_data, 
    load_internships_data,
    save_internships_data,
    format_phone,
    get_active_students,
    get_student_internship_hours
)
from config import get_logo_path

st.set_page_config(
    page_title="Estágios - Sistema de Gestão Libras",
    page_icon="📝",
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
    st.title("Gerenciamento de Estágios")

# Load data
students_df = load_students_data()
internships_df = load_internships_data()

# Create tabs for different operations
tab1, tab2, tab3 = st.tabs(["Registrar Estágio", "Listar Estágios", "Horas por Aluno"])

with tab1:
    st.subheader("Registrar Novo Estágio")
    
    if students_df is not None and not students_df.empty:
        # Get active students
        active_students = get_active_students(students_df)
        
        if not active_students.empty:
            with st.form("internship_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Internship information
                    date = st.date_input("Data do Estágio", datetime.now())
                    topic = st.text_input("Tema/Atividade", help="Descreva a atividade realizada no estágio")
                    duration_hours = st.number_input("Duração (horas)", min_value=0.5, max_value=24.0, value=2.0, step=0.5)
                
                with col2:
                    # Student selection (multi-select)
                    all_students = st.checkbox("Selecionar todos os alunos")
                    
                    if all_students:
                        selected_students = active_students["phone"].tolist()
                    else:
                        selected_students = st.multiselect(
                            "Selecione os alunos participantes:",
                            options=active_students["phone"].tolist(),
                            format_func=lambda x: f"{active_students.loc[active_students['phone'] == x, 'name'].values[0]} ({x})"
                        )
                
                notes = st.text_area("Observações")
                
                submit_button = st.form_submit_button("Registrar Estágio")
            
            if submit_button:
                if selected_students and topic and duration_hours > 0:
                    # Helper function to format student list
                    def format_students(students_str):
                        # Split string if it's already a string
                        if isinstance(students_str, str):
                            students_list = students_str.split(",")
                        else:
                            students_list = []
                        
                        # Add new students
                        for phone in selected_students:
                            if phone not in students_list:
                                students_list.append(phone)
                        
                        return ",".join(students_list)
                    
                    # Create new internship record
                    new_internship = {
                        "date": date.strftime("%Y-%m-%d"),
                        "topic": topic,
                        "duration_hours": duration_hours,
                        "students": ",".join(selected_students),
                        "notes": notes
                    }
                    
                    # Add to dataframe
                    if internships_df is None:
                        internships_df = pd.DataFrame([new_internship])
                    else:
                        internships_df = pd.concat([internships_df, pd.DataFrame([new_internship])], ignore_index=True)
                    
                    # Save to CSV
                    save_internships_data(internships_df)
                    
                    st.success(f"Estágio registrado com sucesso para {len(selected_students)} alunos!")
                    
                    # Show updated hours for each student
                    st.subheader("Horas de Estágio Atualizadas")
                    
                    update_table = []
                    
                    for phone in selected_students:
                        student_name = active_students.loc[active_students["phone"] == phone, "name"].values[0]
                        total_hours = get_student_internship_hours(internships_df, phone)
                        
                        update_table.append({
                            "Aluno": student_name,
                            "Telefone": phone,
                            "Total de Horas": f"{total_hours:.1f}h"
                        })
                    
                    st.table(pd.DataFrame(update_table))
                else:
                    if not selected_students:
                        st.error("Selecione pelo menos um aluno!")
                    if not topic:
                        st.error("Informe o tema do estágio!")
                    if duration_hours <= 0:
                        st.error("A duração deve ser maior que zero!")
        else:
            st.warning("Não há alunos ativos no sistema. Cadastre um aluno primeiro.")
    else:
        st.warning("Não há alunos cadastrados no sistema. Cadastre um aluno primeiro.")

with tab2:
    st.subheader("Listar Estágios")
    
    if internships_df is not None and not internships_df.empty:
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            # Date range filter
            date_range = st.date_input(
                "Filtrar por período",
                value=(
                    datetime.now() - timedelta(days=30),
                    datetime.now()
                ),
                key="date_range_filter"
            )
        
        with col2:
            # Topic filter
            all_topics = internships_df["topic"].unique().tolist()
            topic_filter = st.multiselect(
                "Filtrar por tema",
                options=["Todos"] + all_topics,
                default=["Todos"],
                key="topic_filter"
            )
        
        # Apply filters
        filtered_df = internships_df.copy()
        
        # Date filter
        if len(date_range) == 2:
            filtered_df["date"] = pd.to_datetime(filtered_df["date"])
            filtered_df = filtered_df[
                (filtered_df["date"] >= pd.Timestamp(date_range[0])) & 
                (filtered_df["date"] <= pd.Timestamp(date_range[1]))
            ]
        
        # Topic filter (only if "Todos" is not selected)
        if "Todos" not in topic_filter and topic_filter:
            filtered_df = filtered_df[filtered_df["topic"].isin(topic_filter)]
        
        # Display data
        if not filtered_df.empty:
            # Format date for display
            filtered_df["formatted_date"] = pd.to_datetime(filtered_df["date"]).dt.strftime('%d/%m/%Y')
            
            # Count students for each internship
            filtered_df["student_count"] = filtered_df["students"].apply(
                lambda x: len(x.split(",")) if isinstance(x, str) else 0
            )
            
            # Choose columns to display
            display_df = filtered_df[["formatted_date", "topic", "duration_hours", "student_count", "notes"]].copy()
            
            # Rename columns for display
            display_df.columns = ["Data", "Tema", "Duração (horas)", "Nº de Alunos", "Observações"]
            
            st.dataframe(display_df, use_container_width=True)
            
            # Summary section
            st.subheader("Resumo")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Estágios", len(filtered_df))
            
            with col2:
                total_hours = filtered_df["duration_hours"].sum()
                st.metric("Total de Horas", f"{total_hours:.1f}h")
            
            with col3:
                avg_students = filtered_df["student_count"].mean()
                st.metric("Média de Alunos por Estágio", f"{avg_students:.1f}")
            
            # Download option
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Baixar dados filtrados (CSV)",
                csv,
                "estagios.csv",
                "text/csv",
                key='download-csv'
            )
            
            # Option to view details of specific internship
            st.subheader("Detalhes do Estágio")
            
            selected_index = st.selectbox(
                "Selecione um estágio para ver detalhes",
                options=filtered_df.index,
                format_func=lambda x: f"{filtered_df.loc[x, 'formatted_date']} - {filtered_df.loc[x, 'topic']}"
            )
            
            if selected_index is not None:
                internship = filtered_df.loc[selected_index]
                
                st.write(f"**Data:** {internship['formatted_date']}")
                st.write(f"**Tema:** {internship['topic']}")
                st.write(f"**Duração:** {internship['duration_hours']} horas")
                st.write(f"**Observações:** {internship['notes']}")
                
                # Show list of students who attended
                student_phones = internship['students'].split(",") if isinstance(internship['students'], str) else []
                
                if student_phones and students_df is not None and not students_df.empty:
                    st.write("**Alunos Participantes:**")
                    
                    student_list = []
                    for phone in student_phones:
                        if phone in students_df["phone"].values:
                            student_name = students_df.loc[students_df["phone"] == phone, "name"].values[0]
                            student_list.append({
                                "Nome": student_name,
                                "Telefone": phone
                            })
                    
                    if student_list:
                        st.table(pd.DataFrame(student_list))
                
                # Option to edit this internship (TODO: implement edit functionality)
                if st.button("Editar este Estágio"):
                    st.warning("Funcionalidade de edição em desenvolvimento.")
                
                # Option to delete this internship
                if st.button("Excluir este Estágio"):
                    delete_confirmed = st.checkbox("Confirmar exclusão (esta ação não pode ser desfeita!)")
                    
                    if delete_confirmed:
                        # Remove internship from dataframe
                        internships_df = internships_df.drop(selected_index)
                        
                        # Save to CSV
                        save_internships_data(internships_df)
                        
                        st.success("Estágio excluído com sucesso!")
                        st.rerun()
        else:
            st.warning("Nenhum estágio encontrado com os filtros selecionados.")
    else:
        st.info("Não há estágios registrados.")

with tab3:
    st.subheader("Horas de Estágio por Aluno")
    
    if students_df is not None and not students_df.empty and internships_df is not None and not internships_df.empty:
        # Get active students
        active_students = get_active_students(students_df)
        
        if not active_students.empty:
            # Compute hours for each student
            student_hours = []
            
            for _, student in active_students.iterrows():
                phone = student["name"]
                name = student["name"]
                total_hours = get_student_internship_hours(internships_df, student["phone"])
                
                student_hours.append({
                    "Nome": name,
                    "Telefone": student["phone"],
                    "Total de Horas": total_hours
                })
            
            # Convert to dataframe for display
            student_hours_df = pd.DataFrame(student_hours)
            
            # Format hours
            student_hours_df["Total de Horas"] = student_hours_df["Total de Horas"].apply(lambda x: f"{x:.1f}h")
            
            # Sort by total hours (descending)
            student_hours_df = student_hours_df.sort_values("Total de Horas", ascending=False)
            
            # Display table
            st.dataframe(student_hours_df, use_container_width=True)
            
            # Option to view details for a specific student
            st.subheader("Detalhes por Aluno")
            
            selected_phone = st.selectbox(
                "Selecione um aluno para ver detalhes",
                options=active_students["phone"].tolist(),
                format_func=lambda x: f"{active_students.loc[active_students['phone'] == x, 'name'].values[0]} ({x})"
            )
            
            if selected_phone:
                student_name = active_students.loc[active_students["phone"] == selected_phone, "name"].values[0]
                
                st.write(f"**Aluno:** {student_name}")
                st.write(f"**Telefone:** {selected_phone}")
                
                total_hours = get_student_internship_hours(internships_df, selected_phone)
                st.write(f"**Total de Horas:** {total_hours:.1f}h")
                
                # Get internships for this student
                student_internships = []
                
                for _, internship in internships_df.iterrows():
                    student_list = internship["students"].split(",") if isinstance(internship["students"], str) else []
                    
                    if selected_phone in student_list:
                        student_internships.append({
                            "Data": pd.to_datetime(internship["date"]).strftime('%d/%m/%Y'),
                            "Tema": internship["topic"],
                            "Duração (horas)": internship["duration_hours"],
                            "Observações": internship["notes"]
                        })
                
                if student_internships:
                    st.subheader("Estágios Realizados")
                    
                    # Convert to dataframe and sort by date (most recent first)
                    student_internships_df = pd.DataFrame(student_internships)
                    student_internships_df["Data"] = pd.to_datetime(student_internships_df["Data"], format='%d/%m/%Y')
                    student_internships_df = student_internships_df.sort_values("Data", ascending=False)
                    student_internships_df["Data"] = student_internships_df["Data"].dt.strftime('%d/%m/%Y')
                    
                    st.dataframe(student_internships_df, use_container_width=True)
                else:
                    st.info("Este aluno ainda não participou de nenhum estágio.")
        else:
            st.warning("Não há alunos ativos no sistema.")
    else:
        st.info("Não há dados suficientes para mostrar horas de estágio.")

# Help section at bottom
with st.expander("Ajuda"):
    st.write("""
    ### Como gerenciar estágios
    
    - **Registrar Estágio**: Registre novos estágios, selecionando os alunos participantes.
    - **Listar Estágios**: Visualize, filtre e exporte todos os estágios registrados.
    - **Horas por Aluno**: Veja o total de horas de estágio acumuladas por cada aluno.
    
    ### Dicas
    
    - Você pode selecionar múltiplos alunos de uma vez ao registrar um estágio.
    - O tema do estágio deve ser descritivo para facilitar o acompanhamento.
    - A duração deve ser informada em horas, aceitando valores fracionados (ex: 2.5 horas).
    """)
