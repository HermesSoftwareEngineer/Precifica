from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from app.bot.graphEvaluator import graph as evaluator_graph
from app.models.evaluation import Evaluation, BaseListing
from app.extensions import db
from app.bot.evaluatorTools import ler_conteudo_site, pesquisar_sites
import json
from datetime import datetime
from typing import List, Dict, Any
from app.bot.customTypes import SalvarAvaliacaoInput

@tool
def ler_instrucoes_para_nova_avaliacao():
    """
    Retorna instruções de como iniciar uma nova avaliação (SOMENTE EM CASOS DE NOVA AVALIAÇÃO)
    """
    return """Você é um avaliador de imóveis sênior da Imobiliária Stylus. Determine o valor de mercado com precisão usando dados reais.

### PROCESSO:

1. **Coletar Dados do Imóvel**:
   - Endereço completo, Área (m²), Quartos, Banheiros, Vagas, Finalidade (Venda/Aluguel)
   - Se faltar informação crítica (Bairro, Cidade, Área), pergunte ao usuário

2. **Pesquisar Comparáveis**:
   - Busque 15-25 imóveis no **mesmo bairro e cidade**
   - Use `pesquisar_sites` para encontrar anúncios semelhantes
   - Acesse 2-3 links com `ler_conteudo_site` para extrair detalhes precisos

3. **Extrair Dados** (para cada imóvel):
   - Link, Endereço, Área (m²), Valor Total, Quartos, Banheiros, Vagas, Condomínio
   - Calcule: Valor/m² = Valor Total ÷ Área

4. **🚨 FILTRAR IMÓVEIS (CRÍTICO)**:
   - **REMOVA** imóveis com diferenças grandes em relação ao imóvel avaliado:
     - Área: ±60% da área alvo
     - Quartos/Banheiros/Vagas: ±3 unidade
     - Valor/m²: outliers (valores muito acima/abaixo da média)
   - Mantenha apenas 10-20 imóveis **REALMENTE SEMELHANTES**
   - Justifique brevemente quais foram removidos e por quê

5. **Calcular Avaliação**:
   - **Média do Valor/m²** da amostra filtrada
   - **Preço Estimado** = Média m² × Área do Imóvel
   - **Preço Arredondado** comercialmente aceitável

6. **Salvar** (OBRIGATÓRIO):
   - Use `salvar_avaliacao_db` com TODOS os campos
   - Inclua apenas os imóveis filtrados em `imoveis_considerados`

7. **Relatório**:
   - Valor estimado, Média m², Lista de imóveis usados, Justificativa
   - Mencione quantos imóveis foram removidos na filtragem

Base suas estimativas APENAS em dados semelhantes e verificados.
        """

