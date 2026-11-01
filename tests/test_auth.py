import httpx
from uuid import uuid4

BASE_URL = "http://127.0.0.1:8000"

def test_authentication_workflow():
    email= f"test_{uuid4().hex[:8]}@example.com"
    password="password123"

    with httpx.Client(base_url=BASE_URL) as client:

        """Register a new User"""
        register_response= client.post(
            "/register",
            data={
                "username": email,
                "password": password,
                "full_name": "Test User"
            }
        )

        assert register_response.status_code in (200, 201)


        """Log in and obtain access token"""
        login_response= client.post(
            "/token",
            data={
                "username": email,
                "password": password
            }
        )

        assert login_response.status_code == 200

        token= login_response.json()["access_token"]

        """Use token to access protected endpoint"""
        headers= {"Authorization": f"Bearer {token}"}

        me_response= client.get("/me", headers=headers)

        assert me_response.status_code == 200
        assert me_response.json()["email"] == email
        