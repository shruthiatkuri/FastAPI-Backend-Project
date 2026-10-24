# FastAPI Backend Project

A backend application built with FastAPI and PostgreSQL, featuring user authentication, JWT-based authorization, product retrieval, and order management.

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/shruthiatkuri/FastAPI-Backend-Project.git
cd FastAPI-Backend-project
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv .venv
```

On Windows, activate the virtual environment:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root using `.env.example` as a reference.

Add your own values for the required environment variables, such as database connection settings and authentication secrets.

```bash
DATABASE_URL=postgresql://database:yourpassword@localhost:5432/databasename
SECRET_KEY=Add-your-secret-key
```

Ensure PostgreSQL is running and the database is configured before starting the application.

### 5. Start the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 6. Explore the API

Once the server is running, open either of these URLs in your browser:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

## Authentication

The application uses JWT-based authentication to protect endpoints.

1. Register a user using `POST /register`.
2. Log in using `POST /token` with the registered credentials.
3. Copy the `access_token` from the login response.
4. Use the token as a Bearer token when accessing protected endpoints.

## Testing

Run the test file to check the API endpoints:

```bash
python test.py
```

Review the output to verify that the tests execute successfully. Ensure that the required database and environment variables are configured before running the tests.

## Testing with Postman

Start the FastAPI server before sending requests from Postman.

### 1. Register a User

- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/register`
- **Body:** `x-www-form-urlencoded`
- **Fields:** `username`, `password`, and `full_name`

Use the same credentials for the login request.

### 2. Log In

- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/token`
- **Body:** `x-www-form-urlencoded`
- **Fields:** `username` and `password`

Copy the `access_token` from the response.

### 3. Configure Authorization

For protected requests:

1. Open the **Authorization** tab in Postman.
2. Select **Bearer Token** from the Auth Type dropdown.
3. Paste the copied access token into the Token field.

Reuse the token for subsequent requests until it expires or becomes invalid.

### 4. Create an Order

- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/orders`
- **Authorization:** Bearer Token
- **Body:** `raw` → `JSON`

Example request body:

```json
{
  "product_id": 3,
  "quantity": 2
}
```

The application assigns the order to the authenticated user.

### 5. Retrieve an Order

- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/orders/{order_id}`

Replace `{order_id}` with the actual ID returned when the order was created. Use the same Bearer token.

### 6. Update an Order

- **Method:** `PATCH`
- **URL:** `http://127.0.0.1:8000/orders/{order_id}`
- **Body:** `raw` → `JSON`

Example:

```json
{
  "quantity": 3
}
```

Use the appropriate order ID and a valid update field.

## Notes

- Ensure PostgreSQL is running and the required environment variables are configured.
- Use valid product IDs when creating orders.
- Protected endpoints require a valid access token.
- Some operations require administrator privileges.