@tool
def ler_instrucoes_para_atualizar_uma_avaliacao_existente():
    """
    Retorna instruções de como atualizar uma avaliação existente (SOMENTE PARA ATUALIZAÇÕES DE AVALIAÇÕES JÁ SALVAS)
    """
    return """Você é um avaliador de imóveis sênior da Imobiliária Stylus. ATUALIZE avaliações existentes com precisão.

### PROCESSO:

1. **Identificar Avaliação**:
   - Com ID: use `ler_avaliacao(id)`
   - Sem ID: use `listar_avaliacoes` e localize por endereço/bairro
   - **SEMPRE** leia a avaliação completa antes de alterar

2. **Tipos de Atualização**:

   **A) Alterar Dados Principais** (`alterar_avaliacao`):
   - `owner_name`, `appraiser_name`, `estimated_price`, `rounded_price`
   - `description`, `classification`, `purpose`, `property_type`
   - `bedrooms`, `bathrooms`, `parking_spaces`
   - `area` → ⚠️ recalcula métricas automaticamente

   **B) Adicionar Imóveis Comparativos**:
   - Pesquise com `pesquisar_sites` + `ler_conteudo_site`
   - **🚨 FILTRE** antes de adicionar:
     - Área: ±30% do imóvel avaliado
     - Quartos/Banheiros/Vagas: ±3 unidade
     - Remova outliers de Valor/m²
   - Use `adicionar_imoveis_base(evaluation_id, imoveis)`
   - Métricas recalculam automaticamente

   **C) Remover Imóveis** (outliers, dados incorretos):
   - Identifique IDs em `ler_avaliacao`
   - Use `deletar_imoveis_base([id1, id2, ...])`
   - Confirme com usuário antes de deletar
   - Mantenha 10-20 imóveis semelhantes na amostra

   **D) Corrigir Dados de Imóvel**:
   - `ler_imovel_base(id)` → ver dados atuais
   - `alterar_imovel_base(id, campo, valor)` → corrigir
   - Recalcula métricas automaticamente

3. **🚨 VALIDAÇÃO DE SEMELHANÇA** (ao adicionar/manter imóveis):
   - **CRÍTICO**: Imóveis devem ser SEMELHANTES ao avaliado
   - Rejeite se diferenças grandes em:
     - Área (±60%)
     - Quartos, Banheiros, Vagas (±1)
     - Valor/m² (outliers)
   - Justifique exclusões ao usuário

4. **Recálculo Automático**:
   - Sistema recalcula: Média m², Preço estimado, Qtd. imóveis
   - **NÃO** recalcule manualmente

5. **Confirmar e Reportar**:
   - Releia com `ler_avaliacao` após mudanças
   - Informe: o que mudou, novos valores, recálculos

### EXEMPLO:
"Adicione 5 imóveis à avaliação ID 10"
→ Lê avaliação 10 → Pesquisa → Filtra semelhantes → `adicionar_imoveis_base` → Relê → Reporta novos valores

Seja preciso e valide semelhança SEMPRE.
        """

@tool(args_schema=SalvarAvaliacaoInput)
def salvar_avaliacao_db(
    endereco: str,
    bairro: str,
    cidade: str,
    estado: str,
    area: float,
    imoveis_considerados: list,
    quartos: int = 0,
    banheiros: int = 0,
    vagas: int = 0,
    description: str = None,
    classification: str = None,
    purpose: str = None,
    property_type: str = None,
    tipo_analise: str = "region",
    valor_regiao_m2: float = None,
    nome_proprietario: str = None,
    nome_avaliador: str = None,
    preco_estimado: float = None,
    preco_arredondado: float = None
):
    """
    Salva uma avaliação e seus imóveis comparativos no banco de dados.

    Campos da Avaliação:
    - endereco (str): Endereço completo
    - bairro (str): Bairro
    - cidade (str): Cidade
    - estado (str): Estado (UF)
    - area (float): Área em m²
    - quartos (int): Quantidade de quartos
    - banheiros (int): Quantidade de banheiros
    - vagas (int): Quantidade de vagas
    - description (str, opcional): Descrição
    - classification (str, opcional): Classificação (Venda/Aluguel)
    - purpose (str, opcional): Finalidade (Residencial/Comercial)
    - property_type (str, opcional): Tipo do imóvel
    - tipo_analise (str): "region" ou "street"
    - valor_regiao_m2 (float, opcional)
    - nome_proprietario (str, opcional)
    - nome_avaliador (str, opcional)
    - preco_estimado (float, opcional)
    - preco_arredondado (float, opcional)

    Campos para cada imóvel em 'imoveis_considerados':
    - numero_amostra (int, opcional): Número da amostra no contexto da avaliação
    - endereco, bairro, cidade, estado (str)
    - link (str): URL do anúncio
    - area (float)
    - quartos, banheiros, vagas (int)
    - valor_aluguel, valor_condominio (float)
    - tipo (str): ex: Apartamento
    - finalidade (str): ex: Residencial
    """
    try:
        # Create Evaluation
        nova_avaliacao = Evaluation(
            address=endereco,
            neighborhood=bairro,
            city=cidade,
            state=estado,
            area=area,
            bedrooms=quartos,
            bathrooms=banheiros,
            parking_spaces=vagas,
            description=description,
            classification=classification,
            purpose=purpose,
            property_type=property_type,
            region_value_sqm=valor_regiao_m2,
            analysis_type=tipo_analise,
            owner_name=nome_proprietario,
            appraiser_name=nome_avaliador,
            estimated_price=preco_estimado,
            rounded_price=preco_arredondado,
            analyzed_properties_count=len(imoveis_considerados)
        )
        
        db.session.add(nova_avaliacao)
        db.session.flush() # Get ID

        # Create BaseListings
        for idx, imovel in enumerate(imoveis_considerados, start=1):
            # Check if imovel is dict or object
            def get_attr(obj, attr):
                if isinstance(obj, dict):
                    return obj.get(attr)
                return getattr(obj, attr, None)

            novo_imovel = BaseListing(
                evaluation_id=nova_avaliacao.id,
                sample_number=get_attr(imovel, 'numero_amostra') or idx,
                address=get_attr(imovel, 'endereco'),
                neighborhood=get_attr(imovel, 'bairro'),
                city=get_attr(imovel, 'cidade'),
                state=get_attr(imovel, 'estado'),
                link=get_attr(imovel, 'link'),
                area=get_attr(imovel, 'area'),
                bedrooms=get_attr(imovel, 'quartos') or 0,
                bathrooms=get_attr(imovel, 'banheiros') or 0,
                parking_spaces=get_attr(imovel, 'vagas') or 0,
                rent_value=get_attr(imovel, 'valor_aluguel'),
                condo_fee=get_attr(imovel, 'valor_condominio'),
                type=get_attr(imovel, 'tipo'),
                purpose=get_attr(imovel, 'finalidade'),
                collected_at=datetime.utcnow()
            )
            db.session.add(novo_imovel)

        db.session.flush()
        nova_avaliacao.recalculate_metrics()
        db.session.commit()
        return f"Avaliação salva com sucesso! ID: {nova_avaliacao.id}"

    except Exception as e:
        db.session.rollback()
        return f"Erro ao salvar avaliação: {str(e)}"

