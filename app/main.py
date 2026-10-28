from fastapi import Depends,FastAPI,Form, HTTPException, Response, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order,Product, User
from app.schemas import OrderCreate, OrderOut, OrderUpdate
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.auth import (
    hash_password, 
    verify_password,
    create_access_token,
    decode_access_token)


app= FastAPI(title="Orders API")

oauth2_scheme= OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(
        token: str= Depends(oauth2_scheme),
        db: Session= Depends(get_db),
) -> User:
    """Retrieve the authenticated user from the access token.

    Args:
        token: The JWT access token extracted from the request.
        db: The database session used to retrieve the user.

    Returns:
        The User object associated with the token.

    Raises:
        HTTPException: If the token is invalid or expired, or if the
            user associated with the token no longer exists.
    """
    user_id= decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail= "Invalid or expired token"
        )
    user= db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User no longer exists"
        )
    return user

def require_admin(current_user: User= Depends(get_current_user)) -> User:
    """Verify that the current user has administrator privileges.

    Args:
        current_user: The authenticated user retrieved from the access token.

    Returns:
        The current user if they have the admin role.

    Raises:
        HTTPException: If the current user does not have administrator
            privileges, with status code 403 (Forbidden).
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403,
                            detail="Admin access required")
    return current_user

@app.post("/register", description="Register a new account by providing your full name, email address (username), and password.")
def register(
    full_name: str =Form(...),
    form_data: OAuth2PasswordRequestForm= Depends(),
    db: Session= Depends(get_db)): 
    """Register a new user account.

    Args:
        full_name: The full name of the user submitted through the form.
        form_data: The submitted username (used as the email address)
            and password.
        db: The database session used to check and create the user.

    Returns:
        dict: A success message and the registered user's email and
        full name.

    Raises:
        HTTPException: If a user with the submitted email already exists,
            with status code 409 (Conflict).
    """
    user= db.query(User).filter(
        User.email == form_data.username
    ).first()
    if user is not None:
        raise HTTPException(
            status_code= 409,
            detail="User already exists")

    register_this= hash_password(form_data.password)
    new_user= User(
        email= form_data.username,
        full_name= full_name,
        hashed_password= register_this
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return{
        "message": "User registered successfully",
        "email": new_user.email,
        "full_name": new_user.full_name
    }

@app.post("/token", description= "Log in using your email address and password.")
def login(form:OAuth2PasswordRequestForm= Depends(), db: Session= Depends(get_db)):
    """Authenticate a user and generate a JWT access token.

    Args:
        form: The submitted login credentials, where username contains
            the user's email address and password contains the plain-text
            password.
        db: The database session used to retrieve the user.

    Returns:
        dict: A dictionary containing the JWT access token and its
        token type ("bearer").

    Raises:
        HTTPException: If the email address is not found or the password
            is incorrect, with status code 401 (Unauthorized).
    """
    user= db.query(User).filter(User.email == form.username).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Incorrect email or password",
        )
    token= create_access_token(user.id)
    return {"access_token": token, "token_type":"bearer"}
    


@app.get("/me")
def read_me(current_user: User= Depends(get_current_user)):
    """Retrieve the profile information of the authenticated user.

    Args:
        current_user: The authenticated user obtained from the access token.

    Returns:
        dict: A dictionary containing the user's ID, email address,
        and role.
    """
    return {"id": current_user.id, "email": current_user.email,"role": current_user.role}


#CREATE

@app.post("/orders", response_model=OrderOut, status_code= 201, 
          description="Only authenticated users can create orders by providing the product ID and quantity.")  
def create_order(payload:OrderCreate, 
                 db: Session= Depends(get_db),
                 current_user: User= Depends(get_current_user)):
    """Create a new order for the authenticated user.

    Args:
        payload: The order details, including the product ID and quantity.
        db: The database session used to retrieve the product and save
            the new order.
        current_user: The authenticated user who is placing the order.

    Returns:
        Order: The newly created order, serialized according to OrderOut.

    Raises:
        HTTPException: If the specified product does not exist, with
            status code 400 (Bad Request).
    """
    product= db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(
            status_code= 400, 
            detail= "product_id does not exist"
        )
    order= Order(user_id= current_user.id,
                 product_id=payload.product_id,
                 quantity= payload.quantity, 
                 status="pending")
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


#READ ORDERS LIST

@app.get(
    "/orders",
    response_model=list[OrderOut],
    description="Retrieve orders. Regular users can view only their own orders. Admins can view all users' orders.",
)
def list_orders(
    user_id: int | None = Query(None, description="Filter orders by user ID. Admins only need this to view a specific user's orders.", example=88),
    status: str | None = Query(None, description="Filter orders by status, for example: pending."),
    product_id: int | None = Query(None, description="Filter orders by product ID, for example: 78."),
    skip: int = Query(0, ge=0, description="Number of orders to skip. Default: 0."),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of orders to return (1–100). Default: 20.", example=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve orders based on user role and optional filters.

    Admins can view orders from all users and optionally filter by user ID.
    Regular users can view only their own orders.

    Args:
        user_id: Optional ID used to filter orders by user. Regular users
            cannot request another user's orders.
        status: Optional order status used to filter results.
        product_id: Optional product ID used to filter results.
        skip: Number of orders to skip for pagination. Must be non-negative.
        limit: Maximum number of orders to return. Must be between 1 and 100.
        db: The database session used to query orders.
        current_user: The authenticated user making the request.

    Returns:
        list[OrderOut]: A list of orders matching the filters, serialized
        according to the OrderOut schema.

    Raises:
        HTTPException: If a regular user attempts to view another user's
            orders, with status code 403 (Forbidden).
    """

    query= db.query(Order)

    if current_user.role == "admin":
        if user_id is not None:
            query= query.filter(Order.user_id == user_id) 

    else:
        if user_id is not None and user_id != current_user.id:
                
            raise HTTPException(
                status_code= 403,
                detail= "You are not allwed to view others' orders"
            )
        query= query.filter(Order.user_id == current_user.id)  
    

    if status is not None:
        query= query.filter(Order.status == status)

    if product_id is not None:
        query= query.filter(Order.product_id == product_id)
    

    return query.order_by(Order.id).offset(skip).limit(limit).all()


