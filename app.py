            # Students with overdue payments
            st.subheader("Alunos com Pagamentos Atrasados")

            if not overdue_payments.empty:
                # Verificar colunas disponíveis e selecionar apenas as que existem
                available_columns = []
                column_config = {}
                
                # Definir quais colunas exibir (apenas se existirem)
                if 'name' in overdue_payments.columns:
                    available_columns.append('name')
                    column_config['name'] = 'Nome'
                
                if 'phone' in overdue_payments.columns:
                    available_columns.append('phone')
                    column_config['phone'] = 'Telefone'
                
                if 'email' in overdue_payments.columns:
                    available_columns.append('email')
                    column_config['email'] = 'Email'
                
                if 'monthly_fee' in overdue_payments.columns:
                    available_columns.append('monthly_fee')
                    column_config['monthly_fee'] = 'Mensalidade'
                
                if 'last_due_date' in overdue_payments.columns:
                    available_columns.append('last_due_date')
                    column_config['last_due_date'] = 'Último Vencimento'
                
                if 'days_overdue' in overdue_payments.columns:
                    available_columns.append('days_overdue')
                    column_config['days_overdue'] = 'Dias em Atraso'
                
                # Verificar se temos colunas para exibir
                if available_columns:
                    st.dataframe(
                        overdue_payments[available_columns], 
                        use_container_width=True,
                        column_config=column_config
                    )
                else:
                    st.warning("Não foi possível exibir dados de pagamentos atrasados: formato de dados inválido.")
            else:
                st.success("Não há pagamentos atrasados no momento.")
