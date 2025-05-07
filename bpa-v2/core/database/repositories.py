from typing import List, Dict, Any, Optional, TypeVar, Generic, Type, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
import logging
from datetime import datetime

from bpa_v2.core.exceptions.exceptions import DatabaseError
from bpa_v2.core.database.base_model import BaseModel

T = TypeVar('T')
logger = logging.getLogger(__name__)

class Repository(Generic[T]):
    """
    Implementação genérica do padrão Repository.
    Fornece métodos comuns para operações CRUD.
    """
    
    def __init__(self, model_class: Type[T], session: Session):
        self.model_class = model_class
        self.session = session
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Busca uma entidade pelo ID.
        
        Args:
            entity_id: ID da entidade
            
        Returns:
            Optional[T]: Entidade encontrada ou None
        """
        try:
            return self.session.query(self.model_class).filter_by(id=entity_id).first()
        except Exception as e:
            logger.error(f"Erro ao buscar {self.model_class.__name__} por ID {entity_id}: {str(e)}")
            raise DatabaseError(f"Falha ao buscar {self.model_class.__name__}: {str(e)}")
    
    def get_all(self) -> List[T]:
        """
        Retorna todas as entidades.
        
        Returns:
            List[T]: Lista de entidades
        """
        try:
            return self.session.query(self.model_class).all()
        except Exception as e:
            logger.error(f"Erro ao buscar todas as entidades {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Falha ao listar {self.model_class.__name__}: {str(e)}")
    
    def get_by_filters(self, 
                     filters: Dict[str, Any], 
                     order_by: Optional[str] = None,
                     limit: Optional[int] = None,
                     offset: Optional[int] = None,
                     descending: bool = False) -> List[T]:
        """
        Busca entidades com filtros.
        
        Args:
            filters: Dicionário de filtros (campo=valor)
            order_by: Campo para ordenação
            limit: Limite de resultados
            offset: Deslocamento para paginação
            descending: Se a ordenação deve ser decrescente
            
        Returns:
            List[T]: Lista de entidades que correspondem aos filtros
        """
        try:
            query = self.session.query(self.model_class)
            
            # Aplicar filtros
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        conditions.append(getattr(self.model_class, key).in_(value))
                    else:
                        conditions.append(getattr(self.model_class, key) == value)
                query = query.filter(and_(*conditions))
            
            # Aplicar ordenação
            if order_by:
                order_func = desc if descending else asc
                query = query.order_by(order_func(getattr(self.model_class, order_by)))
            
            # Aplicar limite e deslocamento
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            return query.all()
        except Exception as e:
            logger.error(f"Erro ao buscar {self.model_class.__name__} com filtros: {str(e)}")
            raise DatabaseError(f"Falha ao filtrar {self.model_class.__name__}: {str(e)}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Conta o número de entidades que correspondem aos filtros.
        
        Args:
            filters: Dicionário de filtros (campo=valor)
            
        Returns:
            int: Número de entidades
        """
        try:
            query = self.session.query(func.count(self.model_class.id))
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        conditions.append(getattr(self.model_class, key).in_(value))
                    else:
                        conditions.append(getattr(self.model_class, key) == value)
                query = query.filter(and_(*conditions))
            
            return query.scalar()
        except Exception as e:
            logger.error(f"Erro ao contar {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Falha ao contar {self.model_class.__name__}: {str(e)}")
    
    def create(self, data: Union[Dict[str, Any], T]) -> T:
        """
        Cria uma nova entidade.
        
        Args:
            data: Dicionário com dados ou instância da entidade
            
        Returns:
            T: Entidade criada
        """
        try:
            if isinstance(data, dict):
                entity = self.model_class(**data)
            else:
                entity = data
            
            self.session.add(entity)
            self.session.flush()
            self.session.refresh(entity)
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao criar {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Falha ao criar {self.model_class.__name__}: {str(e)}")
    
    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """
        Cria múltiplas entidades em lote.
        
        Args:
            items: Lista de dicionários com dados das entidades
            
        Returns:
            List[T]: Lista de entidades criadas
        """
        entities = []
        try:
            for item in items:
                entity = self.model_class(**item)
                self.session.add(entity)
                entities.append(entity)
            
            self.session.flush()
            for entity in entities:
                self.session.refresh(entity)
            
            return entities
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao criar em lote {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Falha ao criar em lote {self.model_class.__name__}: {str(e)}")
    
    def update(self, entity_id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Atualiza uma entidade existente.
        
        Args:
            entity_id: ID da entidade
            data: Dicionário com dados a atualizar
            
        Returns:
            Optional[T]: Entidade atualizada ou None se não encontrada
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                return None
            
            # Atualiza apenas os campos fornecidos
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            # Atualiza o timestamp de atualização se for um BaseModel
            if isinstance(entity, BaseModel):
                entity.updated_at = datetime.utcnow()
            
            self.session.flush()
            self.session.refresh(entity)
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao atualizar {self.model_class.__name__} ID {entity_id}: {str(e)}")
            raise DatabaseError(f"Falha ao atualizar {self.model_class.__name__}: {str(e)}")
    
    def delete(self, entity_id: int) -> bool:
        """
        Remove uma entidade pelo ID.
        
        Args:
            entity_id: ID da entidade
            
        Returns:
            bool: True se removida com sucesso, False se não encontrada
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                return False
            
            self.session.delete(entity)
            self.session.flush()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao remover {self.model_class.__name__} ID {entity_id}: {str(e)}")
            raise DatabaseError(f"Falha ao remover {self.model_class.__name__}: {str(e)}")
    
    def delete_many(self, filter_dict: Dict[str, Any]) -> int:
        """
        Remove múltiplas entidades com base em filtros.
        
        Args:
            filter_dict: Dicionário de filtros (campo=valor)
            
        Returns:
            int: Número de entidades removidas
        """
        try:
            conditions = []
            for key, value in filter_dict.items():
                if isinstance(value, list):
                    conditions.append(getattr(self.model_class, key).in_(value))
                else:
                    conditions.append(getattr(self.model_class, key) == value)
            
            query = self.session.query(self.model_class).filter(and_(*conditions))
            count = query.count()
            query.delete(synchronize_session=False)
            self.session.flush()
            return count
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao remover múltiplos {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Falha ao remover múltiplos {self.model_class.__name__}: {str(e)}")
    
    def upsert(self, 
              unique_fields: List[str], 
              data: Dict[str, Any]) -> Tuple[T, bool]:
        """
        Insere ou atualiza uma entidade com base em campos únicos.
        
        Args:
            unique_fields: Lista de campos que identificam unicamente a entidade
            data: Dicionário com dados da entidade
            
        Returns:
            Tuple[T, bool]: Tupla com a entidade e um booleano indicando se foi criada (True) ou atualizada (False)
        """
        try:
            # Constrói filtro com campos únicos
            filters = {field: data[field] for field in unique_fields if field in data}
            
            # Verifica se a entidade existe
            existing = self.get_by_filters(filters)
            
            if existing:
                # Atualiza se existir
                entity = existing[0]
                for key, value in data.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)
                
                # Atualiza o timestamp de atualização se for um BaseModel
                if isinstance(entity, BaseModel):
                    entity.updated_at = datetime.utcnow()
                
                self.session.flush()
                self.session.refresh(entity)
                return entity, False
            else:
                # Cria se não existir
                entity = self.create(data)
                return entity, True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao upsert {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Falha ao upsert {self.model_class.__name__}: {str(e)}")
    
    def bulk_upsert(self, 
                   unique_fields: List[str], 
                   items: List[Dict[str, Any]]) -> Tuple[List[T], int, int]:
        """
        Insere ou atualiza múltiplas entidades com base em campos únicos.
        
        Args:
            unique_fields: Lista de campos que identificam unicamente as entidades
            items: Lista de dicionários com dados das entidades
            
        Returns:
            Tuple[List[T], int, int]: Tupla com a lista de entidades, número de criadas e número de atualizadas
        """
        entities = []
        created = 0
        updated = 0
        
        try:
            for item in items:
                entity, is_new = self.upsert(unique_fields, item)
                entities.append(entity)
                
                if is_new:
                    created += 1
                else:
                    updated += 1
            
            return entities, created, updated
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao bulk upsert {self.model_class.__name__}: {str(e)}")
            raise DatabaseError(f"Falha ao bulk upsert {self.model_class.__name__}: {str(e)}")
    
    def commit(self):
        """Confirma as alterações pendentes na sessão."""
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erro ao confirmar transação: {str(e)}")
            raise DatabaseError(f"Falha ao confirmar transação: {str(e)}")
    
    def rollback(self):
        """Reverte as alterações pendentes na sessão."""
        try:
            self.session.rollback()
        except Exception as e:
            logger.error(f"Erro ao reverter transação: {str(e)}")
            raise DatabaseError(f"Falha ao reverter transação: {str(e)}")
    
    def begin_transaction(self):
        """Inicia uma nova transação."""
        try:
            self.session.begin_nested()
        except Exception as e:
            logger.error(f"Erro ao iniciar transação: {str(e)}")
            raise DatabaseError(f"Falha ao iniciar transação: {str(e)}")
    
    def close(self):
        """Fecha a sessão."""
        try:
            self.session.close()
        except Exception as e:
            logger.error(f"Erro ao fechar sessão: {str(e)}")
            raise DatabaseError(f"Falha ao fechar sessão: {str(e)}") 