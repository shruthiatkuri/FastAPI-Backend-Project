from app.database import SessionLocal
from langchain.tools import tool
from app.models import Product

@tool
def get_product_price(product_id:int)->str:
    """Get the name and price of a product using its product ID."""
    """
    Retrieve a product's name and price from the database using its product ID.

    Queries the PostgreSQL database to find the product matching the
    provided product ID. Returns the product name and price if the
    product exists, or a not-found message if no matching product
    is found.

    Args:
        product_id (int): Unique identifier of the product to look up.

    Returns:
        str: A string containing the product name and price, or a
            message indicating that the product was not found.

    Note:
        The database session is closed after the query, including when
        an exception occurs.
    """
    
    db=SessionLocal()

    try:
        product= db.get(Product, product_id)

        if product is None:
            return f"Product with ID {product_id} was not found."

        return f"{product.name} cost ${product.price}"

    finally:
      db.close()