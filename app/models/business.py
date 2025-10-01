"""
Business-related Pydantic models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class Product(BaseModel):
    """Product model"""
    id: int = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    price: Decimal = Field(..., description="Product price")
    description: Optional[str] = Field(default=None, description="Product description")
    launch_date: Optional[datetime] = Field(default=None, description="Product launch date")
    status: str = Field(default="active", description="Product status")
    rating: Optional[float] = Field(default=None, description="Average rating")
    review_count: Optional[int] = Field(default=0, description="Number of reviews")

class Customer(BaseModel):
    """Customer model"""
    id: int = Field(..., description="Customer ID")
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email")
    registration_date: datetime = Field(..., description="Registration date")
    segment: str = Field(..., description="Customer segment")
    lifetime_value: Decimal = Field(..., description="Customer lifetime value")
    total_orders: Optional[int] = Field(default=0, description="Total number of orders")
    last_order_date: Optional[datetime] = Field(default=None, description="Last order date")

class Order(BaseModel):
    """Order model"""
    id: int = Field(..., description="Order ID")
    customer_id: int = Field(..., description="Customer ID")
    product_id: int = Field(..., description="Product ID")
    order_date: datetime = Field(..., description="Order date")
    quantity: int = Field(..., description="Quantity ordered")
    total_amount: Decimal = Field(..., description="Total order amount")
    status: str = Field(..., description="Order status")
    
class Review(BaseModel):
    """Review model"""
    id: int = Field(..., description="Review ID")
    product_id: int = Field(..., description="Product ID")
    customer_id: int = Field(..., description="Customer ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    review_text: Optional[str] = Field(default=None, description="Review text")
    review_date: datetime = Field(..., description="Review date")
    sentiment: Optional[str] = Field(default=None, description="Sentiment analysis result")
    helpful_votes: Optional[int] = Field(default=0, description="Number of helpful votes")

class SalesPerformance(BaseModel):
    """Sales performance model"""
    id: int = Field(..., description="Record ID")
    product_id: int = Field(..., description="Product ID")
    month: datetime = Field(..., description="Month")
    units_sold: int = Field(..., description="Units sold")
    revenue: Decimal = Field(..., description="Revenue generated")
    region: str = Field(..., description="Sales region")
    growth_rate: Optional[float] = Field(default=None, description="Growth rate percentage")

class BusinessSummary(BaseModel):
    """Business summary analytics model"""
    total_products: int = Field(..., description="Total number of products")
    total_customers: int = Field(..., description="Total number of customers")
    total_orders: int = Field(..., description="Total number of orders")
    avg_rating: float = Field(..., description="Average product rating")
    monthly_revenue: Decimal = Field(..., description="Current month revenue")
    top_categories: List[str] = Field(..., description="Top performing categories")
    customer_segments: List[str] = Field(..., description="Customer segments")
    growth_metrics: dict = Field(..., description="Various growth metrics")