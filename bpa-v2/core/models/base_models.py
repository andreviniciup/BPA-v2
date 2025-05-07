from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from bpa_v2.core.database.base_model import BaseModel

class Usuario(BaseModel):
    """Modelo para usuários do sistema."""
    
    __tablename__ = "usuarios"
    
    # Campos básicos
    nome = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    
    # Campos de acesso e perfil
    role = Column(String(50), nullable=False, default="usuario")
    ultimo_acesso = Column(DateTime, nullable=True)
    
    # Campos de auditoria
    criado_por = Column(Integer, nullable=True)
    
    # Relacionamentos
    tokens = relationship("TokenAcesso", back_populates="usuario", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Usuario {self.username}>"


class TokenAcesso(BaseModel):
    """Modelo para tokens de acesso e refresh tokens."""
    
    __tablename__ = "tokens_acesso"
    
    # Chave estrangeira
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Campos do token
    token_hash = Column(String(255), nullable=False)
    tipo = Column(String(20), nullable=False, default="access")  # access ou refresh
    expiracao = Column(DateTime, nullable=False)
    revogado = Column(Boolean, default=False, nullable=False)
    dispositivo = Column(String(100), nullable=True)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="tokens")
    
    def __repr__(self):
        return f"<TokenAcesso {self.tipo} para {self.usuario_id}>"


class LogAuditoria(BaseModel):
    """Modelo para registros de auditoria do sistema."""
    
    __tablename__ = "logs_auditoria"
    
    # Campos de identificação
    usuario_id = Column(Integer, nullable=True)
    username = Column(String(50), nullable=True)
    
    # Campos de evento
    acao = Column(String(50), nullable=False)
    recurso = Column(String(100), nullable=False)
    recurso_id = Column(String(50), nullable=True)
    
    # Detalhes da ação
    descricao = Column(Text, nullable=True)
    dados_anteriores = Column(Text, nullable=True)
    dados_novos = Column(Text, nullable=True)
    
    # Informações de contexto
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<LogAuditoria {self.acao} em {self.recurso} por {self.username}>"


class Configuracao(BaseModel):
    """Modelo para configurações do sistema."""
    
    __tablename__ = "configuracoes"
    
    # Campos de configuração
    chave = Column(String(100), unique=True, nullable=False)
    valor = Column(Text, nullable=True)
    descricao = Column(String(255), nullable=True)
    tipo = Column(String(20), nullable=False, default="string")
    
    # Metadados
    grupo = Column(String(100), nullable=True)
    nivel = Column(String(20), default="sistema", nullable=False)  # sistema, modulo, usuario
    editavel = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<Configuracao {self.chave}={self.valor[:20]}>"
    
    def get_valor_tipado(self):
        """Retorna o valor convertido para o tipo correto."""
        if self.valor is None:
            return None
            
        if self.tipo == "int":
            return int(self.valor)
        elif self.tipo == "float":
            return float(self.valor)
        elif self.tipo == "boolean":
            return self.valor.lower() in ("true", "1", "sim", "yes")
        elif self.tipo == "json":
            import json
            return json.loads(self.valor)
        else:
            return self.valor 