@tool
def ler_avaliacao(id: int):
    """
    Busca os detalhes de uma avaliação existente pelo seu ID.
    Retorna os dados da avaliação e dos imóveis comparativos usados.
    """
    try:
        evaluation = Evaluation.query.get(id)
        if not evaluation:
            return f"Avaliação com ID {id} não encontrada."
        
        return json.dumps(evaluation.to_dict(include_listings=True), indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Erro ao ler avaliação: {str(e)}"

@tool
def listar_avaliacoes():
    """
    Lista todas as avaliações salvas no banco de dados.
    Retorna ID, Endereço, Bairro e Preço Estimado.
    """
    try:
        evaluations = Evaluation.query.all()
        if not evaluations:
            return "Nenhuma avaliação encontrada."
        
        result = []
        for ev in evaluations:
            result.append(f"ID: {ev.id} | Endereço: {ev.address} | Bairro: {ev.neighborhood} | Preço: {ev.estimated_price}")
        
        return "\n".join(result)
    except Exception as e:
        return f"Erro ao listar avaliações: {str(e)}"

@tool
def alterar_avaliacao(id: int, campo: str, novo_valor: str):
    """
    Atualiza um campo específico de uma avaliação.
    Campos permitidos: owner_name, appraiser_name, estimated_price, rounded_price, description, classification, purpose, property_type, bedrooms, bathrooms, parking_spaces, area.
    """
    try:
        evaluation = Evaluation.query.get(id)
        if not evaluation:
            return f"Avaliação com ID {id} não encontrada."
        
        if campo == 'owner_name':
            evaluation.owner_name = novo_valor
        elif campo == 'appraiser_name':
            evaluation.appraiser_name = novo_valor
        elif campo == 'estimated_price':
            evaluation.estimated_price = float(novo_valor)
        elif campo == 'rounded_price':
            evaluation.rounded_price = float(novo_valor)
        elif campo == 'description':
            evaluation.description = novo_valor
        elif campo == 'classification':
            evaluation.classification = novo_valor
        elif campo == 'purpose':
            evaluation.purpose = novo_valor
        elif campo == 'property_type':
            evaluation.property_type = novo_valor
        elif campo == 'bedrooms':
            evaluation.bedrooms = int(novo_valor)
        elif campo == 'bathrooms':
            evaluation.bathrooms = int(novo_valor)
        elif campo == 'parking_spaces':
            evaluation.parking_spaces = int(novo_valor)
        elif campo == 'area':
            evaluation.area = float(novo_valor)
            evaluation.recalculate_metrics()
        else:
            return "Campo inválido. Use: owner_name, appraiser_name, estimated_price, rounded_price, description, classification, purpose, property_type, bedrooms, bathrooms, parking_spaces, area."
            
        db.session.commit()
        return f"Avaliação {id} atualizada com sucesso."
    except Exception as e:
        db.session.rollback()
        return f"Erro ao atualizar avaliação: {str(e)}"

@tool
def deletar_avaliacao(id: int):
    """
    Remove uma avaliação do banco de dados pelo ID.
    """
    try:
        evaluation = Evaluation.query.get(id)
        if not evaluation:
            return f"Avaliação com ID {id} não encontrada."
        
        db.session.delete(evaluation)
        db.session.commit()
        return f"Avaliação {id} deletada com sucesso."
    except Exception as e:
        db.session.rollback()
        return f"Erro ao deletar avaliação: {str(e)}"

@tool
def ler_imovel_base(id: int):
    """
    Busca os detalhes de um imóvel base (comparativo) pelo seu ID.
    """
    try:
        listing = BaseListing.query.get(id)
        if not listing:
            return f"Imóvel base com ID {id} não encontrado."
        
        return json.dumps(listing.to_dict(), indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Erro ao ler imóvel base: {str(e)}"

@tool
def alterar_imovel_base(id: int, campo: str, novo_valor: str):
    """
    Atualiza um campo específico de um imóvel base (comparativo).
    Campos permitidos: sample_number, address, neighborhood, city, state, link, area, bedrooms, bathrooms, parking_spaces, rent_value, condo_fee, type, purpose.
    """
    try:
        listing = BaseListing.query.get(id)
        if not listing:
            return f"Imóvel base com ID {id} não encontrado."
        
        # Helper to convert types if needed
        if campo == 'sample_number':
            setattr(listing, campo, int(novo_valor) if novo_valor else None)
        elif campo in ['area', 'rent_value', 'condo_fee']:
             setattr(listing, campo, float(novo_valor))
        elif campo in ['bedrooms', 'bathrooms', 'parking_spaces', 'living_rooms']:
             setattr(listing, campo, int(novo_valor))
        elif campo in ['address', 'neighborhood', 'city', 'state', 'link', 'type', 'purpose']:
             setattr(listing, campo, novo_valor)
        else:
            return f"Campo '{campo}' não é válido ou não pode ser alterado por esta ferramenta."
            
        if listing.evaluation:
            listing.evaluation.recalculate_metrics()

        db.session.commit()
        return f"Imóvel base {id} atualizado com sucesso."
    except Exception as e:
        db.session.rollback()
        return f"Erro ao atualizar imóvel base: {str(e)}"

@tool
def deletar_imoveis_base(ids: List[int]):
    """
    Remove um ou mais imóveis base (comparativos) do banco de dados pelos seus IDs.
    Exemplo de uso: deletar_imoveis_base([1, 2, 3])
    """
    try:
        count = 0
        evaluations_to_update = set()
        for id in ids:
            listing = BaseListing.query.get(id)
            if listing:
                if listing.evaluation:
                    evaluations_to_update.add(listing.evaluation)
                db.session.delete(listing)
                count += 1
        
        db.session.flush()
        for evaluation in evaluations_to_update:
            evaluation.recalculate_metrics()

        db.session.commit()
        return f"{count} imóveis base deletados com sucesso."
    except Exception as e:
        db.session.rollback()
        return f"Erro ao deletar imóveis base: {str(e)}"

@tool
def adicionar_imoveis_base(evaluation_id: int, imoveis: List[Dict[str, Any]]):
    """
    Adiciona um ou mais imóveis base (comparativos) a uma avaliação existente.
    'imoveis' deve ser uma lista de dicionários contendo os dados dos imóveis.
    Campos esperados no dicionário (em português OU inglês):
    - numero_amostra/sample_number (int, opcional): Número da amostra
    - endereco/address, bairro/neighborhood, cidade/city, estado/state (str)
    - link (str): URL do anúncio
    - area (float): Área em m²
    - quartos/bedrooms, banheiros/bathrooms, vagas/parking_spaces (int)
    - valor_aluguel/rent_value, valor_condominio/condo_fee (float)
    - tipo/type (str): ex: Apartamento
    - finalidade/purpose (str): ex: Residencial
    """
    try:
        evaluation = Evaluation.query.get(evaluation_id)
        if not evaluation:
            return f"Avaliação com ID {evaluation_id} não encontrada."

        count = 0
        # Get current max sample_number for auto-increment
        existing_listings = BaseListing.query.filter_by(evaluation_id=evaluation_id).all()
        next_sample_number = max([l.sample_number for l in existing_listings if l.sample_number], default=0) + 1
        
        for imovel in imoveis:
            # Helper function to get value from dict (supports both PT and EN keys)
            def get_attr(obj, attr_pt, attr_en=None):
                if isinstance(obj, dict):
                    # Try Portuguese first, then English
                    return obj.get(attr_pt) or (obj.get(attr_en) if attr_en else None)
                return getattr(obj, attr_pt, None) or (getattr(obj, attr_en, None) if attr_en else None)

            new_listing = BaseListing(
                evaluation_id=evaluation_id,
                sample_number=get_attr(imovel, 'numero_amostra', 'sample_number') or next_sample_number,
                address=get_attr(imovel, 'endereco', 'address'),
                neighborhood=get_attr(imovel, 'bairro', 'neighborhood'),
                city=get_attr(imovel, 'cidade', 'city'),
                state=get_attr(imovel, 'estado', 'state'),
                link=get_attr(imovel, 'link'),
                area=get_attr(imovel, 'area'),
                bedrooms=get_attr(imovel, 'quartos', 'bedrooms') or 0,
                bathrooms=get_attr(imovel, 'banheiros', 'bathrooms') or 0,
                parking_spaces=get_attr(imovel, 'vagas', 'parking_spaces') or 0,
                rent_value=get_attr(imovel, 'valor_aluguel', 'rent_value'),
                condo_fee=get_attr(imovel, 'valor_condominio', 'condo_fee'),
                type=get_attr(imovel, 'tipo', 'type'),
                purpose=get_attr(imovel, 'finalidade', 'purpose'),
                collected_at=datetime.utcnow()
            )
            db.session.add(new_listing)
            count += 1
            next_sample_number += 1
        
        db.session.flush()
        evaluation.recalculate_metrics()
        db.session.commit()
        return f"{count} imóveis base adicionados com sucesso à avaliação {evaluation_id}."
    except Exception as e:
        db.session.rollback()
        return f"Erro ao adicionar imóveis base: {str(e)}"

toolsList = [salvar_avaliacao_db, ler_instrucoes_para_nova_avaliacao, ler_instrucoes_para_atualizar_uma_avaliacao_existente, ler_avaliacao, listar_avaliacoes, alterar_avaliacao, deletar_avaliacao, ler_imovel_base, alterar_imovel_base, deletar_imoveis_base, adicionar_imoveis_base, ler_conteudo_site, pesquisar_sites]
tools_node = ToolNode(toolsList)