from sqlalchemy import create_engine, MetaData, Column, Integer, DateTime, String, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from datetime import datetime
import logging
from typing import Dict, Any, Optional, List

from bpa_v2.core.exceptions.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Configuração de conexão com o banco de dados."""
    
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        schema: str = "public",
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.schema = schema
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        
    @property
    def connection_string(self) -> str:
        """Retorna a string de conexão com o banco de dados."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class Database:
    """Gerenciador de conexão com o banco de dados."""
    
    _instance = None
    
    def __new__(cls, config: Optional[DatabaseConfig] = None):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        if self.initialized:
            return
            
        if config is None:
            raise ValueError("É necessário fornecer uma configuração de banco de dados")
            
        self.config = config
        self.metadata = MetaData(schema=config.schema)
        self.engine = create_engine(
            config.connection_string,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            echo=config.echo,
            poolclass=QueuePool
        )
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        self.Base = declarative_base(metadata=self.metadata)
        self.initialized = True
        
        logger.info(f"Conexão com banco de dados inicializada: {config.host}:{config.port}/{config.database}")
    
    def create_session(self):
        """Cria uma nova sessão de banco de dados."""
        return self.Session()
        
    def create_all(self):
        """Cria todas as tabelas definidas nos modelos."""
        self.Base.metadata.create_all(self.engine)
        logger.info("Tabelas criadas no banco de dados")
        
    def drop_all(self):
        """Remove todas as tabelas definidas nos modelos."""
        self.Base.metadata.drop_all(self.engine)
        logger.info("Tabelas removidas do banco de dados")
        
    def get_table_names(self) -> List[str]:
        """Retorna a lista de nomes de tabelas no schema."""
        return inspect(self.engine).get_table_names(schema=self.config.schema)
        
    def dispose(self):
        """Libera todas as conexões do pool."""
        self.engine.dispose()
        logger.info("Conexões liberadas")

# Classe base para modelos que inclui colunas padrão
class BaseModel:
    """Classe base para todos os modelos."""
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para um dicionário."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """Cria uma instância do modelo a partir de um dicionário."""
        return cls(**{k: v for k, v in data.items() if k in cls.__table__.columns.keys()})

# Função para inicializar o banco de dados
def init_db(config: DatabaseConfig) -> Database:
    """
    Inicializa a conexão com o banco de dados.
    
    Args:
        config: Configuração de conexão com o banco de dados
        
    Returns:
        Database: Instância do gerenciador de banco de dados
    """
    try:
        return Database(config)
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        raise DatabaseError(f"Falha na conexão com o banco de dados: {str(e)}") 