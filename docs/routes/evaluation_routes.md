# Evaluation Routes Documentation

Base URL: `/api/evaluations`

## Authentication

All routes in this module require authentication.
The API uses **JWT (JSON Web Token)** authentication. You must include the JWT token obtained from the `/auth/login` endpoint in the `Authorization` header of your requests.

*   **Auth Required:** Yes
*   **Auth Type:** Bearer Token
*   **Header:** `Authorization: Bearer <your_access_token>`

## 1. Create Evaluation
- **URL:** `/`
- **Method:** `POST`
- **Auth Required:** Yes
- **Description:** Creates a new property evaluation. Note: Fields like `region_value_sqm`, `estimated_price`, `rounded_price`, and `analyzed_properties_count` are automatically calculated based on associated base listings and should not be provided in the request body.
- **Body:**
  ```json
  {
    "address": "string",
    "neighborhood": "string",
    "city": "string",
    "state": "string",
    "area": number,
    "analysis_type": "string",
    "owner_name": "string (optional)",
    "appraiser_name": "string (optional)",
    "description": "string (optional)",
    "classification": "string (optional)",
    "purpose": "string (optional)",
    "property_type": "string (optional)",
    "bedrooms": number,
    "bathrooms": number,
    "parking_spaces": number,
    "depreciation": number (optional, default: 0.0, range: 0-100)
  }
  ```
- **Response:** JSON representation of the created evaluation (including auto-calculated fields).

## 1.1 Create Evaluation with AI
- **URL:** `/ai`
- **Method:** `POST`
- **Auth Required:** Yes
- **Description:** Creates a new evaluation and immediately triggers the AI to research comparable listings and add base listings to the evaluation. If no `ai_prompt` is provided, the system builds a default prompt from the created evaluation data.
- **Body:** Same as Create Evaluation, plus optional AI fields.
  ```json
  {
    "address": "string",
    "neighborhood": "string",
    "city": "string",
    "state": "string",
    "area": number,
    "analysis_type": "string",
    "owner_name": "string (optional)",
    "appraiser_name": "string (optional)",
    "description": "string (optional)",
    "classification": "string (optional)",
    "purpose": "string (optional)",
    "property_type": "string (optional)",
    "bedrooms": number,
    "bathrooms": number,
    "parking_spaces": number,
    "depreciation": number (optional, default: 0.0, range: 0-100),
    "ai_prompt": "string (optional)",
    "ai_force_new_chat": true
  }
  ```
- **Response:** JSON with the created evaluation and the AI response payload.
  ```json
  {
    "evaluation": {
      "id": 1,
      "address": "Rua Exemplo, 123",
      "neighborhood": "Centro",
      "city": "Sao Paulo",
      "state": "SP",
      "area": 100.0,
      "analysis_type": "region",
      "created_at": "2023-10-27T10:00:00"
    },
    "ai": {
      "response": "string",
      "conversation_id": 10,
      "message_id": 55
    }
  }
  ```

## 1.2 Create Evaluation with AI (Async)
- **URL:** `/ai/async`
- **Method:** `POST`
- **Auth Required:** Yes
- **Description:** Creates a new evaluation and queues the AI flow in the background. Use SSE to receive progress events and listing updates.
- **Body:** Same as Create Evaluation, plus optional AI fields.
  ```json
  {
    "address": "string",
    "neighborhood": "string",
    "city": "string",
    "state": "string",
    "area": number,
    "analysis_type": "string",
    "owner_name": "string (optional)",
    "appraiser_name": "string (optional)",
    "description": "string (optional)",
    "classification": "string (optional)",
    "purpose": "string (optional)",
    "property_type": "string (optional)",
    "bedrooms": number,
    "bathrooms": number,
    "parking_spaces": number,
    "ai_prompt": "string (optional)",
    "ai_force_new_chat": true
  }
  ```
- **Response:**
  - `202 Accepted`:
    ```json
    {
      "status": "queued",
      "evaluation": {
        "id": 1,
        "address": "Rua Exemplo, 123",
        "neighborhood": "Centro",
        "city": "Sao Paulo",
        "state": "SP",
        "area": 100.0,
        "analysis_type": "region",
        "created_at": "2023-10-27T10:00:00"
      },
      "conversation_id": 10,
      "message_id": 55
    }
    ```

