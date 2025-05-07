import os
import logging
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """Formatter para saída de logs em formato JSON."""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Adiciona informações de exceção se disponíveis
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Adiciona detalhes extras se disponíveis
        if hasattr(record, "details") and record.details:
            log_record["details"] = record.details
            
        return json.dumps(log_record)

def setup_logging(log_dir="logs", log_level=logging.INFO, module_name=None):
    """
    Configura o sistema de logging centralizado.
    
    Args:
        log_dir: Diretório onde os logs serão armazenados
        log_level: Nível de logging (default: INFO)
        module_name: Nome do módulo para identificar logs específicos
        
    Returns:
        logger: O objeto logger configurado
    """
    # Garante que o diretório de logs existe
    os.makedirs(log_dir, exist_ok=True)
    
    # Define o nome do logger e do arquivo
    logger_name = module_name or "bpa-v2"
    log_file = os.path.join(log_dir, f"{logger_name}.log")
    
    # Cria o logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # Remove handlers existentes para evitar duplicação em caso de reinicialização
    if logger.handlers:
        logger.handlers.clear()
    
    # Handler para saída no console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Handler para arquivo com rotação (máximo 10MB, 5 backups)
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_formatter = JsonFormatter()
    file_handler.setFormatter(file_formatter)
    
    # Adiciona os handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info(f"Logger '{logger_name}' configurado com sucesso. Nível: {logging.getLevelName(log_level)}")
    
    return logger 