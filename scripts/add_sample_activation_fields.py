"""
Script para adicionar campos de ativação/desativação de amostras ao banco de dados.

Este script adiciona os seguintes campos à tabela base_listings:
- is_active: Boolean (True por padrão) - indica se a amostra está ativa
- deactivation_reason: Text - motivo da desativação da amostra

Uso:
    python scripts/add_sample_activation_fields.py
"""

import sys
import os

# Adiciona o diretório raiz ao path para permitir imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_activation_fields():
    """Adiciona os campos de ativação às amostras existentes."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Verificando se as colunas já existem...")
            
            # Verifica se as colunas já existem
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('base_listings')]
            
            if 'is_active' in columns and 'deactivation_reason' in columns:
                logger.info("As colunas já existem no banco de dados. Nenhuma alteração necessária.")
                return
            
            logger.info("Adicionando colunas ao banco de dados...")
            
            # Adiciona a coluna is_active se não existir
            if 'is_active' not in columns:
                logger.info("Adicionando coluna 'is_active'...")
                db.session.execute(text(
                    "ALTER TABLE base_listings ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"
                ))
                logger.info("Coluna 'is_active' adicionada com sucesso.")
            else:
                logger.info("Coluna 'is_active' já existe.")
            
            # Adiciona a coluna deactivation_reason se não existir
            if 'deactivation_reason' not in columns:
                logger.info("Adicionando coluna 'deactivation_reason'...")
                db.session.execute(text(
                    "ALTER TABLE base_listings ADD COLUMN deactivation_reason TEXT"
                ))
                logger.info("Coluna 'deactivation_reason' adicionada com sucesso.")
            else:
                logger.info("Coluna 'deactivation_reason' já existe.")
            
            db.session.commit()
            logger.info("Migração concluída com sucesso!")
            
            # Exibe estatísticas
            result = db.session.execute(text("SELECT COUNT(*) FROM base_listings"))
            total = result.scalar()
            logger.info(f"Total de amostras no banco: {total}")
            logger.info("Todas as amostras existentes foram marcadas como ativas por padrão.")
            
        except Exception as e:
            logger.error(f"Erro ao executar migração: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    logger.info("Iniciando migração do banco de dados...")
    logger.info("Adicionando campos de ativação/desativação de amostras...")
    add_activation_fields()
    logger.info("Processo concluído!")
