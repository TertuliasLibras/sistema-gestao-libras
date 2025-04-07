import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from utils import (
    load_students_data, 
    load_internships_data, 
    save_internships_data,
    format_phone,
    get_active_students,
    get_student_internship_hours
)
from login import verificar_autenticacao

# Check authentication
if not verificar_autenticacao():
    st.error("Você precisa fazer login para acessar esta página.")
    st.stop()

# Set page config
st.set_page_config(
    page_title="Estágios - Sistema de Gestão",
    page_icon="⏱️",
    layout="wide"
)

# Display logo and title
col1, col2 = st.columns([1, 3])
with col1:
    st.image('assets/images/logo.svg', width=100)
with col2:
    st.title("Gestão de Estágios")

# Load data
students_df = load_students_data()
internships_df = load_internships_data()

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Registrar Estágio", "Visualizar Estágios", "Relatório de Estágios"])

with tab1:
    st.subheader("Registrar Novo Estágio")
    
    with st.form("internship_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Data do Estágio", datetime.now())
            topic = st.text_input("Tema/Assunto")
        
        with col2:
            duration_hours = st.number_input("Duração (horas)", min_value=0.5, step=0.5, format="%.1f")
        
        # Multi-select for students
        if not students_df.empty:
            # Get only active students
            active_students = get_active_students(students_df)
            
            if not active_students.empty:
                # Create a dictionary for display
                student_options = {
                    row['phone']: f"{row['name']} ({format_phone(row['phone'])})"
                    for _, row in active_students.iterrows()
                }
                
                # Multi-select for students
                selected_students = st.multiselect(
                    "Alunos Participantes",
                    options=list(student_options.keys()),
                    format_func=lambda x: student_options[x]
                )
                
                # Notes
                notes = st.text_area("Observações")
                
                # Submit button
                submit = st.form_submit_button("Registrar Estágio")
                
                if submit:
                    # Validate inputs
                    if not topic:
                        st.error("O tema do estágio é obrigatório.")
                    elif not selected_students:
                        st.error("Selecione pelo menos um aluno participante.")
                    else:
                        # Format student phones as comma-separated string
                        students_str = ",".join(selected_students)
                        
                        # Create new internship record
                        new_internship = {
                            'date': date,
                            'topic': topic,
                            'duration_hours': duration_hours,
                            'students': students_str,
                            'notes': notes
                        }
                        
                        # Add to dataframe
                        if internships_df.empty:
                            internships_df = pd.DataFrame([new_internship])
                        else:
                            internships_df = pd.concat([internships_df, pd.DataFrame([new_internship])], ignore_index=True)
                        
                        # Save data
                        if save_internships_data(internships_df):
                            st.success(f"Estágio {topic} registrado com sucesso!")
                            
                            # Show students and hours
                            def format_students(students_str):
                                student_phones = students_str.split(',')
                                student_names = []
                                for phone in student_phones:
                                    student_row = students_df[students_df['phone'] == phone]
                                    if not student_row.empty:
                                        student_names.append(student_row.iloc[0]['name'])
                                return ", ".join(student_names)
                            
                            students_display = format_students(students_str)
                            st.info(f"Alunos participantes: {students_display}")
                            st.info(f"Duração: {duration_hours} horas")
                        else:
                            st.error("Erro ao salvar dados do estágio.")
            else:
                st.warning("Não há alunos ativos para registrar estágios.")
                submit = st.form_submit_button("Registrar Estágio", disabled=True)
        else:
            st.warning("Não há alunos cadastrados para registrar estágios.")
            submit = st.form_submit_button("Registrar Estágio", disabled=True)

