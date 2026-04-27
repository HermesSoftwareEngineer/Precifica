from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from app.bot.graphEvaluator import graph as evaluator_graph
from app.bot.evaluatorTools import ler_conteudo_site, pesquisar_sites
from app.controllers.evaluation_controller import (
    create_evaluation, get_evaluation, get_evaluations, update_evaluation, delete_evaluation,
    create_base_listing, get_base_listing, update_base_listing, delete_base_listing
)
import json
from datetime import datetime
from typing import List, Dict, Any
from app.bot.customTypes import SalvarAvaliacaoInput
from app.services.ai_cancel import is_evaluation_canceled
from app.services.sse import publish_event

@tool
def ler_instrucoes_para_nova_avaliacao():
    """
    Retorna instruções de como iniciar uma nova avaliação (SOMENTE EM CASOS DE NOVA AVALIAÇÃO)
    """
    return """Você é um avaliador de imóveis sênior da Imobiliária Stylus. Determine o valor de mercado com precisão usando dados reais.

### PROCESSO:

1. **Coletar Dados do Imóvel**:
    - Endereço completo, Área (m²), Quartos, Banheiros, Vagas, Classificação (Venda/Aluguel), Finalidade (Residencial/Comercial)
   - Se faltar informação crítica (Bairro, Cidade, Área), pergunte ao usuário

2. **Pesquisar Comparáveis**:
   - Busque 15-25 imóveis no **mesmo bairro e cidade**
   - Use `pesquisar_sites` para encontrar anúncios semelhantes
   - Acesse 2-3 links com `ler_conteudo_site` para extrair detalhes precisos

3. **Extrair Dados** (para cada imóvel):
   - Link, Endereço, Área (m²), Valor Total, Quartos, Banheiros, Vagas, Condomínio
   - Calcule: Valor/m² = Valor Total ÷ Área
    - Se estiver adicionando a uma avaliação existente, adicione um imóvel por vez assim que validar

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
    - `description`, `classification` (Venda/Aluguel), `purpose` (Residencial/Comercial), `property_type`
   - `bedrooms`, `bathrooms`, `parking_spaces`
   - `area` → ⚠️ recalcula métricas automaticamente

   **B) Adicionar Imóveis Comparativos**:
   - Pesquise com `pesquisar_sites` + `ler_conteudo_site`
   - **🚨 FILTRE** antes de adicionar:
     - Área: ±30% do imóvel avaliado
     - Quartos/Banheiros/Vagas: ±3 unidade
     - Remova outliers de Valor/m²
     - Use `adicionar_imoveis_base(evaluation_id, imoveis)` e adicione um imóvel por vez conforme validar
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
        evaluation_data = {
            "address": endereco,
            "neighborhood": bairro,
            "city": cidade,
            "state": estado,
            "area": area,
            "bedrooms": quartos,
            "bathrooms": banheiros,
            "parking_spaces": vagas,
            "description": description,
            "classification": classification,
            "purpose": purpose,
            "property_type": property_type,
            "region_value_sqm": valor_regiao_m2,
            "analysis_type": tipo_analise,
            "owner_name": nome_proprietario,
            "appraiser_name": nome_avaliador,
            "estimated_price": preco_estimado,
            "rounded_price": preco_arredondado,
            "analyzed_properties_count": len(imoveis_considerados)
        }
        
        response, status_code = create_evaluation(evaluation_data)
        if status_code != 201:
             return f"Erro ao salvar avaliação: {response.get_json().get('error')}"
        
        nova_avaliacao = response.get_json()
        evaluation_id = nova_avaliacao['id']

        # Create BaseListings
        for idx, imovel in enumerate(imoveis_considerados, start=1):
            # Helper to support PT/EN keys when extracting listing data
            def get_attr(obj, *attrs):
                if isinstance(obj, dict):
                    for attr in attrs:
                        value = obj.get(attr)
                        if value not in (None, ""):
                            return value
                else:
                    for attr in attrs:
                        value = getattr(obj, attr, None)
                        if value not in (None, ""):
                            return value
                return None

            listing_data = {
                "sample_number": get_attr(imovel, 'numero_amostra', 'sample_number') or idx,
                "address": get_attr(imovel, 'endereco', 'address'),
                "neighborhood": get_attr(imovel, 'bairro', 'neighborhood'),
                "city": get_attr(imovel, 'cidade', 'city'),
                "state": get_attr(imovel, 'estado', 'state'),
                "link": get_attr(imovel, 'link', 'url'),
                "area": get_attr(imovel, 'area'),
                "bedrooms": get_attr(imovel, 'quartos', 'bedrooms') or 0,
                "bathrooms": get_attr(imovel, 'banheiros', 'bathrooms') or 0,
                "parking_spaces": get_attr(imovel, 'vagas', 'parking_spaces') or 0,
                "rent_value": get_attr(imovel, 'valor_aluguel', 'valor_total', 'rent_value', 'price', 'sale_value'),
                "condo_fee": get_attr(imovel, 'valor_condominio', 'condo_fee'),
                "type": get_attr(imovel, 'tipo', 'type'),
                "purpose": get_attr(imovel, 'finalidade', 'purpose'),
                "collected_at": datetime.utcnow().isoformat()
            }
            
            resp_listing, status_listing = create_base_listing(evaluation_id, listing_data)
            if status_listing != 201:
                return f"Erro ao salvar imóvel comparativo: {resp_listing.get_json().get('error')}"

        return f"Avaliação salva com sucesso! ID: {evaluation_id}"

    except Exception as e:
        return f"Erro ao salvar avaliação: {str(e)}"

@tool
def ler_avaliacao(id: int):
    """
    Busca os detalhes de uma avaliação existente pelo seu ID.
    Retorna os dados da avaliação e dos imóveis comparativos usados.
    """
    try:
        response, status = get_evaluation(id)
        if status != 200:
             return f"Avaliação com ID {id} não encontrada."
        
        return json.dumps(response.get_json(), indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Erro ao ler avaliação: {str(e)}"

@tool
def listar_avaliacoes():
    """
    Lista todas as avaliações salvas no banco de dados.
    Retorna ID, Endereço, Bairro e Preço Estimado.
    """
    try:
        response, status = get_evaluations()
        if status != 200:
            return "Erro ao listar avaliações."
        
        evaluations = response.get_json()
        if isinstance(evaluations, dict):
            evaluations = evaluations.get('items', [])

        if not evaluations:
            return "Nenhuma avaliação encontrada."
        
        result = []
        for ev in evaluations:
            result.append(f"ID: {ev['id']} | Endereço: {ev['address']} | Bairro: {ev['neighborhood']} | Preço: {ev['estimated_price']}")
        
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
        data = {}
        if campo in ['estimated_price', 'rounded_price', 'area']:
            data[campo] = float(novo_valor)
        elif campo in ['bedrooms', 'bathrooms', 'parking_spaces']:
            data[campo] = int(novo_valor)
        elif campo in ['owner_name', 'appraiser_name', 'description', 'classification', 'purpose', 'property_type']:
            data[campo] = novo_valor
        else:
            return "Campo inválido. Use: owner_name, appraiser_name, estimated_price, rounded_price, description, classification, purpose, property_type, bedrooms, bathrooms, parking_spaces, area."
            
        response, status = update_evaluation(id, data)
        if status != 200:
            return f"Erro ao atualizar avaliação: {response.get_json().get('error')}"
            
        return f"Avaliação {id} atualizada com sucesso."
    except Exception as e:
        return f"Erro ao atualizar avaliação: {str(e)}"

@tool
def deletar_avaliacao(id: int):
    """
    Remove uma avaliação do banco de dados pelo ID.
    """
    try:
        response, status = delete_evaluation(id)
        if status != 200:
             return f"Erro ao deletar avaliação: {response.get_json().get('error')}"
        
        return f"Avaliação {id} deletada com sucesso."
    except Exception as e:
        return f"Erro ao deletar avaliação: {str(e)}"

@tool
def ler_imovel_base(id: int):
    """
    Busca os detalhes de um imóvel base (comparativo) pelo seu ID.
    """
    try:
        response, status = get_base_listing(id)
        if status != 200:
            return f"Imóvel base com ID {id} não encontrado."
        
        return json.dumps(response.get_json(), indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Erro ao ler imóvel base: {str(e)}"

@tool
def alterar_imovel_base(id: int, campo: str, novo_valor: str):
    """
    Atualiza um campo específico de um imóvel base (comparativo).
    Campos permitidos: sample_number, address, neighborhood, city, state, link, area, bedrooms, bathrooms, parking_spaces, living_rooms, rent_value, condo_fee, type, purpose, is_active/status/situacao, deactivation_reason/motivo_desativacao.
    """
    try:
        campo_normalizado = (campo or "").strip().lower()
        valor_texto = "" if novo_valor is None else str(novo_valor).strip()
        data = {}
        if campo_normalizado == 'sample_number':
            data['sample_number'] = int(valor_texto) if valor_texto else None
        elif campo_normalizado in ['area', 'rent_value', 'condo_fee']:
            data[campo_normalizado] = float(valor_texto)
        elif campo_normalizado in ['bedrooms', 'bathrooms', 'parking_spaces', 'living_rooms']:
            data[campo_normalizado] = int(valor_texto)
        elif campo_normalizado in ['address', 'neighborhood', 'city', 'state', 'link', 'type', 'purpose']:
            data[campo_normalizado] = novo_valor
        elif campo_normalizado in ['is_active', 'status', 'situacao', 'ativo', 'active']:
            valor_bool = valor_texto.lower()
            if valor_bool in ['true', '1', 'sim', 'ativo', 'ativa', 'yes', 'on']:
                data['is_active'] = True
            elif valor_bool in ['false', '0', 'nao', 'não', 'inativo', 'inativa', 'no', 'off']:
                data['is_active'] = False
            else:
                return (
                    "Valor inválido para status/situacao. "
                    "Use: ativo/inativo, true/false, 1/0, sim/nao."
                )
        elif campo_normalizado in ['deactivation_reason', 'motivo_desativacao', 'motivo_desativação']:
            data['deactivation_reason'] = novo_valor
        else:
            return f"Campo '{campo}' não é válido ou não pode ser alterado por esta ferramenta."
            
        response, status = update_base_listing(id, data)
        if status != 200:
             return f"Erro ao atualizar imóvel base: {response.get_json().get('error')}"

        return f"Imóvel base {id} atualizado com sucesso."
    except Exception as e:
        return f"Erro ao atualizar imóvel base: {str(e)}"

@tool
def deletar_imoveis_base(ids: List[int]):
    """
    Remove um ou mais imóveis base (comparativos) do banco de dados pelos seus IDs.
    Exemplo de uso: deletar_imoveis_base([1, 2, 3])
    """
    try:
        count = 0
        for id in ids:
            response, status = delete_base_listing(id)
            if status == 200:
                count += 1
        
        return f"{count} imóveis base deletados com sucesso."
    except Exception as e:
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
        if is_evaluation_canceled(evaluation_id):
            publish_event(f"evaluation:{evaluation_id}", "cancelled", {"reason": "user_requested"})
            return f"Operacao cancelada pelo usuario para avaliacao {evaluation_id}."
        # Check if evaluation exists
        response, status = get_evaluation(evaluation_id)
        if status != 200:
            return f"Avaliação com ID {evaluation_id} não encontrada."

        evaluation_data = response.get_json()
        existing_listings = evaluation_data.get('base_listings', [])
        
        next_sample_number = max([l.get('sample_number') for l in existing_listings if l.get('sample_number')], default=0) + 1
        
        count = 0
        for imovel in imoveis:
            if is_evaluation_canceled(evaluation_id):
                publish_event(f"evaluation:{evaluation_id}", "cancelled", {"reason": "user_requested"})
                return f"Operacao cancelada pelo usuario para avaliacao {evaluation_id}."
            # Helper function to get value from dict (supports both PT and EN keys)
            def get_attr(obj, attr_pt, attr_en=None, *extra_aliases):
                if isinstance(obj, dict):
                    # Try Portuguese first, then English
                    for key in (attr_pt, attr_en, *extra_aliases):
                        if not key:
                            continue
                        value = obj.get(key)
                        if value not in (None, ""):
                            return value
                    return None
                for key in (attr_pt, attr_en, *extra_aliases):
                    if not key:
                        continue
                    value = getattr(obj, key, None)
                    if value not in (None, ""):
                        return value
                return None

            listing_data = {
                "sample_number": get_attr(imovel, 'numero_amostra', 'sample_number') or next_sample_number,
                "address": get_attr(imovel, 'endereco', 'address'),
                "neighborhood": get_attr(imovel, 'bairro', 'neighborhood'),
                "city": get_attr(imovel, 'cidade', 'city'),
                "state": get_attr(imovel, 'estado', 'state'),
                "link": get_attr(imovel, 'link', None, 'url'),
                "area": get_attr(imovel, 'area'),
                "bedrooms": get_attr(imovel, 'quartos', 'bedrooms') or 0,
                "bathrooms": get_attr(imovel, 'banheiros', 'bathrooms') or 0,
                "parking_spaces": get_attr(imovel, 'vagas', 'parking_spaces') or 0,
                "rent_value": get_attr(imovel, 'valor_aluguel', 'rent_value', 'valor_total', 'price', 'sale_value'),
                "condo_fee": get_attr(imovel, 'valor_condominio', 'condo_fee'),
                "type": get_attr(imovel, 'tipo', 'type'),
                "purpose": get_attr(imovel, 'finalidade', 'purpose'),
                "collected_at": datetime.utcnow().isoformat()
            }
            
            resp_l, status_l = create_base_listing(evaluation_id, listing_data)
            if status_l == 201:
                count += 1
                next_sample_number += 1
        
        return f"{count} imóveis base adicionados com sucesso à avaliação {evaluation_id}."
    except Exception as e:
        return f"Erro ao adicionar imóveis base: {str(e)}"

toolsList = [salvar_avaliacao_db, ler_instrucoes_para_nova_avaliacao, ler_instrucoes_para_atualizar_uma_avaliacao_existente, ler_avaliacao, listar_avaliacoes, alterar_avaliacao, deletar_avaliacao, ler_imovel_base, alterar_imovel_base, deletar_imoveis_base, adicionar_imoveis_base, ler_conteudo_site, pesquisar_sites]
tools_node = ToolNode(toolsList)