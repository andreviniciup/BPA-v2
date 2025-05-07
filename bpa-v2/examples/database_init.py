import os
import sys
import logging

# Adiciona a raiz do projeto ao path para importação dos módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bpa_v2 import (
    # Configuração e logging
    setup_logging,
    load_config,
    
    # Banco de dados
    DatabaseConfig,
    init_db,
    
    # Modelos
    Usuario,
    TipoDocumento,
    Configuracao
)

# Configura o logging
logger = setup_logging(log_level=logging.INFO, module_name="database-init")

def main():
    """Função principal para inicialização do banco de dados."""
    try:
        # Carrega a configuração (poderia ser de um arquivo ou variáveis de ambiente)
        # Aqui estamos definindo diretamente para exemplo
        db_config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres", 
            database="bpa_v2",
            schema="public",
            echo=True  # Ativa o log de SQL para desenvolvimento
        )
        
        logger.info("Inicializando conexão com o banco de dados")
        db = init_db(db_config)
        
        # Cria as tabelas
        logger.info("Criando tabelas no banco de dados")
        db.create_all()
        
        # Cria uma sessão para operações
        session = db.create_session()
        
        # Exemplo: Verifica se já existe algum usuário admin
        usuarios_admin = session.query(Usuario).filter_by(role="admin").count()
        
        if usuarios_admin == 0:
            logger.info("Criando usuário administrador padrão")
            
            # Importa AuthService para criar hash da senha
            from bpa_v2 import AuthService
            auth_service = AuthService(secret_key="chave_secreta_para_tokens")
            
            # Cria o usuário admin
            admin = Usuario(
                nome="Administrador",
                username="admin",
                email="admin@example.com",
                senha_hash=auth_service.get_password_hash("admin123"),
                role="admin"
            )
            
            session.add(admin)
        
        # Exemplo: Cria alguns tipos de documento
        if session.query(TipoDocumento).count() == 0:
            logger.info("Criando tipos de documento padrão")
            
            tipos = [
                TipoDocumento(
                    codigo="BPA-I",
                    nome="Boletim de Produção Ambulatorial - I",
                    descricao="Registro individualizado",
                    prazo_dias=30,
                    formato_arquivo="csv"
                ),
                TipoDocumento(
                    codigo="BPA-C",
                    nome="Boletim de Produção Ambulatorial - Consolidado",
                    descricao="Registro consolidado",
                    prazo_dias=30,
                    formato_arquivo="csv"
                )
            ]
            
            for tipo in tipos:
                session.add(tipo)
        
        # Exemplo: Cria algumas configurações do sistema
        if session.query(Configuracao).count() == 0:
            logger.info("Criando configurações padrão do sistema")
            
            configs = [
                Configuracao(
                    chave="SISTEMA_NOME",
                    valor="BPA Manager V2",
                    descricao="Nome do sistema",
                    tipo="string",
                    grupo="sistema",
                    nivel="sistema"
                ),
                Configuracao(
                    chave="LIMITE_ARQUIVOS",
                    valor="10",
                    descricao="Limite de arquivos por lote",
                    tipo="int",
                    grupo="processamento",
                    nivel="sistema"
                ),
                Configuracao(
                    chave="PROC_AUTOMATICO",
                    valor="true",
                    descricao="Processar arquivos automaticamente após upload",
                    tipo="boolean",
                    grupo="processamento",
                    nivel="sistema"
                )
            ]
            
            for config in configs:
                session.add(config)
        
        # Confirma as alterações no banco
        session.commit()
        logger.info("Inicialização do banco de dados concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante a inicialização do banco de dados: {str(e)}")
        if 'session' in locals():
            session.rollback()
        sys.exit(1)
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main() 