### SSE Stream for AI Progress
- **URL:** `/<evaluation_id>/ai/stream`
- **Method:** `GET`
- **Auth Required:** Yes (same JWT header)
- **Note:** Native `EventSource` cannot set `Authorization` headers. Use cookie-based auth, a polyfill that supports headers, or a custom fetch stream if you must send a bearer token.
- **Description:** Streams progress events while the AI adds base listings.
- **Events:**
  - `connected`: stream is ready
  - `evaluation_created`: evaluation data right after creation
  - `ai_queued`: background AI job queued (includes conversation_id, message_id)
  - `listing_added`: a new base listing was added; includes updated evaluation metrics
  - `cancelled`: AI research stopped by user
  - `done`: AI finished processing
- **Frontend example:**
  ```javascript
  const source = new EventSource(`${API_BASE}/api/evaluations/${evaluationId}/ai/stream`, {
    withCredentials: true
  });

  source.addEventListener('connected', (event) => {
    const data = JSON.parse(event.data);
    console.log('SSE connected', data);
  });

  source.addEventListener('evaluation_created', (event) => {
    const data = JSON.parse(event.data);
    // Update UI with evaluation data (no listings yet)
    renderEvaluation(data);
  });

  source.addEventListener('listing_added', (event) => {
    const data = JSON.parse(event.data);
    // Update UI with new listing + updated evaluation metrics
    addListing(data.listing);
    updateEvaluation(data.evaluation);
  });

  source.addEventListener('done', (event) => {
    const data = JSON.parse(event.data);
    // Mark UI as finished
    finishEvaluationStream(data);
  });

  source.addEventListener('cancelled', (event) => {
    const data = JSON.parse(event.data);
    // Mark UI as cancelled
    cancelEvaluationStream(data);
  });

  source.onerror = () => {
    // Reconnect or show a warning if needed
    source.close();
  };
  ```

### Cancel AI Research
- **URL:** `/<evaluation_id>/ai/cancel`
- **Method:** `POST`
- **Auth Required:** Yes
- **Description:** Stops the AI research flow for the evaluation. The SSE stream emits `cancelled`.
- **Response:**
  - `200 OK`:
    ```json
    {
      "status": "cancelled",
      "evaluation_id": 1
    }
    ```

## 2. Get Evaluations
- **URL:** `/`
- **Method:** `GET`
- **Auth Required:** Yes
- **Description:** Retrieves a list of evaluations with optional filters, sorting, and pagination.
- **Query Params (optional):**
  - `classification`: Filter by classification (e.g., Venda, Aluguel).
  - `purpose`: Filter by purpose (e.g., Residencial, Comercial).
  - `appraiser_name`: Filter by appraiser name (partial match).
  - `min_price`: Minimum `rounded_price`.
  - `max_price`: Maximum `rounded_price`.
  - `start_date`: Start date/time for `created_at` (ISO 8601). If date-only, uses start of day.
  - `end_date`: End date/time for `created_at` (ISO 8601). If date-only, uses end of day.
  - `sort_dir`: `asc` or `desc` (default: `desc`) for `created_at`.
  - `page`: Page number (default: `1`).
  - `per_page`: Items per page (default: `20`).
- **Response:** JSON object with `items` and `meta`.
  ```json
  {
    "items": [
      {
        "id": 1,
        "address": "Rua Exemplo, 123",
        "neighborhood": "Centro",
        "city": "São Paulo",
        "state": "SP",
        "area": 100.0,
        "region_value_sqm": 5000.0,
        "analysis_type": "region",
        "owner_name": "João Silva",
        "appraiser_name": "Maria Souza",
        "estimated_price": 500000.0,
        "rounded_price": 500000.0,
        "description": "Avaliação realizada com base em imóveis da região.",
        "classification": "Venda",
        "purpose": "Residencial",
        "property_type": "Apartamento",
        "bedrooms": 3,
        "bathrooms": 2,
        "parking_spaces": 1,
        "analyzed_properties_count": 5,
        "active_listings_count": 5,
        "inactive_listings_count": 2,
        "total_listings_count": 7,
        "created_at": "2023-10-27T10:00:00"
      }
    ],
    "meta": {
      "total": 1,
      "page": 1,
      "per_page": 20,
      "total_pages": 1,
      "sort_dir": "desc"
    }
  }
  ```