#READ SINGLE ORDER

@app.get("/orders/{order_id}", response_model=OrderOut, description="Retrieve a specific order by its ID. Only the order owner or an administrator can access it.")
def get_order(order_id: int,
              db: Session= Depends(get_db),
              current_user: User= Depends(get_current_user)):
    """Retrieve a specific order by its ID.

    Admins can view any order, while regular users can view only their
    own orders.

    Args:
        order_id: The ID of the order to retrieve.
        db: The database session used to retrieve the order.
        current_user: The authenticated user making the request.

    Returns:
        Order: The requested order, serialized according to OrderOut.

    Raises:
        HTTPException: If the order does not exist, with status code
            404 (Not Found).
        HTTPException: If a regular user attempts to view another user's
            order, with status code 403 (Forbidden).
    """
    order= db.get(Order, order_id)
    
    if order is None:
        raise HTTPException(status_code= 404, detail= "Order not found")

    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not allowed to view this order"

        )

    return order

# UPDATE

@app.patch("/orders/{order_id}", response_model= OrderOut, 
           description="Update an existing order. Only the order owner or an administrator can update it.")
def update_order(
    order_id: int, 
    payload: OrderUpdate, 
    db: Session= Depends(get_db),
    current_user: User= Depends(get_current_user)):
    """Update an existing order.

    Admins can update any order, while regular users can update only
    their own orders.

    Args:
        order_id: The ID of the order to update.
        payload: The fields to update. Only fields explicitly provided
            in the request are applied.
        db: The database session used to retrieve and update the order.
        current_user: The authenticated user making the request.

    Returns:
        Order: The updated order, serialized according to OrderOut.

    Raises:
        HTTPException: If the order does not exist, with status code
            404 (Not Found).
        HTTPException: If a regular user attempts to update another
            user's order, with status code 403 (Forbidden).
    """
    order= db.get(Order, order_id)
    if order is None:
        raise HTTPException(
            status_code= 404,
            detail= "Order not found")

    if current_user.role != 'admin' and current_user.id != order.user_id:
        raise HTTPException(
            status_code= 403,
            detail= "Not allowed to view this order"
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)
    
    return order


# DELETE

@app.delete("/orders/{order_id}", status_code= 204,
            description="Delete an existing order.Only admin can delete the orders")
def delete_order(order_id: int, 
                 db: Session= Depends(get_db),
                 admin: User= Depends(require_admin)):
    """Delete an existing order.

    Only users with administrator privileges can delete orders.

    Args:
        order_id: The ID of the order to delete.
        db: The database session used to retrieve and delete the order.
        admin: The authenticated administrator authorized to perform
            this operation.

    Raises:
        HTTPException: If the order does not exist, with status code
            404 (Not Found).

    Returns:
        Response: An empty HTTP response with status code 204 (No Content).
    """
    order= db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return Response(status_code=204)


@app.get("/products", description="Retrieve all products or a specific product by its ID." )
def get_products(
    product_id: int | None=None,
    current_user: User= Depends(get_current_user),
    db: Session= Depends(get_db)
):
    """Retrieve all products or a specific product by its ID.

    Any authenticated user can access this endpoint.

    Args:
        product_id: Optional ID of the product to retrieve. If omitted,
            all products are returned.
        current_user: The authenticated user making the request.
        db: The database session used to query products.

    Returns:
        list[Product]: A list of products, or a list containing the
        requested product when product_id is provided.

    Raises:
        HTTPException: If a specific product ID is provided but no
            matching product exists, with status code 404 (Not Found).
    """
    query= db.query(Product)

    if product_id is not None:
        query= query.filter(Product.id == product_id)
        
    products= query.all()
    
    if product_id is not None and not products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    return products


@app.get("/products/{id}", description="Retrieve a specific product by its ID." )
def get_product_id(
    id: int,
    current_user: User= Depends(get_current_user),
    db: Session= Depends(get_db)
):
    """Retrieve a specific product by its ID.

    Any authenticated user can access this endpoint.

    Args:
        id: The ID of the product to retrieve.
        current_user: The authenticated user making the request.
        db: The database session used to retrieve the product.

    Returns:
        Product: The product matching the specified ID.

    Raises:
        HTTPException: If no product exists with the specified ID,
            with status code 404 (Not Found).
    """
    product= db.get(Product, id)

    if product is None:
        raise HTTPException(
            status_code= 404,
            detail="Product not found"
        )
    return product


    