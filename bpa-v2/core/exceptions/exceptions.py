
class BPAException(Exception):
    """Classe base para todas as exceções do sistema BPA."""
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(BPAException):
    """Exceção para erros de validação."""
    def __init__(self, message, details=None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)

class DatabaseError(BPAException):
    """Exceção para erros relacionados ao banco de dados."""
    def __init__(self, message, details=None):
        super().__init__(message, code="DATABASE_ERROR", details=details)

class FileProcessingError(BPAException):
    """Exceção para erros no processamento de arquivos."""
    def __init__(self, message, details=None):
        super().__init__(message, code="FILE_PROCESSING_ERROR", details=details)

class AuthenticationError(BPAException):
    """Exceção para erros de autenticação."""
    def __init__(self, message, details=None):
        super().__init__(message, code="AUTHENTICATION_ERROR", details=details)

class ConfigurationError(BPAException):
    """Exceção para erros de configuração."""
    def __init__(self, message, details=None):
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)

class ServiceUnavailableError(BPAException):
    """Exceção para serviços indisponíveis."""
    def __init__(self, message, details=None):
        super().__init__(message, code="SERVICE_UNAVAILABLE", details=details)

class ErrorHandler:
    """Classe para tratamento centralizado de erros."""
    
    @staticmethod
    def handle_exception(exception, log_error=True, logger=None):
        """
        Trata uma exceção de forma padronizada.
        
        Args:
            exception: A exceção a ser tratada
            log_error: Se deve registrar o erro no log
            logger: O logger a ser utilizado
            
        Returns:
            dict: Detalhes do erro em formato padronizado
        """
        if isinstance(exception, BPAException):
            error_data = {
                "code": exception.code,
                "message": exception.message,
                "details": exception.details
            }
        else:
            error_data = {
                "code": "UNKNOWN_ERROR",
                "message": str(exception),
                "details": {}
            }
            
        if log_error and logger:
            logger.error(f"Erro: {error_data['code']} - {error_data['message']}", 
                        extra={"details": error_data["details"]})
            
        return error_data 