## 3. Get Evaluation
- **URL:** `/<evaluation_id>`
- **Method:** `GET`
- **Auth Required:** Yes
- **Description:** Retrieves a specific evaluation by ID, including its associated base listings.
- **Response:** JSON object of the evaluation with `base_listings`.
  ```json
  {
    "id": 1,
    "address": "Rua Exemplo, 123",
    "neighborhood": "Centro",
    "city": "São Paulo",
    "state": "SP",
    "area": 100.0,
    "region_value_sqm": 5000.0,
    "analysis_type": "region",
    "owner_name": "João Silva",
    "appraiser_name": "Maria Souza",
    "estimated_price": 500000.0,
    "rounded_price": 500000.0,
    "description": "Avaliação realizada com base em imóveis da região.",
    "classification": "Venda",
    "purpose": "Residencial",
    "property_type": "Apartamento",
    "bedrooms": 3,
    "bathrooms": 2,
    "parking_spaces": 1,
    "analyzed_properties_count": 5,
    "active_listings_count": 5,
    "inactive_listings_count": 2,
    "total_listings_count": 7,
    "created_at": "2023-10-27T10:00:00",
    "base_listings": [
      {
        "id": 1,
        "evaluation_id": 1,
        "sample_number": 1,
        "address": "Rua Similar, 456",
        "neighborhood": "Centro",
        "city": "São Paulo",
        "state": "SP",
        "link": "http://...",
        "bedrooms": 2,
        "bathrooms": 1,
        "living_rooms": 1,
        "parking_spaces": 1,
        "collected_at": "2023-10-27T10:00:00",
        "rent_value": null,
        "condo_fee": 500.0,
        "purpose": "Residencial",
        "type": "Apartamento",
        "area": 95.0,
        "is_active": true,
        "deactivation_reason": null
      }
    ]
  }
  ```

## 4. Update Evaluation
- **URL:** `/<evaluation_id>`
- **Method:** `PUT`
- **Auth Required:** Yes
- **Description:** Updates an existing evaluation. If the `area` field is updated, the `region_value_sqm`, `estimated_price`, and `rounded_price` are automatically recalculated based on the associated base listings.
- **Body:** Fields to update.
- **Response:** JSON object of the updated evaluation.

## 5. Delete Evaluation
- **URL:** `/<evaluation_id>`
- **Method:** `DELETE`
- **Auth Required:** Yes
- **Description:** Deletes an evaluation.
- **Response:** Success message.

## 6. Create Base Listing
- **URL:** `/<evaluation_id>/listings`
- **Method:** `POST`
- **Description:** Adds a comparable listing to an evaluation. Automatically triggers a recalculation of the parent evaluation's metrics (`region_value_sqm`, `estimated_price`, `rounded_price`, `analyzed_properties_count`). The `sample_number` field can be used to identify the listing within the evaluation context.
- **Body:** Listing details (including optional `sample_number`, `is_active`, `deactivation_reason`).
  ```json
  {
    "sample_number": 1,
    "address": "Rua Exemplo, 123",
    "neighborhood": "Centro",
    "city": "São Paulo",
    "state": "SP",
    "link": "http://...",
    "bedrooms": 2,
    "bathrooms": 1,
    "living_rooms": 1,
    "parking_spaces": 1,
    "rent_value": 5000.0,
    "condo_fee": 500.0,
    "purpose": "Residencial",
    "type": "Apartamento",
    "area": 95.0,
    "is_active": true,
    "deactivation_reason": null
  }
  ```
- **Response:** JSON object of the created listing.

## 7. Get Base Listings
- **URL:** `/<evaluation_id>/listings`
- **Method:** `GET`
- **Description:** Retrieves all listings associated with an evaluation.
- **Response:** JSON list of listings.

## 8. Get Base Listing (Direct)
- **URL:** `/listings/<listing_id>`
- **Method:** `GET`
- **Description:** Retrieves a specific listing by ID.
- **Response:** JSON object of the listing.

