from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from bpa_v2.core.database.base_model import BaseModel


class StatusDocumento(enum.Enum):
    """Enumeração de status possíveis para documentos."""
    RASCUNHO = "rascunho"
    AGUARDANDO_ANALISE = "aguardando_analise"
    EM_ANALISE = "em_analise"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"
    CANCELADO = "cancelado"
    ARQUIVADO = "arquivado"


class TipoDocumento(BaseModel):
    """Modelo para tipos de documentos suportados pelo sistema."""
    
    __tablename__ = "tipos_documento"
    
    # Campos de identificação
    codigo = Column(String(20), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    
    # Campos de configuração
    descricao = Column(Text, nullable=True)
    prazo_dias = Column(Integer, default=30, nullable=False)
    requer_aprovacao = Column(Boolean, default=True, nullable=False)
    formato_arquivo = Column(String(10), nullable=True)  # pdf, docx, xlsx, etc.
    
    # Configurações de processamento
    schema_validacao = Column(JSON, nullable=True)
    workflow_id = Column(Integer, nullable=True)
    
    # Relacionamentos
    documentos = relationship("Documento", back_populates="tipo_documento")
    
    def __repr__(self):
        return f"<TipoDocumento {self.codigo} - {self.nome}>"


class Documento(BaseModel):
    """Modelo para documentos processados pelo sistema."""
    
    __tablename__ = "documentos"
    
    # Chaves estrangeiras
    tipo_documento_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=False)
    cadastrado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Campos de identificação
    numero = Column(String(50), unique=True, nullable=False)
    titulo = Column(String(200), nullable=False)
    
    # Metadados
    data_referencia = Column(DateTime, nullable=False)
    versao = Column(String(20), default="1.0", nullable=False)
    
    # Campos de processamento
    status = Column(Enum(StatusDocumento), default=StatusDocumento.RASCUNHO, nullable=False)
    data_envio = Column(DateTime, nullable=True)
    data_aprovacao = Column(DateTime, nullable=True)
    aprovado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Conteúdo e metadados
    conteudo_json = Column(JSON, nullable=True)
    observacoes = Column(Text, nullable=True)
    
    # Campos de arquivo
    arquivo_path = Column(String(255), nullable=True)
    arquivo_nome = Column(String(100), nullable=True)
    arquivo_hash = Column(String(64), nullable=True)
    arquivo_tamanho = Column(Integer, nullable=True)
    
    # Relacionamentos
    tipo_documento = relationship("TipoDocumento", back_populates="documentos")
    historico = relationship("HistoricoDocumento", back_populates="documento", cascade="all, delete-orphan")
    comentarios = relationship("ComentarioDocumento", back_populates="documento", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Documento {self.numero} - {self.titulo}>"


class HistoricoDocumento(BaseModel):
    """Modelo para histórico de alterações de documentos."""
    
    __tablename__ = "historico_documento"
    
    # Chave estrangeira
    documento_id = Column(Integer, ForeignKey("documentos.id"), nullable=False)
    
    # Campos de rastreamento
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario_nome = Column(String(100), nullable=True)
    
    # Campos do evento
    acao = Column(String(50), nullable=False)
    status_anterior = Column(Enum(StatusDocumento), nullable=True)
    status_novo = Column(Enum(StatusDocumento), nullable=True)
    
    # Detalhes
    descricao = Column(Text, nullable=True)
    metadados = Column(JSON, nullable=True)
    
    # Relacionamentos
    documento = relationship("Documento", back_populates="historico")
    
    def __repr__(self):
        return f"<HistoricoDocumento {self.acao} em {self.documento_id}>"


class ComentarioDocumento(BaseModel):
    """Modelo para comentários em documentos."""
    
    __tablename__ = "comentarios_documento"
    
    # Chaves estrangeiras
    documento_id = Column(Integer, ForeignKey("documentos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Campos do comentário
    texto = Column(Text, nullable=False)
    usuario_nome = Column(String(100), nullable=True)
    
    # Campos de controle
    interno = Column(Boolean, default=False, nullable=False)
    resolvido = Column(Boolean, default=False, nullable=False)
    
    # Relacionamentos
    documento = relationship("Documento", back_populates="comentarios")
    
    def __repr__(self):
        return f"<ComentarioDocumento {self.id} em {self.documento_id}>" 