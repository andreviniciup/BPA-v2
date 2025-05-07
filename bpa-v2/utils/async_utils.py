import asyncio
import logging
from functools import wraps
from typing import Any, Callable, List, Dict, Optional, TypeVar, Coroutine, Union
import time
from concurrent.futures import ThreadPoolExecutor

from bpa_v2.core.exceptions.exceptions import ServiceUnavailableError

T = TypeVar('T')
logger = logging.getLogger(__name__)

def run_in_thread(func):
    """
    Decorator para executar uma função em uma thread separada.
    Útil para operações de I/O bloqueantes.
    
    Args:
        func: A função a ser executada em thread separada
        
    Returns:
        wrapper: Função decorada
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor,
                lambda: func(*args, **kwargs)
            )
    return wrapper

async def gather_with_concurrency(concurrency: int, *tasks):
    """
    Executa tarefas assíncronas com um limite de concorrência.
    
    Args:
        concurrency: Número máximo de tarefas simultâneas
        *tasks: Tarefas assíncronas a serem executadas
        
    Returns:
        List[Any]: Resultados das tarefas na ordem em que foram passadas
    """
    semaphore = asyncio.Semaphore(concurrency)
    
    async def sem_task(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*(sem_task(task) for task in tasks))

async def retry_async(
    coroutine_func: Callable[..., Coroutine], 
    *args, 
    max_retries: int = 3, 
    delay: float = 1.0, 
    backoff_factor: float = 2.0, 
    exceptions: tuple = (Exception,), 
    **kwargs
) -> Any:
    """
    Tenta executar uma coroutine com retentativas em caso de falha.
    
    Args:
        coroutine_func: A função de coroutine a ser executada
        *args: Argumentos para a função
        max_retries: Número máximo de tentativas
        delay: Tempo de espera inicial entre tentativas (segundos)
        backoff_factor: Fator de aumento do tempo de espera entre tentativas
        exceptions: Exceções que acionam novas tentativas
        **kwargs: Argumentos nomeados para a função
        
    Returns:
        Any: Resultado da função
        
    Raises:
        Exception: A última exceção encontrada após todas as tentativas
    """
    retry_count = 0
    current_delay = delay
    last_exception = None
    
    while retry_count <= max_retries:
        try:
            return await coroutine_func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            retry_count += 1
            
            if retry_count > max_retries:
                break
                
            logger.warning(
                f"Tentativa {retry_count}/{max_retries} falhou para {coroutine_func.__name__}: {str(e)}. "
                f"Aguardando {current_delay:.1f}s antes da próxima tentativa."
            )
            
            await asyncio.sleep(current_delay)
            current_delay *= backoff_factor
    
    logger.error(f"Todas as {max_retries} tentativas falharam para {coroutine_func.__name__}")
    if last_exception:
        raise last_exception
    raise ServiceUnavailableError("Falha após múltiplas tentativas")

def retry_sync(
    func: Callable, 
    *args, 
    max_retries: int = 3, 
    delay: float = 1.0, 
    backoff_factor: float = 2.0, 
    exceptions: tuple = (Exception,), 
    **kwargs
) -> Any:
    """
    Versão síncrona da função retry para funções não-assíncronas.
    
    Args:
        func: A função a ser executada
        *args: Argumentos para a função
        max_retries: Número máximo de tentativas
        delay: Tempo de espera inicial entre tentativas (segundos)
        backoff_factor: Fator de aumento do tempo de espera entre tentativas
        exceptions: Exceções que acionam novas tentativas
        **kwargs: Argumentos nomeados para a função
        
    Returns:
        Any: Resultado da função
        
    Raises:
        Exception: A última exceção encontrada após todas as tentativas
    """
    retry_count = 0
    current_delay = delay
    last_exception = None
    
    while retry_count <= max_retries:
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            retry_count += 1
            
            if retry_count > max_retries:
                break
                
            logger.warning(
                f"Tentativa {retry_count}/{max_retries} falhou para {func.__name__}: {str(e)}. "
                f"Aguardando {current_delay:.1f}s antes da próxima tentativa."
            )
            
            time.sleep(current_delay)
            current_delay *= backoff_factor
    
    logger.error(f"Todas as {max_retries} tentativas falharam para {func.__name__}")
    if last_exception:
        raise last_exception
    raise ServiceUnavailableError("Falha após múltiplas tentativas")

async def process_in_batches(
    items: List[Any], 
    batch_size: int, 
    process_func: Callable[[List[Any]], Coroutine[Any, Any, List[Any]]]
) -> List[Any]:
    """
    Processa uma lista de itens em lotes.
    
    Args:
        items: Lista de itens para processar
        batch_size: Tamanho do lote
        process_func: Função assíncrona que processa um lote
        
    Returns:
        List[Any]: Lista combinada de resultados
    """
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        logger.info(f"Processando lote de {len(batch)} itens ({i+1}-{i+len(batch)} de {len(items)})")
        
        batch_results = await process_func(batch)
        results.extend(batch_results)
        
    return results

async def timeout_after(seconds: float, coroutine: Coroutine, message: str = "Operação excedeu o tempo limite"):
    """
    Executa uma coroutine com timeout.
    
    Args:
        seconds: Tempo limite em segundos
        coroutine: A coroutine a ser executada
        message: Mensagem de erro em caso de timeout
        
    Returns:
        Any: Resultado da coroutine
        
    Raises:
        ServiceUnavailableError: Se a operação exceder o tempo limite
    """
    try:
        return await asyncio.wait_for(coroutine, timeout=seconds)
    except asyncio.TimeoutError:
        logger.error(f"Timeout após {seconds}s: {message}")
        raise ServiceUnavailableError(message) 