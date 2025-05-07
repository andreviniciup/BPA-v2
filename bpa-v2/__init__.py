__version__ = "0.1.0"

from bpa_v2.core.exceptions.exceptions import (
    BPAException, 
    ValidationError, 
    DatabaseError, 
    FileProcessingError, 
    AuthenticationError, 
    ConfigurationError,
    ServiceUnavailableError
)

from bpa_v2.core.logging.logger_config import setup_logging
from bpa_v2.utils.config_reader import load_config, get_module_config, BaseBPASettings
from bpa_v2.core.database.base_model import Database, BaseModel, DatabaseConfig, init_db
from bpa_v2.core.database.repositories import Repository
from bpa_v2.core.auth.auth_service import AuthService, UserInfo

# Importação dos modelos
from bpa_v2.core.models import (
    # Modelos básicos
    Usuario,
    TokenAcesso,
    LogAuditoria,
    Configuracao,
    
    # Modelos de documentos
    StatusDocumento,
    TipoDocumento,
    Documento,
    HistoricoDocumento,
    ComentarioDocumento
)

__all__ = [
    # Version
    "__version__",
    
    # Exceptions
    "BPAException",
    "ValidationError",
    "DatabaseError",
    "FileProcessingError",
    "AuthenticationError",
    "ConfigurationError",
    "ServiceUnavailableError",
    
    # Logger
    "setup_logging",
    
    # Config
    "load_config",
    "get_module_config",
    "BaseBPASettings",
    
    # Database
    "Database",
    "BaseModel",
    "DatabaseConfig",
    "init_db",
    "Repository",
    
    # Auth
    "AuthService",
    "UserInfo",
    
    # Modelos básicos
    "Usuario",
    "TokenAcesso",
    "LogAuditoria",
    "Configuracao",
    
    # Modelos de documentos
    "StatusDocumento",
    "TipoDocumento",
    "Documento",
    "HistoricoDocumento",
    "ComentarioDocumento",
] 