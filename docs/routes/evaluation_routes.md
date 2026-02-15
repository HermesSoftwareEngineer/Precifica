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
    "parking_spaces": number
  }
  ```
- **Response:** JSON representation of the created evaluation (including auto-calculated fields).

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
        "area": 95.0
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
- **Body:** Listing details (including optional `sample_number`).
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
- **Description:** Updates a specific listing. Automatically triggers a recalculation of the parent evaluation's metrics.
- **Response:** JSON object of the updated listing.

## 10. Delete Base Listing (Direct)
- **URL:** `/listings/<listing_id>`
- **Method:** `DELETE`
- **Description:** Deletes a specific listing. Automatically triggers a recalculation of the parent evaluation's metrics.
- **Response:** Success message.
