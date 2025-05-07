import os
import zipfile
import io
from typing import List, Dict, Any, BinaryIO, Optional, Union
import csv
import tempfile

from bpa_v2.core.exceptions.exceptions import FileProcessingError

def extract_zip_file(zip_data: Union[str, bytes, BinaryIO], target_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Extrai um arquivo ZIP para um diretório de destino ou para um diretório temporário.
    
    Args:
        zip_data: Caminho do arquivo ZIP ou objeto de arquivo em memória
        target_dir: Diretório de destino (opcional)
        
    Returns:
        Dict[str, str]: Mapeamento de nomes de arquivos para caminhos extraídos
    """
    try:
        if target_dir is None:
            target_dir = tempfile.mkdtemp()
        
        extracted_files = {}
        
        # Se zip_data for string, assume que é o caminho para um arquivo
        if isinstance(zip_data, str):
            if not os.path.exists(zip_data):
                raise FileProcessingError(f"Arquivo ZIP não encontrado: {zip_data}")
            with zipfile.ZipFile(zip_data, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
                extracted_files = {f: os.path.join(target_dir, f) for f in zip_ref.namelist()}
        else:
            # Caso contrário, assume que é um objeto de arquivo em memória
            with zipfile.ZipFile(zip_data, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
                extracted_files = {f: os.path.join(target_dir, f) for f in zip_ref.namelist()}
        
        return extracted_files
    except zipfile.BadZipFile:
        raise FileProcessingError("Arquivo ZIP inválido ou corrompido")
    except Exception as e:
        raise FileProcessingError(f"Erro ao extrair arquivo ZIP: {str(e)}")

def create_zip_file(files_to_zip: Dict[str, str], output_path: Optional[str] = None) -> Union[str, bytes]:
    """
    Cria um arquivo ZIP contendo os arquivos especificados.
    
    Args:
        files_to_zip: Dicionário mapeando nomes de arquivo dentro do ZIP para caminhos locais
        output_path: Caminho onde o arquivo ZIP será salvo (opcional)
        
    Returns:
        Union[str, bytes]: Caminho do arquivo ZIP criado ou bytes se output_path for None
    """
    try:
        if output_path:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for zip_path, local_path in files_to_zip.items():
                    if os.path.exists(local_path):
                        zip_file.write(local_path, zip_path)
                    else:
                        raise FileProcessingError(f"Arquivo não encontrado: {local_path}")
            return output_path
        else:
            # Criar ZIP em memória
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for zip_path, local_path in files_to_zip.items():
                    if os.path.exists(local_path):
                        zip_file.write(local_path, zip_path)
                    else:
                        raise FileProcessingError(f"Arquivo não encontrado: {local_path}")
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
    except Exception as e:
        raise FileProcessingError(f"Erro ao criar arquivo ZIP: {str(e)}")

def read_fixed_width_file(file_path: str, column_specs: List[Dict[str, Any]], 
                         encoding: str = 'utf-8', skip_header: bool = False) -> List[Dict[str, str]]:
    """
    Lê um arquivo de largura fixa e retorna os dados como lista de dicionários.
    
    Args:
        file_path: Caminho para o arquivo
        column_specs: Especificações das colunas com nome, posição inicial e tamanho
        encoding: Codificação do arquivo
        skip_header: Se deve pular a primeira linha (cabeçalho)
        
    Returns:
        List[Dict[str, str]]: Lista de registros como dicionários
    """
    try:
        results = []
        
        with open(file_path, 'r', encoding=encoding) as file:
            if skip_header:
                next(file)
                
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                    
                record = {}
                for spec in column_specs:
                    start = spec['start'] - 1  # Ajustar para índice base 0
                    end = start + spec['length']
                    
                    # Verifica se a linha é longa o suficiente
                    if len(line) >= end:
                        value = line[start:end].strip()
                        record[spec['name']] = value
                    else:
                        # Se a linha for mais curta que o esperado
                        record[spec['name']] = ''
                        
                results.append(record)
                
        return results
    except Exception as e:
        raise FileProcessingError(f"Erro ao processar arquivo de largura fixa {file_path}: {str(e)}")

def write_fixed_width_file(data: List[Dict[str, Any]], file_path: str, 
                          column_specs: List[Dict[str, Any]], encoding: str = 'utf-8',
                          include_header: bool = False) -> str:
    """
    Escreve dados em um arquivo de largura fixa.
    
    Args:
        data: Lista de dicionários contendo os dados
        file_path: Caminho onde o arquivo será salvo
        column_specs: Especificações das colunas
        encoding: Codificação do arquivo
        include_header: Se deve incluir linha de cabeçalho
        
    Returns:
        str: Caminho do arquivo salvo
    """
    try:
        with open(file_path, 'w', encoding=encoding, newline='') as file:
            # Escreve cabeçalho se necessário
            if include_header:
                header_line = ""
                for spec in column_specs:
                    header_name = spec.get('header', spec['name'])
                    header_line += header_name.ljust(spec['length'])[:spec['length']]
                file.write(header_line + '\n')
            
            # Escreve os dados
            for record in data:
                line = ""
                for spec in column_specs:
                    field_name = spec['name']
                    field_value = str(record.get(field_name, "")).ljust(spec['length'])
                    line += field_value[:spec['length']]
                file.write(line + '\n')
                
        return file_path
    except Exception as e:
        raise FileProcessingError(f"Erro ao escrever arquivo de largura fixa {file_path}: {str(e)}")

def is_valid_file_extension(file_path: str, allowed_extensions: List[str]) -> bool:
    """
    Verifica se a extensão do arquivo é válida.
    
    Args:
        file_path: Caminho do arquivo
        allowed_extensions: Lista de extensões permitidas (sem o ponto)
        
    Returns:
        bool: True se a extensão for válida
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower()[1:] in [e.lower() for e in allowed_extensions]

def get_file_size(file_path: str) -> int:
    """
    Retorna o tamanho do arquivo em bytes.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        int: Tamanho do arquivo em bytes
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        raise FileProcessingError(f"Erro ao obter tamanho do arquivo {file_path}: {str(e)}")

def read_csv_file(file_path: str, delimiter: str = ',', encoding: str = 'utf-8') -> List[Dict[str, str]]:
    """
    Lê um arquivo CSV e retorna os dados como lista de dicionários.
    
    Args:
        file_path: Caminho para o arquivo CSV
        delimiter: Caractere delimitador
        encoding: Codificação do arquivo
        
    Returns:
        List[Dict[str, str]]: Lista de registros como dicionários
    """
    try:
        results = []
        with open(file_path, 'r', encoding=encoding, newline='') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            for row in reader:
                results.append(dict(row))
        return results
    except Exception as e:
        raise FileProcessingError(f"Erro ao ler arquivo CSV {file_path}: {str(e)}")

def ensure_directory(directory_path: str) -> str:
    """
    Garante que um diretório exista, criando-o se necessário.
    
    Args:
        directory_path: Caminho do diretório
        
    Returns:
        str: Caminho do diretório
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return directory_path
    except Exception as e:
        raise FileProcessingError(f"Erro ao criar diretório {directory_path}: {str(e)}")

def list_files(directory_path: str, file_extension: Optional[str] = None) -> List[str]:
    """
    Lista arquivos em um diretório, opcionalmente filtrando por extensão.
    
    Args:
        directory_path: Caminho do diretório
        file_extension: Extensão para filtrar (opcional)
        
    Returns:
        List[str]: Lista de caminhos de arquivos
    """
    try:
        if not os.path.exists(directory_path):
            return []
            
        files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) 
                if os.path.isfile(os.path.join(directory_path, f))]
                
        if file_extension:
            ext = file_extension if file_extension.startswith('.') else f'.{file_extension}'
            files = [f for f in files if f.lower().endswith(ext.lower())]
            
        return files
    except Exception as e:
        raise FileProcessingError(f"Erro ao listar arquivos no diretório {directory_path}: {str(e)}") 