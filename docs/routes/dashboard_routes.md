# Dashboard Routes

Este documento descreve a API de rotas do Dashboard.

## Autenticação

Todas as rotas neste módulo requerem autenticação.
A API usa autenticação **JWT (JSON Web Token)**. Você deve incluir o token JWT obtido do endpoint `/auth/login` no cabeçalho `Authorization` de suas requisições.

*   **Autenticação Obrigatória:** Sim
*   **Tipo de Autenticação:** Bearer Token
*   **Header:** `Authorization: Bearer <seu_access_token>`

## Obter Estatísticas do Dashboard

Retorna todas as estatísticas consolidadas do dashboard em uma única requisição.

*   **URL:** `/api/dashboard/stats`
*   **Método:** `GET`
*   **Autenticação Obrigatória:** Sim

### Resposta de Sucesso

*   **Código:** 200
*   **Conteúdo:**
    ```json
    {
        "top_neighborhoods": {
            "sale": [
                {
                    "neighborhood": "Jardins",
                    "city": "São Paulo",
                    "avg_price_sqm": 12500.50
                },
                {
                    "neighborhood": "Leblon",
                    "city": "Rio de Janeiro",
                    "avg_price_sqm": 11800.00
                }
            ],
            "rent": [
                {
                    "neighborhood": "Vila Mariana",
                    "city": "São Paulo",
                    "avg_price_sqm": 85.30
                },
                {
                    "neighborhood": "Botafogo",
                    "city": "Rio de Janeiro",
                    "avg_price_sqm": 75.00
                }
            ]
        },
        "top_cities": {
            "sale": [
                {
                    "city": "São Paulo",
                    "avg_price_sqm": 8500.00,
                    "count": 150
                },
                {
                    "city": "Rio de Janeiro",
                    "avg_price_sqm": 7800.00,
                    "count": 80
                }
            ],
            "rent": [
                {
                    "city": "São Paulo",
                    "avg_price_sqm": 65.00,
                    "count": 200
                },
                {
                    "city": "Rio de Janeiro",
                    "avg_price_sqm": 58.00,
                    "count": 120
                }
            ]
        },
        "evaluations_by_type": {
            "Apartamento": 250,
            "Casa": 120,
            "Cobertura": 30,
            "Kitnet": 15
        },
        "evaluations_by_purpose": {
            "Residencial": 350,
            "Comercial": 65
        },
        "avg_price_sqm_by_purpose": {
            "Residencial": 7500.50,
            "Comercial": 9200.00
        },
        "avg_price_sqm_by_type": {
            "Apartamento": 8000.00,
            "Casa": 7200.00,
            "Cobertura": 12000.00,
            "Kitnet": 5500.00
        },
        "avg_price_sqm_by_bedrooms": [
            {
                "bedrooms": 1,
                "avg_price_sqm": 6500.00,
                "count": 80
            },
            {
                "bedrooms": 2,
                "avg_price_sqm": 7200.00,
                "count": 150
            },
            {
                "bedrooms": 3,
                "avg_price_sqm": 8000.00,
                "count": 120
            },
            {
                "bedrooms": 4,
                "avg_price_sqm": 9500.00,
                "count": 45
            }
        ]
    }
    ```

### Detalhamento dos Dados Retornados

#### top_neighborhoods
Top 10 bairros por preço médio do m², separados por:
- **sale**: Bairros com maiores preços médios de venda
- **rent**: Bairros com maiores preços médios de aluguel

Cada item contém:
- `neighborhood`: Nome do bairro
- `city`: Nome da cidade
- `avg_price_sqm`: Preço médio do m² no bairro

#### top_cities  
Top 10 cidades por preço médio do m², separadas por:
- **sale**: Cidades com maiores preços médios de venda
- **rent**: Cidades com maiores preços médios de aluguel

Cada item contém:
- `city`: Nome da cidade
- `avg_price_sqm`: Preço médio do m² na cidade
- `count`: Número de avaliações na cidade

#### evaluations_by_type
Número total de avaliações agrupadas por tipo de imóvel:
- Apartamento
- Casa
- Cobertura
- Kitnet
- Outros tipos

#### evaluations_by_purpose
Número total de avaliações agrupadas por finalidade:
- **Residencial**: Imóveis residenciais
- **Comercial**: Imóveis comerciais

#### avg_price_sqm_by_purpose
Preço médio do m² agrupado por finalidade (Residencial vs Comercial)

#### avg_price_sqm_by_type
Preço médio do m² agrupado por tipo de imóvel

#### avg_price_sqm_by_bedrooms
Lista com preço médio do m² agrupado por número de quartos, ordenada crescente:

Cada item contém:
- `bedrooms`: Número de quartos
- `avg_price_sqm`: Preço médio do m² para imóveis com esse número de quartos
- `count`: Quantidade de avaliações com esse número de quartos

### Resposta de Erro

*   **Código:** 500
*   **Conteúdo:** `{"error": "Descrição da mensagem de erro"}`

### Exemplo de Requisição

```bash
curl -X GET https://api.exemplo.com/api/dashboard/stats \
  -H "Authorization: Bearer seu_token_jwt_aqui"
```

### Observações

- Todos os valores de preço são arredondados para 2 casas decimais
- Quando não há dados suficientes para calcular médias, o valor retornado é `0`
- A classificação de venda/aluguel é feita buscando por palavras-chave: "venda"/"sale" para vendas e "aluguel"/"rent" para aluguéis
- Apenas avaliações com dados válidos (não nulos) são consideradas nos cálculos
