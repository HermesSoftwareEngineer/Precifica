"""
Script para adicionar campo de depreciação às avaliações.

Este script adiciona o campo depreciation à tabela evaluations:
- depreciation: Float (0.0 por padrão) - porcentagem de depreciação (0-100)

Uso:
    python scripts/add_depreciation_field.py
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

def add_depreciation_field():
    """Adiciona o campo de depreciação às avaliações existentes."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Verificando se a coluna já existe...")
            
            # Verifica se a coluna já existe
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('evaluations')]
            
            if 'depreciation' in columns:
                logger.info("A coluna 'depreciation' já existe no banco de dados. Nenhuma alteração necessária.")
                return
            
            logger.info("Adicionando coluna 'depreciation' ao banco de dados...")
            
            # Adiciona a coluna depreciation
            db.session.execute(text(
                "ALTER TABLE evaluations ADD COLUMN depreciation FLOAT NOT NULL DEFAULT 0.0"
            ))
            
            db.session.commit()
            logger.info("Coluna 'depreciation' adicionada com sucesso.")
            
            # Exibe estatísticas
            result = db.session.execute(text("SELECT COUNT(*) FROM evaluations"))
            total = result.scalar()
            logger.info(f"Total de avaliações no banco: {total}")
            logger.info("Todas as avaliações existentes foram configuradas com depreciação 0% por padrão.")
            
        except Exception as e:
            logger.error(f"Erro ao executar migração: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    logger.info("Iniciando migração do banco de dados...")
    logger.info("Adicionando campo de depreciação às avaliações...")
    add_depreciation_field()
    logger.info("Processo concluído!")
