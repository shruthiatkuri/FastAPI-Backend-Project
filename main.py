from fastapi import Depends,FastAPI,Form, HTTPException, Response, Query, status
from sqlalchemy.orm import Session
from database import get_db
from models import Order,Product, User
from schemas import OrderCreate, OrderOut, OrderUpdate
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth import (
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
    if current_user.role != "admin":
        raise HTTPException(status_code=403,
                            detail="Admin access required")
    return current_user

@app.post("/register")
def register(
    full_name: str =Form(...),
    form_data: OAuth2PasswordRequestForm= Depends(),
    db: Session= Depends(get_db)): 
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
        "message": "User registed successfully",
        "email": new_user.email,
        "full_name": new_user.full_name
    }

@app.post("/token")
def login(form:OAuth2PasswordRequestForm= Depends(), db: Session= Depends(get_db)):
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
    return {"id": current_user.id, "email": current_user.email,"role": current_user.role}


#CREATE

@app.post("/orders", response_model=OrderOut, status_code= 201)
def create_order(payload:OrderCreate, 
                 db: Session= Depends(get_db),
                 current_user: User= Depends(get_current_user)):
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

@app.get("/orders", response_model=list[OrderOut])
def list_orders(
    user_id: int | None=None,
    status: str | None= None,
    product_id: int | None= None,
    skip: int = Query(0, ge=0),
    limit:int= Query(20, ge=1, le=100),
    db: Session= Depends(get_db),
    current_user: User= Depends(get_current_user)):

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

@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int,
              db: Session= Depends(get_db),
              current_user: User= Depends(get_current_user)):
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

@app.patch("/orders/{order_id}", response_model= OrderOut)
def update_order(
    order_id: int, 
    payload: OrderUpdate, 
    db: Session= Depends(get_db),
    current_user: User= Depends(get_current_user)):
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

@app.delete("/orders/{order_id}", status_code= 204)
def delete_order(order_id: int, 
                 db: Session= Depends(get_db),
                 admin: User= Depends(require_admin)):
    order= db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return Response(status_code=204)


@app.get("/products")
def get_products(
    product_id: int | None=None,
    current_user: User= Depends(get_current_user),
    db: Session= Depends(get_db)
):
    query= db.query(Product)

    if product_id is not None:
        query= query.filter(Product.id == product_id)
        
    Products= query.all()
    
    if product_id is not None and not Products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    return Products


@app.get("/products/{id}")
def get_products_id(
    id: int,
    current_user: User= Depends(get_current_user),
    db: Session= Depends(get_db)
):
    product= db.get(Product, id)

    if product is None:
        raise HTTPException(
            status_code= 404,
            detail="Product not found"
        )
    return product


    