with tab2:
    st.subheader("Visualizar Estágios")
    
    if not internships_df.empty:
        # Convert date to datetime
        internships_df['date'] = pd.to_datetime(internships_df['date'])
        
        # Sort by date (most recent first)
        sorted_internships = internships_df.sort_values('date', ascending=False)
        
        # Format date for display
        sorted_internships['date_formatted'] = sorted_internships['date'].dt.strftime('%d/%m/%Y')
        
        # Display internships
        for i, internship in sorted_internships.iterrows():
            with st.expander(f"{internship['date_formatted']} - {internship['topic']} ({internship['duration_hours']}h)"):
                # Display internship details
                st.markdown(f"**Tema:** {internship['topic']}")
                st.markdown(f"**Data:** {internship['date_formatted']}")
                st.markdown(f"**Duração:** {internship['duration_hours']} horas")
                
                # Format and display participating students
                if 'students' in internship and internship['students']:
                    student_phones = str(internship['students']).split(',')
                    
                    if student_phones:
                        st.markdown("**Alunos Participantes:**")
                        
                        for phone in student_phones:
                            student_row = students_df[students_df['phone'] == phone]
                            
                            if not student_row.empty:
                                student = student_row.iloc[0]
                                st.markdown(f"- {student['name']} ({format_phone(phone)})")
                            else:
                                st.markdown(f"- Aluno não encontrado ({format_phone(phone)})")
                
                # Display notes
                if 'notes' in internship and pd.notna(internship['notes']) and internship['notes']:
                    st.markdown("**Observações:**")
                    st.markdown(internship['notes'])
                
                # Edit/Delete options
                col1, col2 = st.columns(2)
                
                # Edit internship
                with col1:
                    if st.button(f"Editar Estágio #{i}", key=f"edit_{i}"):
                        st.session_state['editing_internship'] = i
                
                # Delete internship
                with col2:
                    if st.button(f"Excluir Estágio #{i}", key=f"delete_{i}"):
                        # Confirm deletion
                        if st.button(f"Confirmar Exclusão #{i}", key=f"confirm_{i}"):
                            # Delete internship
                            internships_df = internships_df.drop(i)
                            
                            # Save data
                            if save_internships_data(internships_df):
                                st.success("Estágio excluído com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao excluir estágio.")
                
                # Show edit form if editing this internship
                if 'editing_internship' in st.session_state and st.session_state['editing_internship'] == i:
                    st.subheader("Editar Estágio")
                    
                    with st.form(f"edit_internship_form_{i}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_date = st.date_input(
                                "Data do Estágio",
                                pd.to_datetime(internship['date']).date()
                            )
                            edit_topic = st.text_input("Tema/Assunto", internship['topic'])
                        
                        with col2:
                            edit_duration = st.number_input(
                                "Duração (horas)",
                                min_value=0.5,
                                step=0.5,
                                value=float(internship['duration_hours']),
                                format="%.1f"
                            )
                        
                        # Current selected students
                        current_students = str(internship['students']).split(',')
                        
                        # Multi-select for students
                        if not students_df.empty:
                            # Get only active students
                            active_students = get_active_students(students_df)
                            
                            if not active_students.empty:
                                # Create a dictionary for display
                                student_options = {
                                    row['phone']: f"{row['name']} ({format_phone(row['phone'])})"
                                    for _, row in active_students.iterrows()
                                }
                                
                                # Add currently selected students who might be inactive now
                                for phone in current_students:
                                    if phone and phone not in student_options:
                                        student_row = students_df[students_df['phone'] == phone]
                                        if not student_row.empty:
                                            student_options[phone] = f"{student_row.iloc[0]['name']} ({format_phone(phone)})"
                                
                                # Multi-select for students
                                edit_students = st.multiselect(
                                    "Alunos Participantes",
                                    options=list(student_options.keys()),
                                    default=current_students,
                                    format_func=lambda x: student_options.get(x, f"Aluno não encontrado ({x})")
                                )
                        
                        # Notes
                        edit_notes = st.text_area(
                            "Observações",
                            internship['notes'] if pd.notna(internship['notes']) else ""
                        )
                        
                        # Submit button
                        update_submit = st.form_submit_button("Atualizar Estágio")
                        
                        if update_submit:
                            # Validate inputs
                            if not edit_topic:
                                st.error("O tema do estágio é obrigatório.")
                            elif not edit_students:
                                st.error("Selecione pelo menos um aluno participante.")
                            else:
                                # Format student phones as comma-separated string
                                edit_students_str = ",".join(edit_students)
                                
                                # Update internship record
                                internships_df.at[i, 'date'] = edit_date
                                internships_df.at[i, 'topic'] = edit_topic
                                internships_df.at[i, 'duration_hours'] = edit_duration
                                internships_df.at[i, 'students'] = edit_students_str
                                internships_df.at[i, 'notes'] = edit_notes
                                
                                # Save data
                                if save_internships_data(internships_df):
                                    st.success("Estágio atualizado com sucesso!")
                                    # Clear editing state
                                    del st.session_state['editing_internship']
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar estágio.")
                    
                    # Cancel button
                    if st.button("Cancelar Edição"):
                        # Clear editing state
                        del st.session_state['editing_internship']
                        st.rerun()
    else:
        st.info("Não há estágios registrados.")

with tab3:
    st.subheader("Relatório de Estágios")
    
    if not internships_df.empty and not students_df.empty:
        # Date range selection
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Data Inicial", value=datetime.now().replace(day=1, month=1))
        
        with col2:
            end_date = st.date_input("Data Final", value=datetime.now())
        
        # Convert dates to datetime
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        
        # Ensure date is datetime
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
            
            # Get unique students from all internships
            unique_students = set()
            for students_str in filtered_internships['students']:
                if pd.notna(students_str):
                    student_phones = str(students_str).split(',')
                    for phone in student_phones:
                        if phone:  # Ensure phone is not empty
                            unique_students.add(phone)
            
            # Student participation count
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
                
                # Display student participation
                st.subheader("Participação dos Alunos")
                
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
                
                # Export data option
                st.subheader("Exportar Dados")
                
                # Format internships for export
                export_internships = filtered_internships.copy()
                export_internships['date'] = export_internships['date'].dt.strftime('%d/%m/%Y')
                
                # Download button for internships
                csv_internships = export_internships.to_csv(index=False).encode('utf-8')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        "Baixar Dados de Estágios",
                        csv_internships,
                        f"estagios_{start_date.strftime('%Y%m%d')}_a_{end_date.strftime('%Y%m%d')}.csv",
                        "text/csv",
                        key='download-internships'
                    )
                
                # Download button for student participation
                csv_participation = participation_df.to_csv(index=False).encode('utf-8')
                
                with col2:
                    st.download_button(
                        "Baixar Dados de Participação",
                        csv_participation,
                        f"participacao_{start_date.strftime('%Y%m%d')}_a_{end_date.strftime('%Y%m%d')}.csv",
                        "text/csv",
                        key='download-participation'
                    )
            else:
                st.info("Não há dados de participação para exibir.")
        else:
            st.info("Não há estágios no período selecionado.")
    else:
        st.info("Não há dados suficientes para gerar relatório.")
