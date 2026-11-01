import os
from dotenv import load_dotenv
import httpx
from uuid import uuid4

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"


def create_authenticated_user(client):
    """Register a user and return their authentication headers."""

    email = f"order_test_{uuid4().hex[:8]}@example.com"
    password = "password123"

    register_response = client.post(
        "/register",
        data={
            "username": email,
            "password": password,
            "full_name": "Order Test User"
        }
    )

    assert register_response.status_code in (200, 201)

    login_response = client.post(
        "/token",
        data={
            "username": email,
            "password": password
        }
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

def test_order_workflow():
    with httpx.Client(base_url=BASE_URL) as client:

        # 1. Register and authenticate a user
        headers = create_authenticated_user(client)

        # 2. Retrieve products to get a valid product ID
        products_response = client.get(
            "/products",
            headers=headers
        )

        assert products_response.status_code == 200

        products = products_response.json()
        assert len(products) > 0

        product_id = products[0]["id"]

        # 3. Create an order
        order_response = client.post(
            "/orders",
            json={
                "product_id": product_id,
                "quantity": 2
            },
            headers=headers
        )

        assert order_response.status_code in (200, 201)

        order = order_response.json()
        order_id = order["id"]

        # 4. Retrieve all orders belonging to the user
        orders_response = client.get(
            "/orders",
            headers=headers
        )

        assert orders_response.status_code == 200

        orders = orders_response.json()
        assert any(item["id"] == order_id for item in orders)

        # 5. Retrieve one specific order
        single_order_response = client.get(
            f"/orders/{order_id}",
            headers=headers
        )
        assert single_order_response.status_code == 200
        assert single_order_response.json()["id"] == order_id

        # 6. Update the order
        update_response = client.patch(
            f"/orders/{order_id}",
            json={
                "quantity": 3,
                "status": "shipped"
            },
            headers=headers
        )

        assert update_response.status_code == 200

        # Verify the updated order
        updated_order_response = client.get(
            f"/orders/{order_id}",
            headers=headers
        )

        assert updated_order_response.status_code == 200
        assert updated_order_response.json()["quantity"] == 3
        assert updated_order_response.json()["status"] == "shipped"


def test_get_orders_without_authentication():
    response = httpx.get(f"{BASE_URL}/orders")

    assert response.status_code in (401, 403)


def test_create_order_without_authentication():
    response = httpx.post(
        f"{BASE_URL}/orders",
        json={
            "product_id": 3,
            "quantity": 2
        }
    )

    assert response.status_code in (401, 403)


def test_customer_cannot_delete_order():
    with httpx.Client(base_url=BASE_URL) as client:

        # 1. Register and authenticate a customer
        headers = create_authenticated_user(client)

        # 2. Get a valid product ID
        products_response = client.get(
            "/products",
            headers=headers
        )

        assert products_response.status_code == 200

        product_id = products_response.json()[0]["id"]

        # 3. Create an order
        order_response = client.post(
            "/orders",
            json={
                "product_id": product_id,
                "quantity": 2
            },
            headers=headers
        )

        assert order_response.status_code in (200, 201)

        order_id = order_response.json()["id"]

        # 4. Attempt to delete the order as a customer
        delete_response = client.delete(
            f"/orders/{order_id}",
            headers=headers
        )

        # 5. Customer should not have permission
        assert delete_response.status_code == 403

def get_admin_auth_headers(client):
    """Log in as an existing admin and return authentication headers."""

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    assert admin_email is not None, "ADMIN_EMAIL is missing from .env"
    assert admin_password is not None, "ADMIN_PASSWORD is missing from .env"

    login_response = client.post(
        "/token",
        data={
            "username": admin_email,
            "password": admin_password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

def test_admin_can_delete_order():
    with httpx.Client(base_url=BASE_URL) as client:

        # 1. Authenticate as admin
        headers = get_admin_auth_headers(client)

        # 2. Get a valid product ID
        products_response = client.get(
            "/products",
            headers=headers
        )

        assert products_response.status_code == 200

        product_id = products_response.json()[0]["id"]

        # 3. Create an order
        order_response = client.post(
            "/orders",
            json={
                "product_id": product_id,
                "quantity": 2
            },
            headers=headers
        )

        assert order_response.status_code in (200, 201)

        order_id = order_response.json()["id"]

        # 4. Delete the order as admin
        delete_response = client.delete(
            f"/orders/{order_id}",
            headers=headers
        )

        assert delete_response.status_code == 204

        # 5. Verify the order no longer exists
        get_response = client.get(
            f"/orders/{order_id}",
            headers=headers
        )

        assert get_response.status_code == 404

def test_customer_cannot_access_another_customers_order():
    with httpx.Client(base_url=BASE_URL) as client:

        # 1. Create Customer A
        customer_a_headers = create_authenticated_user(client)

        # 2. Customer A creates an order
        products_response = client.get(
            "/products",
            headers=customer_a_headers
        )

        assert products_response.status_code == 200

        product_id = products_response.json()[0]["id"]

        order_response = client.post(
            "/orders",
            json={
                "product_id": product_id,
                "quantity": 2
            },
            headers=customer_a_headers
        )

        assert order_response.status_code in (200, 201)

        order_id = order_response.json()["id"]

        # 3. Create Customer B
        customer_b_headers = create_authenticated_user(client)

        # 4. Customer B tries to access Customer A's order
        response = client.get(
            f"/orders/{order_id}",
            headers=customer_b_headers
        )

        # 5. Customer B should not have access
        assert response.status_code == 403

def test_customer_cannot_update_another_customers_order():
    with httpx.Client(base_url=BASE_URL) as client:

        # 1. Create Customer A
        customer_a_headers = create_authenticated_user(client)

        # 2. Customer A creates an order
        products_response = client.get(
            "/products",
            headers=customer_a_headers
        )

        assert products_response.status_code == 200

        product_id = products_response.json()[0]["id"]

        order_response = client.post(
            "/orders",
            json={
                "product_id": product_id,
                "quantity": 2
            },
            headers=customer_a_headers
        )

        assert order_response.status_code in (200, 201)

        order_id = order_response.json()["id"]

        # 3. Create Customer B
        customer_b_headers = create_authenticated_user(client)

        # 4. Customer B attempts to update Customer A's order
        response = client.patch(
            f"/orders/{order_id}",
            json={"quantity": 10},
            headers=customer_b_headers
        )

        # 5. Customer B should not have permission
        assert response.status_code == 403