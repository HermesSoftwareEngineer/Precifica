from langchain_core.tools import tool
from scraper import extract_content
from langgraph.prebuilt import ToolNode
from webSearch import web_search
from app.bot.customTypes import SalvarAvaliacaoInput
from app.extensions import db
from app.models.evaluation import Evaluation, BaseListing
from datetime import datetime

def normalize_purpose(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    normalized = value.strip()
    lowered = normalized.lower()

    if "residential" in lowered and "commercial" in lowered:
        return "Residencial / Comercial"
    if "residencial" in lowered and "comercial" in lowered:
        return "Residencial / Comercial"
    if "residential" in lowered or "residencial" in lowered:
        return "Residencial"
    if "commercial" in lowered or "comercial" in lowered:
        return "Comercial"

    return normalized

def normalize_property_type(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    normalized = value.strip()
    lowered = normalized.lower()

    mapping = [
        ("apartamento", "Apartamento"),
        ("apartment", "Apartamento"),
        ("casa", "Casa"),
        ("house", "Casa"),
        ("kitnet", "Kitnet"),
        ("loja", "Loja"),
        ("store", "Loja"),
        ("sala", "Sala"),
        ("office", "Sala"),
        ("terreno", "Terreno"),
        ("land", "Terreno")
    ]

    found = []
    for key, label in mapping:
        if key in lowered and label not in found:
            found.append(label)

    if found:
        return " / ".join(found)

    return normalized

@tool
def ler_conteudo_site(url: str):
    """
        Use essa ferramente para ler conteúdos de sites através de urls.
    """
    content = extract_content(url)
    return content

@tool
def pesquisar_sites(pesquisa: str):
    """
        Use essa ferramenta pra fazer pesquisas online.
    """
    cx = "f250cd15b14884f9f" 
    num_results=10
    results = web_search(pesquisa, num_results, cx)
    return results

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
        normalized_purpose = normalize_purpose(purpose)
        normalized_property_type = normalize_property_type(property_type)
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
            purpose=normalized_purpose,
            property_type=normalized_property_type,
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
            # Check if imovel is dict or object and allow PT/EN keys
            def get_attr(obj, *attrs):
                if isinstance(obj, dict):
                    for attr in attrs:
                        if not attr:
                            continue
                        value = obj.get(attr)
                        if value not in (None, ""):
                            return value
                else:
                    for attr in attrs:
                        if not attr:
                            continue
                        value = getattr(obj, attr, None)
                        if value not in (None, ""):
                            return value
                return None

            listing_purpose = normalize_purpose(get_attr(imovel, 'finalidade', 'purpose'))
            listing_type = normalize_property_type(get_attr(imovel, 'tipo', 'type'))
            novo_imovel = BaseListing(
                evaluation_id=nova_avaliacao.id,
                sample_number=get_attr(imovel, 'numero_amostra', 'sample_number') or idx,
                address=get_attr(imovel, 'endereco', 'address'),
                neighborhood=get_attr(imovel, 'bairro', 'neighborhood'),
                city=get_attr(imovel, 'cidade', 'city'),
                state=get_attr(imovel, 'estado', 'state'),
                link=get_attr(imovel, 'link', 'url'),
                area=get_attr(imovel, 'area'),
                bedrooms=get_attr(imovel, 'quartos', 'bedrooms') or 0,
                bathrooms=get_attr(imovel, 'banheiros', 'bathrooms') or 0,
                parking_spaces=get_attr(imovel, 'vagas', 'parking_spaces') or 0,
                rent_value=get_attr(imovel, 'valor_aluguel', 'valor_total', 'rent_value', 'price', 'sale_value'),
                condo_fee=get_attr(imovel, 'valor_condominio', 'condo_fee'),
                type=listing_type,
                purpose=listing_purpose,
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

toolsList = [ler_conteudo_site, pesquisar_sites, salvar_avaliacao_db]
tools_node = ToolNode(toolsList)