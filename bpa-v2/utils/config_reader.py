import os
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, validator, Field
import json
import yaml
from pathlib import Path
import logging
from dotenv import load_dotenv

from bpa_v2.core.exceptions.exceptions import ConfigurationError

class BaseBPASettings(BaseSettings):
    """Classe base para configurações do sistema BPA."""
    
    # Configurações de Logs
    LOG_LEVEL: str = Field("INFO", description="Nível de log: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    LOG_DIR: str = Field("logs", description="Diretório onde os logs serão armazenados")
    
    # Configurações de Banco de Dados
    DB_HOST: str = Field(..., description="Host do banco de dados")
    DB_PORT: int = Field(5432, description="Porta do banco de dados")
    DB_NAME: str = Field(..., description="Nome do banco de dados")
    DB_USER: str = Field(..., description="Usuário do banco de dados")
    DB_PASSWORD: str = Field(..., description="Senha do banco de dados")
    DB_SCHEMA: str = Field("public", description="Schema do banco de dados")
    DB_POOL_SIZE: int = Field(5, description="Tamanho do pool de conexões")
    DB_MAX_OVERFLOW: int = Field(10, description="Máximo de conexões extras além do pool")
    
    # Configurações do Servidor
    HOST: str = Field("0.0.0.0", description="Host do servidor")
    PORT: int = Field(5000, description="Porta do servidor")
    DEBUG: bool = Field(False, description="Modo debug")
    
    # Configurações de Segurança
    SECRET_KEY: str = Field(..., description="Chave secreta para JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="Tempo de expiração do token em minutos")
    
    # Configurações específicas de arquivos
    FILE_UPLOAD_DIR: str = Field("uploads", description="Diretório para upload de arquivos")
    ALLOWED_EXTENSIONS: List[str] = Field(["zip", "txt"], description="Extensões de arquivo permitidas")
    MAX_CONTENT_LENGTH: int = Field(16 * 1024 * 1024, description="Tamanho máximo de arquivo (16MB)")
    
    # Configurações de cache
    CACHE_TYPE: str = Field("simple", description="Tipo de cache: simple, redis, etc.")
    CACHE_REDIS_URL: Optional[str] = Field(None, description="URL do Redis para cache")
    CACHE_DEFAULT_TIMEOUT: int = Field(300, description="Tempo padrão de expiração do cache em segundos")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Nível de log deve ser um dos seguintes: {', '.join(allowed_levels)}")
        return v.upper()
    
    @property
    def db_url(self) -> str:
        """Retorna a URL de conexão do banco de dados."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

def load_config(config_path: Optional[str] = None, env_file: Optional[str] = None) -> BaseBPASettings:
    """
    Carrega configurações a partir de arquivo e/ou variáveis de ambiente.
    
    Args:
        config_path: Caminho para arquivo de configuração (json ou yaml)
        env_file: Caminho para arquivo .env
        
    Returns:
        BaseBPASettings: Instância de configurações carregadas e validadas
    """
    try:
        # Carrega variáveis de ambiente
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
            
        # Carrega configurações do arquivo se especificado
        config_dict = {}
        if config_path:
            config_file = Path(config_path)
            if not config_file.exists():
                logging.warning(f"Arquivo de configuração não encontrado: {config_path}")
            else:
                if config_file.suffix.lower() in ['.json']:
                    with open(config_file, 'r') as f:
                        config_dict = json.load(f)
                elif config_file.suffix.lower() in ['.yaml', '.yml']:
                    with open(config_file, 'r') as f:
                        config_dict = yaml.safe_load(f)
                else:
                    logging.warning(f"Formato de arquivo de configuração não suportado: {config_path}")
        
        # Cria a instância de configurações
        return BaseBPASettings(**config_dict)
    except Exception as e:
        raise ConfigurationError(f"Erro ao carregar configurações: {str(e)}")

def get_module_config(module_name: str, config_base: Optional[BaseBPASettings] = None) -> Dict[str, Any]:
    """
    Filtra configurações específicas para um módulo.
    
    Args:
        module_name: Nome do módulo (ex: "data-injector", "bpa-gerador")
        config_base: Configurações base (opcional)
        
    Returns:
        Dict[str, Any]: Configurações específicas do módulo
    """
    if config_base is None:
        config_base = load_config()
        
    # Converte para dicionário
    config_dict = config_base.dict()
    
    # Filtra configurações com prefixo do módulo
    prefix = f"{module_name.upper().replace('-', '_')}_"
    module_config = {}
    
    # Extrai configurações específicas do módulo
    for key, value in config_dict.items():
        if key.startswith(prefix):
            # Remove o prefixo
            module_key = key[len(prefix):]
            module_config[module_key] = value
    
    # Adiciona configurações comuns
    common_keys = [
        "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_SCHEMA",
        "LOG_LEVEL", "LOG_DIR", "DEBUG"
    ]
    
    for key in common_keys:
        if key not in module_config and key in config_dict:
            module_config[key] = config_dict[key]
            
    return module_config 