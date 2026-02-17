"""
Script para migrar todas as avaliações e conversas existentes para a unidade de ID 4
"""
import sys
import os

# Adiciona o diretório raiz ao path
if '__file__' in globals():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
else:
    sys.path.insert(0, '.')

from app import create_app, db
from app.models.evaluation import Evaluation
from app.models.chat import Conversation
from app.models.unit import Unit

def migrate_to_unit_4():
    app = create_app()
    
    with app.app_context():
        # Verifica se a unidade 4 existe
        unit = Unit.query.get(4)
        if not unit:
            print("❌ Erro: Unidade com ID 4 não existe!")
            return
        
        print(f"✓ Unidade encontrada: {unit.name}")
        print("-" * 60)
        
        # Migrar Avaliações
        evaluations = Evaluation.query.filter(
            (Evaluation.unit_id.is_(None)) | (Evaluation.unit_id != 4)
        ).all()
        
        print(f"📊 Migrando {len(evaluations)} avaliações para unidade '{unit.name}'...")
        for eval in evaluations:
            old_unit = eval.unit_id
            eval.unit_id = 4
            print(f"  - Avaliação ID {eval.id}: unit_id {old_unit} -> 4")
        
        # Migrar Conversas
        conversations = Conversation.query.filter(
            (Conversation.unit_id.is_(None)) | (Conversation.unit_id != 4)
        ).all()
        
        print(f"\n💬 Migrando {len(conversations)} conversas para unidade '{unit.name}'...")
        for conv in conversations:
            old_unit = conv.unit_id
            conv.unit_id = 4
            print(f"  - Conversa ID {conv.id}: unit_id {old_unit} -> 4")
        
        # Commit das mudanças
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ Migração concluída com sucesso!")
            print("=" * 60)
            print(f"✓ {len(evaluations)} avaliações migradas")
            print(f"✓ {len(conversations)} conversas migradas")
            print(f"✓ Todas agora pertencem à unidade: {unit.name}")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao fazer commit: {e}")
            raise

if __name__ == "__main__":
    migrate_to_unit_4()
