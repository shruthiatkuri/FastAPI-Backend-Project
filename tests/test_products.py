import httpx

BASE_URL= "http://127.0.0.1:8000"


def get_auth_headers():
    """Register a user, log in, and return authentication headers."""
    with httpx.Client(base_url=BASE_URL) as client:
        client.post(
            "/register",
            data={
                "username": "products_test@example.com",
                "password": "password123",
                "full_name": "Products Test User"
                }
        )
        login_response = client.post(
            "/token",
            data={
                "username": "products_test@example.com",
                "password": "password123"
            }
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

def test_get_all_products():
    headers = get_auth_headers()

    response = httpx.get(
        f"{BASE_URL}/products",
        headers=headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_single_product():
    headers = get_auth_headers()

    products_response = httpx.get(
        f"{BASE_URL}/products",
        headers=headers
    )

    assert products_response.status_code == 200

    products = products_response.json()

    if not products:
        import pytest
        pytest.skip("No products available in the database")

    product_id = products[0]["id"]

    response = httpx.get(
        f"{BASE_URL}/products/{product_id}",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == product_id

def test_get_products_without_authentication():
    response = httpx.get(f"{BASE_URL}/products")

    assert response.status_code in (401, 403)


def test_get_single_product_without_authentication():
    response = httpx.get(f"{BASE_URL}/products/1")

    assert response.status_code in (401, 403)