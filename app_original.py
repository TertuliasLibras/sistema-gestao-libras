import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from utils import (
    load_students_data,
    load_payments_data,
    load_internships_data,
    format_currency,
    calculate_monthly_revenue,
    get_overdue_payments,
    get_active_students
)

# Verificar se estamos no Streamlit Cloud
IS_STREAMLIT_CLOUD = os.environ.get('STREAMLIT_SHARING_MODE') == 'streamlit' or os.environ.get('IS_STREAMLIT_CLOUD') == 'true'

# Importar módulo de login adequado
try:
    if IS_STREAMLIT_CLOUD:
        from login_fallback import verificar_autenticacao, mostrar_pagina_login, logout
    else:
        from login import verificar_autenticacao, mostrar_pagina_login, logout
except ImportError:
    from login_fallback import verificar_autenticacao, mostrar_pagina_login, logout

# Configuração da página
st.set_page_config(
    page_title="Tertúlia Libras - Sistema de Gestão",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Verificar autenticação
if not verificar_autenticacao():
    mostrar_pagina_login()
else:
    # Dashboard
    st.title("Dashboard")
    
    st.markdown("Esta é uma versão de demonstração. Os dados são simulados para fins de teste no ambiente Cloud.")
    
    # Botão de logout
    if st.sidebar.button("Sair"):
        logout()
        st.rerun()
