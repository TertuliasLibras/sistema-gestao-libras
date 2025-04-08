import streamlit as st
import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    st.set_page_config(page_title="Configuração do Banco de Dados - Sistema de Gestão Libras")
    
    st.title("Configuração do Banco de Dados")
    st.write("Este utilitário irá configurar as tabelas necessárias no Supabase.")
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Definir credenciais do Supabase diretamente
    url = "https://apgjdytrovjdhnutkzqp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFwZ2pkeXRyb3ZqZGhudXRrenFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxMTkxMDcsImV4cCI6MjA1OTY5NTEwN30.mSmjrkoc5DaFAIwek5VThxX_GQwsWWGFif5rgDjoIr8"
    
    if url and key:
        st.success("Credenciais do Supabase carregadas com sucesso.")
    else:
        st.error("Credenciais do Supabase não encontradas no arquivo .env")
    
    # Exibir formato de URL para depuração
    st.info(f"URL configurada: {url}")
    if key:
        st.info(f"KEY formato: {key[:10]}...{key[-5:]}")
    else:
        st.error("Chave do Supabase não encontrada")
    
    # Verificar se a URL está no formato correto
    if url and (not url.startswith("https://") or ".supabase.co" not in url):
        st.warning("ATENÇÃO: O formato da URL parece incorreto. Deve ser algo como 'https://seu-projeto.supabase.co'")
    
    # Botão para confirmar a configuração
    if st.button("Configurar Banco de Dados"):
        with st.spinner("Configurando o banco de dados..."):
            try:
                # Mostrar exatamente o que está sendo usado
                st.write(f"Tentando conectar com URL: {url}")
                st.write("Se a URL acima não parecer correta, verifique se há espaços extras ou caracteres inválidos.")
                
                # Criar cliente Supabase
                try:
                    supabase = create_client(url, key)
                    st.success("Conexão com Supabase estabelecida com sucesso!")
                except Exception as e:
                    st.error(f"Erro específico na conexão: {str(e)}")
                    return
                
                # Verificar se conseguimos acessar as tabelas
                try:
                    # Testar acesso ao banco
                    test_result = supabase.table('students').select('*').limit(1).execute()
                    st.info("Teste de conexão realizado com sucesso!")
                except Exception as e:
                    st.warning(f"Aviso: Não foi possível acessar a tabela 'students'. Ela pode não existir ainda: {str(e)}")
                
                # Criar tabelas do banco de dados manualmente em vez de usar SQL
                # 1. Tabela students (estudantes) - Criar se não existir
                try:
                    # Verificar se a tabela existe
                    result = supabase.table('students').select('*').limit(1).execute()
                    st.success("Tabela 'students' já existe!")
                except Exception as e:
                    st.warning(f"A tabela 'students' pode não existir ainda: {str(e)}")
                    # Aqui normalmente criaríamos a tabela via SQL, mas isso não é possível
                    # com o cliente Python do Supabase

                # 2. Tabela payments (pagamentos) - Criar se não existir
                try:
                    result = supabase.table('payments').select('*').limit(1).execute()
                    st.success("Tabela 'payments' já existe!")
                except Exception as e:
                    st.warning(f"A tabela 'payments' pode não existir ainda: {str(e)}")

                # 3. Tabela internships (estágios) - Criar se não existir
                try:
                    result = supabase.table('internships').select('*').limit(1).execute()
                    st.success("Tabela 'internships' já existe!")
                except Exception as e:
                    st.warning(f"A tabela 'internships' pode não existir ainda: {str(e)}")

                # 4. Tabela users (usuários) - Criar se não existir
                try:
                    result = supabase.table('users').select('*').limit(1).execute()
                    st.success("Tabela 'users' já existe!")
                    
                    # Verificar se já existe um usuário admin
                    admin_check = supabase.table('users').select('*').eq('username', 'admin').execute()
                    if len(admin_check.data) == 0:
                        # Criar usuário admin
                        import hashlib
                        admin_hash = hashlib.md5('admin123'.encode()).hexdigest()
                        admin_data = {
                            'username': 'admin',
                            'password_hash': admin_hash,
                            'name': 'Administrador',
                            'level': 'admin'  # Usando apenas o campo level
                        }
                        supabase.table('users').insert(admin_data).execute()
                        st.success("Usuário admin criado com sucesso!")
                    else:
                        st.info("Usuário admin já existe!")
                except Exception as e:
                    st.warning(f"A tabela 'users' pode não existir ainda: {str(e)}")
                
                # Verificar se as tabelas foram criadas com sucesso
                tables_to_check = ['students', 'payments', 'internships', 'users']
                table_status = []
                
                for table in tables_to_check:
                    try:
                        result = supabase.table(table).select('*').limit(1).execute()
                        table_status.append(f"Tabela '{table}' está acessível!")
                    except Exception as e:
                        table_status.append(f"Tabela '{table}' não pôde ser acessada: {str(e)}")
                
                for status in table_status:
                    st.write(status)
                
                st.success("Verificação de tabelas concluída!")
                
            except Exception as e:
                st.error(f"Erro ao configurar o banco de dados: {e}")
    
    # Informações adicionais
    st.markdown("### Próximos Passos")
    st.write("Após a configuração do banco de dados, execute o aplicativo principal com:")
    st.code("streamlit run app.py")
    
    st.markdown("### Informações das Tabelas")
    st.markdown("""
    O script tenta verificar a existência das seguintes tabelas:
    
    1. **students** - Armazena informações dos estudantes
    2. **payments** - Armazena registros de pagamentos
    3. **internships** - Armazena registros de estágios
    4. **users** - Armazena usuários do sistema
    
    Um usuário administrador padrão será criado com as seguintes credenciais:
    - **Usuário**: admin
    - **Senha**: admin123
    
    Lembre-se de alterar a senha do administrador após o primeiro acesso por segurança.
    
    ### Importante
    Se as tabelas não existirem, você precisará criá-las manualmente através do painel de administração do Supabase.
    """)

if __name__ == "__main__":
    main()
