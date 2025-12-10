# Dashboard Routes

This document describes the API routes for the Dashboard.

## Authentication

All routes in this module require authentication.
The API uses **JWT (JSON Web Token)** authentication. You must include the JWT token obtained from the `/auth/login` endpoint in the `Authorization` header of your requests.

*   **Auth Required:** Yes
*   **Auth Type:** Bearer Token
*   **Header:** `Authorization: Bearer <your_access_token>`

## Get Summary Statistics

Retrieves high-level summary statistics for the dashboard.

*   **URL:** `/api/dashboard/summary`
*   **Method:** `GET`
*   **Auth Required:** Yes
*   **Success Response:**
    *   **Code:** 200
    *   **Content:**
        ```json
        {
            "total_evaluations": 150,
            "total_users": 25,
            "total_conversations": 42,
            "average_price_sqm": 5432.10
        }
        ```
*   **Error Response:**
    *   **Code:** 500
    *   **Content:** `{"error": "Error message description"}`

## Get Charts Data

Retrieves aggregated data suitable for rendering charts (e.g., evaluations by city, property type, purpose).

*   **URL:** `/api/dashboard/charts`
*   **Method:** `GET`
*   **Auth Required:** Yes
*   **Success Response:**
    *   **Code:** 200
    *   **Content:**
        ```json
        {
            "evaluations_by_city": {
                "São Paulo": 120,
                "Rio de Janeiro": 30
            },
            "evaluations_by_type": {
                "Apartment": 100,
                "House": 50
            },
            "evaluations_by_purpose": {
                "Residential": 140,
                "Commercial": 10
            }
        }
        ```
*   **Error Response:**
    *   **Code:** 500
    *   **Content:** `{"error": "Error message description"}`

## Get Evaluation Trends

Retrieves evaluation trends over time (count and average price/sqm).

*   **URL:** `/api/dashboard/trends`
*   **Method:** `GET`
*   **Auth Required:** Yes
*   **Success Response:**
    *   **Code:** 200
    *   **Content:**
        ```json
        {
            "trends": [
                {
                    "date": "2023-10-01",
                    "count": 5,
                    "avg_sqm": 5000.00
                },
                ...
            ]
        }
        ```

## Get Price Distribution

Retrieves price distribution data for histograms.

*   **URL:** `/api/dashboard/distribution`
*   **Method:** `GET`
*   **Auth Required:** Yes
*   **Success Response:**
    *   **Code:** 200
    *   **Content:**
        ```json
        {
            "distribution": {
                "0-1000": 5,
                "1000-2000": 15,
                ...
            }
        }
        ```

## Get Geographic Statistics

Retrieves top cities and neighborhoods by average price.

*   **URL:** `/api/dashboard/geographic`
*   **Method:** `GET`
*   **Auth Required:** Yes
*   **Success Response:**
    *   **Code:** 200
    *   **Content:**
        ```json
        {
            "top_cities_by_price": [
                {"city": "São Paulo", "avg_price": 6000.00},
                ...
            ],
            "top_neighborhoods_by_price": [
                {"neighborhood": "Vila Mariana", "city": "São Paulo", "avg_price": 7000.00},
                ...
            ]
        }
        ```

## Get Property Features Statistics

Retrieves statistics based on property features (bedrooms, parking).

*   **URL:** `/api/dashboard/features`
*   **Method:** `GET`
*   **Auth Required:** Yes
*   **Success Response:**
    *   **Code:** 200
    *   **Content:**
        ```json
        {
            "price_by_bedrooms": {
                "1": 5000.00,
                "2": 5500.00,
                ...
            },
            "price_by_parking": {
                "0": 4500.00,
                "1": 5200.00,
                ...
            }
        }
        ```