## 9. Update Base Listing (Direct)
- **URL:** `/listings/<listing_id>`
- **Method:** `PUT`
- **Description:** Updates a specific listing. Automatically triggers a recalculation of the parent evaluation's metrics. Use `is_active` and `deactivation_reason` to activate/deactivate samples without deleting them.
- **Body (Example - Deactivate):**
  ```json
  {
    "is_active": false,
    "deactivation_reason": "Outlier - valor muito acima da média"
  }
  ```

---

## Sample Activation Management

### Overview
Samples (base_listings) can be activated/deactivated instead of deleted. Inactive samples are excluded from metric calculations but remain in the database for audit purposes.

### New Fields
- **`is_active`** (Boolean, default: `true`): Controls if sample is used in calculations
- **`deactivation_reason`** (Text, optional): Documents why sample was deactivated

### Metric Calculation Rules
Only **active** samples (`is_active = true`) are used to calculate:
- `region_value_sqm`
- `estimated_price`
- `rounded_price`
- `analyzed_properties_count`

### Evaluation Response Enhancements
Evaluation objects now include:
- `active_listings_count`: Number of active samples
- `inactive_listings_count`: Number of inactive samples
- `total_listings_count`: Total samples (active + inactive)

### Common Use Cases

**Deactivate outlier:**
```bash
PUT /api/evaluations/listings/123
{
  "is_active": false,
  "deactivation_reason": "Outlier - área muito diferente do alvo"
}
```

**Reactivate sample:**
```bash
PUT /api/evaluations/listings/123
{
  "is_active": true,
  "deactivation_reason": null
}
```

### SSE Events
Updating a listing triggers:
- **Event:** `listing_updated`
- **Channel:** `evaluation:{evaluation_id}`
- **Payload:** Updated listing + recalculated evaluation metrics

### Database Migration
Run script to add activation fields to existing database:
```bash
python scripts/add_sample_activation_fields.py
```

Existing samples are marked active by default.
- **Body (Example - Reactivate):**
  ```json
  {
    "is_active": true,
    "deactivation_reason": null
  }
  ```
- **Response:** JSON object of the updated listing. Triggers SSE event `listing_updated` on channel `evaluation:{evaluation_id}`.

## 10. Delete Base Listing (Direct)
- **URL:** `/listings/<listing_id>`
- **Method:** `DELETE`
- **Description:** Deletes a specific listing. Automatically triggers a recalculation of the parent evaluation's metrics.
- **Response:** Success message.
---

## Depreciation Management

### Overview
Evaluations support a depreciation percentage that is applied to the estimated price before rounding. This allows adjusting the final valuation to account for property depreciation factors.

### Depreciation Field
- **`depreciation`** (Float, default: `0.0`, range: `0-100`)
  - Percentage of depreciation to apply to the estimated price
  - User-defined value representing property depreciation

### Calculation Flow
The system calculates prices as follows:

1. **Calculate base estimated price:**
   ```
   estimated_price = area × region_value_sqm
   ```

2. **Apply depreciation:**
   ```
   price_after_depreciation = estimated_price × (1 - depreciation/100)
   ```

3. **Round the final value:**
   - **Sale (Venda):** Round to nearest R$ 10.000
   - **Rent (Aluguel):** Round to nearest R$ 10

**Example:**
- Area: 100 m²
- Region value: R$ 5.000/m²
- Depreciation: 15%
- Classification: Sale

```
estimated_price = 100 × 5000 = R$ 500.000
price_after_depreciation = 500000 × (1 - 15/100) = R$ 425.000
rounded_price = round(425000 / 10000) × 10000 = R$ 420.000
```

### API Usage

**Create evaluation with depreciation:**
```bash
POST /api/evaluations
{
  "address": "Rua Exemplo, 123",
  "area": 100.0,
  "depreciation": 15.0,
  ...
}
```

**Update depreciation:**
```bash
PUT /api/evaluations/123
{
  "depreciation": 20.0
}
```

When `depreciation` or `area` is updated, metrics are automatically recalculated.

### Database Migration
Run script to add depreciation field to existing evaluations:
```bash
python scripts/add_depreciation_field.py
```

Existing evaluations are set to 0% depreciation by default.