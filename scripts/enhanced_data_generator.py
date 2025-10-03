"""
Enhanced Business Database Generator with Comprehensive Data
Creates realistic, demo-ready databases with extensive data for different business types
"""

import asyncio
import random
import json
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker
import sqlite3
import os
from typing import Dict, List, Any

# Initialize Faker with default locale to avoid startup delays
fake = Faker()

class EnhancedBusinessDataGenerator:
    """Enhanced data generator for realistic business databases"""
    
    def __init__(self, business_type: str, company_name: str, company_description: str):
        self.business_type = business_type.lower()
        self.company_name = company_name
        self.company_description = company_description
        self.fake = fake
        
        # Business-specific configurations
        self.business_configs = {
            'retail': {
                'categories': ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Beauty', 'Books', 'Automotive', 'Toys'],
                'customer_segments': ['VIP', 'Premium', 'Standard', 'Budget'],
                'locations': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego'],
                'departments': ['Sales', 'Marketing', 'Customer Service', 'Inventory', 'Logistics', 'Finance', 'HR'],
                'product_count': 150,
                'customer_count': 800,
                'review_count': 2000,
                'order_count': 3000
            },
            'ecommerce': {
                'categories': ['Electronics', 'Fashion', 'Home', 'Sports', 'Beauty', 'Books', 'Tech Gadgets', 'Health'],
                'customer_segments': ['New', 'Returning', 'Loyal', 'VIP'],
                'locations': ['Online - US', 'Online - Canada', 'Online - UK', 'Online - Australia', 'Mobile App'],
                'departments': ['Digital Marketing', 'Customer Success', 'Product Management', 'DevOps', 'Analytics'],
                'product_count': 200,
                'customer_count': 1200,
                'review_count': 3500,
                'order_count': 5000
            },
            'healthcare': {
                'categories': ['Cardiology', 'Pediatrics', 'Orthopedics', 'Dermatology', 'Neurology', 'Emergency'],
                'patient_segments': ['Pediatric', 'Adult', 'Senior', 'Critical Care'],
                'locations': ['Main Hospital', 'Outpatient Clinic', 'Emergency Dept', 'Surgery Center', 'Lab'],
                'departments': ['Medical', 'Nursing', 'Administration', 'Laboratory', 'Pharmacy', 'Radiology'],
                'service_count': 100,
                'patient_count': 600,
                'appointment_count': 2500,
                'treatment_count': 1800
            },
            'finance': {
                'categories': ['Checking', 'Savings', 'Loans', 'Credit Cards', 'Investments', 'Insurance'],
                'customer_segments': ['Basic', 'Premium', 'Private Banking', 'Business'],
                'locations': ['Downtown Branch', 'Mall Branch', 'Online Banking', 'Mobile App', 'ATM Network'],
                'departments': ['Retail Banking', 'Commercial Banking', 'Investment Services', 'Risk Management', 'Compliance'],
                'product_count': 50,
                'customer_count': 1000,
                'transaction_count': 8000,
                'account_count': 1500
            },
            'education': {
                'categories': ['Mathematics', 'Science', 'English', 'History', 'Arts', 'Physical Education', 'Computer Science'],
                'student_segments': ['Elementary', 'Middle School', 'High School', 'Special Needs'],
                'locations': ['Main Campus', 'Science Lab', 'Library', 'Gymnasium', 'Cafeteria', 'Auditorium'],
                'departments': ['Academic', 'Administration', 'Student Services', 'Facilities', 'Technology', 'Counseling'],
                'course_count': 80,
                'student_count': 500,
                'enrollment_count': 1200,
                'grade_count': 3000
            },
            'manufacturing': {
                'categories': ['Raw Materials', 'Components', 'Finished Goods', 'Packaging', 'Tools', 'Safety Equipment'],
                'supplier_segments': ['Primary', 'Secondary', 'Local', 'International'],
                'locations': ['Factory Floor', 'Warehouse', 'Quality Control', 'Shipping Dock', 'Office'],
                'departments': ['Production', 'Quality Assurance', 'Supply Chain', 'Maintenance', 'Safety', 'Engineering'],
                'product_count': 120,
                'supplier_count': 200,
                'production_count': 2000,
                'inventory_count': 1500
            }
        }
    
    def get_business_config(self) -> Dict[str, Any]:
        """Get configuration for the specific business type"""
        return self.business_configs.get(self.business_type, self.business_configs['retail'])
    
    def generate_realistic_reviews(self, product_id: int, product_name: str, category: str) -> List[Dict]:
        """Generate realistic, detailed customer reviews"""
        config = self.get_business_config()
        reviews = []
        
        # Templates for realistic reviews by rating
        review_templates = {
            5: [
                f"Absolutely love this {product_name}! Exceeded my expectations in every way.",
                f"Outstanding quality! This {product_name} is exactly what I was looking for.",
                f"Perfect {product_name}! Fast shipping, great packaging, couldn't be happier.",
                f"Five stars! This {product_name} works flawlessly. Highly recommend!",
                f"Incredible {product_name}! Worth every penny. Will definitely buy again."
            ],
            4: [
                f"Great {product_name} overall. Just a few minor issues but mostly satisfied.",
                f"Very good quality {product_name}. Works as expected, good value for money.",
                f"Happy with this {product_name}. Solid build quality, does what it says.",
                f"Good {product_name}. Minor room for improvement but generally pleased.",
                f"Satisfied with this {product_name}. Good features, reasonable price."
            ],
            3: [
                f"Okay {product_name}. Does the job but nothing special.",
                f"Average {product_name}. Met basic expectations but could be better.",
                f"Decent {product_name} for the price. Some pros and cons.",
                f"Fair {product_name}. Works fine but has some limitations.",
                f"Middle of the road {product_name}. Neither great nor terrible."
            ],
            2: [
                f"Disappointed with this {product_name}. Several issues right out of the box.",
                f"Below expectations. This {product_name} has multiple problems.",
                f"Not great. The {product_name} doesn't work as advertised.",
                f"Poor quality {product_name}. Wouldn't recommend to others.",
                f"Had high hopes but this {product_name} fell short."
            ],
            1: [
                f"Terrible {product_name}! Complete waste of money. Returning immediately.",
                f"Awful quality. This {product_name} broke after just one use.",
                f"Don't buy this {product_name}! Multiple defects and poor design.",
                f"Worst {product_name} I've ever purchased. Save your money.",
                f"One star is too generous. This {product_name} is completely useless."
            ]
        }
        
        # Generate 5-15 reviews per product
        num_reviews = random.randint(5, 15)
        
        for _ in range(num_reviews):
            # Weight ratings toward positive (realistic for most products)
            rating = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.08, 0.15, 0.35, 0.37])[0]
            
            # Select and customize review template
            base_review = random.choice(review_templates[rating])
            
            # Add specific details based on category
            details = self.get_category_specific_details(category, rating)
            review_text = f"{base_review} {details}"
            
            reviews.append({
                'product_id': product_id,
                'rating': rating,
                'review_text': review_text,
                'review_date': self.fake.date_between(start_date='-1y', end_date='today'),
                'sentiment': 'positive' if rating >= 4 else 'negative' if rating <= 2 else 'neutral',
                'helpful_votes': random.randint(0, 50) if rating >= 4 else random.randint(0, 20),
                'verified_purchase': random.choice([True, True, True, False])  # 75% verified
            })
        
        return reviews
    
    def get_category_specific_details(self, category: str, rating: int) -> str:
        """Generate category-specific review details"""
        details_by_category = {
            'Electronics': {
                'positive': ["Battery life is excellent.", "Setup was incredibly easy.", "Great build quality and design."],
                'negative': ["Battery drains too quickly.", "Difficult to set up.", "Feels cheap and flimsy."],
                'neutral': ["Battery life is okay.", "Setup was straightforward.", "Build quality is decent."]
            },
            'Clothing': {
                'positive': ["Perfect fit and comfortable fabric.", "Color is exactly as shown.", "Great quality stitching."],
                'negative': ["Runs small, had to return.", "Color faded after one wash.", "Poor stitching quality."],
                'neutral': ["Fit is okay, fabric is decent.", "Color is close to photo.", "Stitching is acceptable."]
            },
            'Home & Garden': {
                'positive': ["Easy to assemble and very sturdy.", "Looks great in my space.", "Excellent value for money."],
                'negative': ["Assembly was nightmare.", "Doesn't match the photos.", "Overpriced for the quality."],
                'neutral': ["Assembly took some time.", "Looks decent in person.", "Fair price for what you get."]
            }
        }
        
        sentiment = 'positive' if rating >= 4 else 'negative' if rating <= 2 else 'neutral'
        category_details = details_by_category.get(category, details_by_category['Electronics'])
        
        return random.choice(category_details.get(sentiment, ["No additional details."]))
    
    def generate_comprehensive_products(self) -> List[Dict]:
        """Generate realistic, detailed product catalog"""
        config = self.get_business_config()
        products = []
        
        # Business-specific product generators
        if self.business_type in ['retail', 'ecommerce']:
            products = self.generate_retail_products(config)
        elif self.business_type == 'healthcare':
            products = self.generate_healthcare_services(config)
        elif self.business_type == 'finance':
            products = self.generate_financial_products(config)
        elif self.business_type == 'education':
            products = self.generate_educational_courses(config)
        elif self.business_type == 'manufacturing':
            products = self.generate_manufacturing_products(config)
        
        return products
    
    def generate_retail_products(self, config: Dict) -> List[Dict]:
        """Generate comprehensive retail product catalog based on company description"""
        products = []
        
        # Check if company description contains specific business keywords
        description_lower = self.company_description.lower()
        
        # Generate context-aware products based on company description
        if any(keyword in description_lower for keyword in ['jellybean', 'candy', 'sweet', 'confection', 'chocolate', 'gum']):
            products = self.generate_candy_products()
        elif any(keyword in description_lower for keyword in ['fish', 'aquarium', 'pet', 'coral', 'marine']):
            products = self.generate_aquarium_products()
        elif any(keyword in description_lower for keyword in ['home improvement', 'hardware', 'tools', 'depot', 'building']):
            products = self.generate_home_improvement_products()
        elif any(keyword in description_lower for keyword in ['sock', 'clothing', 'apparel', 'fashion']):
            products = self.generate_clothing_products()
        else:
            # Fall back to generic retail products
            products = self.generate_generic_retail_products(config)
        
        return products
    
    def generate_candy_products(self) -> List[Dict]:
        """Generate candy and confectionery products"""
        candy_products = [
            ('Classic Jellybeans Assorted', 'Traditional mixed flavor jellybeans in vibrant colors', 'Candy', 2.99),
            ('Gourmet Jellybeans Premium', 'Premium gourmet jellybeans with unique flavor combinations', 'Premium Candy', 7.99),
            ('Sour Jellybeans Extreme', 'Extra sour jellybeans for the ultimate sour candy experience', 'Sour Candy', 3.49),
            ('Chocolate Covered Jellybeans', 'Jellybeans covered in smooth milk chocolate', 'Chocolate Candy', 5.99),
            ('Organic Jellybeans Natural', 'Organic jellybeans made with natural flavors and colors', 'Organic Candy', 8.99),
            ('Giant Jellybeans Jumbo', 'Extra large jellybeans with intense fruit flavors', 'Novelty Candy', 4.99),
            ('Sugar-Free Jellybeans', 'Delicious jellybeans sweetened with natural sugar alternatives', 'Diet Candy', 6.49),
            ('Tropical Jellybeans Mix', 'Exotic tropical fruit flavored jellybeans', 'Tropical Candy', 3.99),
            ('Gummy Bears Classic', 'Traditional chewy gummy bears in assorted fruit flavors', 'Gummy Candy', 2.49),
            ('Chocolate Bars Milk', 'Creamy milk chocolate bars with smooth texture', 'Chocolate', 1.99),
            ('Hard Candy Lollipops', 'Colorful hard candy lollipops in various fruit flavors', 'Hard Candy', 1.49),
            ('Peppermint Candy Canes', 'Traditional red and white striped peppermint candy canes', 'Holiday Candy', 2.99),
            ('Caramel Chews Soft', 'Soft and chewy caramel candies with rich butter flavor', 'Caramel', 3.49),
            ('Rock Candy Crystals', 'Natural rock candy crystals on wooden sticks', 'Novelty Candy', 2.99),
            ('Licorice Twists Black', 'Classic black licorice twists with authentic flavor', 'Licorice', 2.49),
            ('Fruit Snacks Gummy', 'Chewy fruit snacks made with real fruit juice', 'Fruit Candy', 2.99),
            ('Chocolate Truffles Assorted', 'Handcrafted chocolate truffles with various fillings', 'Premium Chocolate', 12.99),
            ('Mint Chocolates', 'Cool mint chocolates with dark chocolate coating', 'Mint Candy', 4.99),
            ('Toffee Pieces Butter', 'Rich butter toffee pieces covered in chocolate', 'Toffee', 5.99),
            ('Marshmallows Jumbo', 'Large fluffy marshmallows perfect for roasting', 'Marshmallow', 3.99)
        ]
        
        products = []
        for name, description, category, price in candy_products:
            products.append({
                'name': name,
                'sku': f'CANDY{self.fake.random_int(1000, 9999)}',
                'category': category,
                'price': price,
                'description': description,
                'stock_quantity': self.fake.random_int(50, 500),
                'weight': round(self.fake.random.uniform(0.1, 2.0), 2),
                'dimensions': f'{self.fake.random_int(2, 8)}"x{self.fake.random_int(2, 8)}"x{self.fake.random_int(1, 4)}"',
                'manufacturer': self.fake.random.choice(['Sweet Treats Co.', 'Candy World Inc.', 'Sugar Rush Confections', 'Jellybeans Plus']),
                'warranty_months': 0,  # Food products don't have warranties
                'launch_date': self.fake.date_between(start_date='-2y', end_date='today'),
                'status': self.fake.random.choice(['Active', 'Active', 'Active', 'Discontinued'])
            })
        
        return products
    
    def generate_generic_retail_products(self, config: Dict) -> List[Dict]:
        """Generate generic retail products when no specific context is found"""
        products = []
        
        # Define realistic products by category
        product_templates = {
            'Electronics': [
                ('Wireless Noise-Canceling Headphones', 'Premium audio experience with active noise cancellation and 30-hour battery life'),
                ('4K Smart TV 55-inch', 'Ultra-high definition smart television with built-in streaming apps'),
                ('Gaming Laptop RTX 4060', 'High-performance gaming laptop with latest graphics card'),
                ('Smartphone Pro Max', 'Latest flagship smartphone with professional camera system'),
                ('Wireless Charging Pad', 'Fast wireless charging for all Qi-enabled devices'),
                ('Bluetooth Speakers Waterproof', 'Portable speakers with premium sound quality and water resistance'),
                ('Smart Watch Fitness Tracker', 'Advanced fitness tracking with heart rate and GPS monitoring'),
                ('USB-C Hub Multi-Port', 'Versatile connectivity hub with multiple ports and fast data transfer')
            ],
            'Clothing': [
                ('Premium Cotton T-Shirt', 'Soft, breathable cotton t-shirt perfect for everyday wear'),
                ('Designer Jeans Slim Fit', 'High-quality denim with comfortable stretch and modern cut'),
                ('Wool Blend Sweater', 'Cozy sweater made from premium wool blend for cold weather'),
                ('Running Shoes Athletic', 'Lightweight running shoes with advanced cushioning technology'),
                ('Leather Jacket Genuine', 'Classic leather jacket crafted from genuine cowhide'),
                ('Formal Dress Shirt', 'Crisp cotton dress shirt perfect for business and formal occasions'),
                ('Yoga Pants Stretch', 'Comfortable stretch pants ideal for yoga and fitness activities'),
                ('Winter Coat Insulated', 'Warm winter coat with premium insulation and weather protection')
            ],
            'Home & Garden': [
                ('Coffee Maker Programmable', 'Automatic coffee maker with programmable timer and multiple brew sizes'),
                ('Indoor Plant Monstera', 'Beautiful monstera deliciosa plant perfect for home decoration'),
                ('LED Desk Lamp Adjustable', 'Modern desk lamp with adjustable brightness and USB charging port'),
                ('Vacuum Cleaner Cordless', 'Powerful cordless vacuum with long battery life and multiple attachments'),
                ('Kitchen Knife Set Professional', 'Professional-grade knife set with ergonomic handles and storage block'),
                ('Throw Pillows Decorative Set', 'Set of decorative pillows to enhance your living space comfort'),
                ('Garden Hose Heavy Duty', 'Durable garden hose with brass fittings and kink-resistant design'),
                ('Air Purifier HEPA Filter', 'Advanced air purifier with HEPA filtration for clean indoor air')
            ]
        }
        
        for category in config['categories']:
            if category in product_templates:
                templates = product_templates[category]
                for name, description in templates:
                    # Set realistic price ranges by category
                    price_ranges = {
                        'Electronics': (29.99, 1299.99),
                        'Clothing': (19.99, 199.99),
                        'Home & Garden': (14.99, 299.99),
                        'Sports': (24.99, 399.99),
                        'Beauty': (9.99, 149.99),
                        'Books': (12.99, 59.99),
                        'Automotive': (19.99, 799.99),
                        'Toys': (9.99, 199.99)
                    }
                    
                    price_range = price_ranges.get(category, (19.99, 299.99))
                    price = round(random.uniform(price_range[0], price_range[1]), 2)
                    
                    products.append({
                        'name': name,
                        'category': category,
                        'price': price,
                        'description': description,
                        'sku': f"{category[:3].upper()}-{random.randint(1000, 9999)}",
                        'stock_quantity': random.randint(5, 200),
                        'launch_date': self.fake.date_between(start_date='-2y', end_date='today'),
                        'status': random.choices(['active', 'discontinued'], weights=[0.9, 0.1])[0],
                        'weight': round(random.uniform(0.1, 25.0), 2),
                        'dimensions': f"{random.randint(5, 50)}x{random.randint(5, 50)}x{random.randint(2, 30)} cm",
                        'manufacturer': self.fake.company(),
                        'warranty_months': random.choice([12, 24, 36, 60])
                    })
        
        return products[:config['product_count']]

    def generate_financial_products(self, config: Dict) -> List[Dict]:
        """Generate financial products and services"""
        products = []
        
        # Define financial products by category
        product_templates = {
            'Checking': [
                ('Basic Checking Account', 'No-fee checking account with online banking and mobile app access'),
                ('Premium Checking Account', 'High-yield checking with additional benefits and no minimum balance'),
                ('Student Checking Account', 'Specially designed checking account for students with no monthly fees'),
                ('Business Checking Account', 'Professional checking account for small businesses with merchant services'),
                ('Senior Checking Account', 'Checking account with special benefits for customers 55 and older')
            ],
            'Savings': [
                ('High-Yield Savings Account', 'Competitive interest rates with easy online access to your money'),
                ('Money Market Account', 'Higher interest savings with limited check-writing privileges'),
                ('Certificate of Deposit 12-Month', 'Fixed-rate CD with guaranteed returns over 12 months'),
                ('Certificate of Deposit 24-Month', 'Higher yield CD with 24-month commitment for better returns'),
                ('IRA Savings Account', 'Individual Retirement Account with tax advantages for retirement planning')
            ],
            'Loans': [
                ('Personal Loan Fixed Rate', 'Unsecured personal loan with competitive fixed rates'),
                ('Auto Loan New Vehicle', 'Financing for new vehicle purchases with attractive rates'),
                ('Auto Loan Used Vehicle', 'Competitive rates for pre-owned vehicle financing'),
                ('Home Mortgage Fixed 30-Year', 'Traditional 30-year fixed-rate mortgage for home purchases'),
                ('Home Equity Line of Credit', 'Flexible credit line secured by your home equity'),
                ('Student Loan Private', 'Educational financing to help cover college expenses')
            ],
            'Credit Cards': [
                ('Cashback Rewards Credit Card', 'Earn cash back on every purchase with no annual fee'),
                ('Travel Rewards Credit Card', 'Earn points on travel purchases with premium travel benefits'),
                ('Business Credit Card', 'Designed for business expenses with expense tracking tools'),
                ('Secured Credit Card', 'Build or rebuild credit with a secured credit card'),
                ('Low Interest Credit Card', 'Competitive APR for everyday purchases and balance transfers')
            ],
            'Investments': [
                ('Individual Brokerage Account', 'Self-directed investment account with commission-free stock trades'),
                ('Roth IRA Investment Account', 'Tax-free growth potential for retirement savings'),
                ('Traditional IRA Investment', 'Tax-deferred growth for retirement planning'),
                ('529 Education Savings Plan', 'Tax-advantaged savings plan for education expenses'),
                ('Mutual Fund Portfolio', 'Diversified investment portfolios managed by professionals')
            ],
            'Insurance': [
                ('Term Life Insurance', 'Affordable life insurance protection for a specific period'),
                ('Whole Life Insurance', 'Permanent life insurance with cash value accumulation'),
                ('Auto Insurance Full Coverage', 'Comprehensive auto insurance with collision and liability'),
                ('Homeowners Insurance', 'Protect your home and belongings with comprehensive coverage'),
                ('Disability Income Insurance', 'Replace lost income if you become unable to work')
            ]
        }
        
        for category in config['categories']:
            if category in product_templates:
                templates = product_templates[category]
                for name, description in templates:
                    # Set realistic rates and minimums by product type
                    product_specs = self.get_financial_product_specs(category, name)
                    
                    products.append({
                        'name': name,
                        'product_type': category.lower(),
                        'category': category,
                        'description': description,
                        'minimum_amount': product_specs['minimum_amount'],
                        'interest_rate': product_specs['interest_rate'],
                        'term_months': product_specs['term_months'],
                        'risk_level': product_specs['risk_level'],
                        'fees': product_specs['fees'],
                        'status': 'active'
                    })
        
        return products[:config['product_count']]
    
    def get_financial_product_specs(self, category: str, name: str) -> Dict:
        """Get realistic specifications for financial products"""
        specs = {
            'minimum_amount': 0.00,
            'interest_rate': 0.0000,
            'term_months': None,
            'risk_level': 'low',
            'fees': 0.00
        }
        
        if category == 'Checking':
            specs.update({
                'minimum_amount': random.choice([0.00, 25.00, 100.00, 500.00]),
                'interest_rate': round(random.uniform(0.0001, 0.0150), 4),
                'fees': random.choice([0.00, 5.00, 10.00, 15.00])
            })
        elif category == 'Savings':
            specs.update({
                'minimum_amount': random.choice([1.00, 25.00, 100.00, 1000.00]),
                'interest_rate': round(random.uniform(0.0050, 0.0450), 4),
                'risk_level': 'low'
            })
            if 'CD' in name or 'Certificate' in name:
                specs.update({
                    'term_months': random.choice([6, 12, 18, 24, 36, 60]),
                    'minimum_amount': random.choice([500.00, 1000.00, 2500.00, 5000.00])
                })
        elif category == 'Loans':
            specs.update({
                'minimum_amount': random.choice([1000.00, 5000.00, 10000.00, 25000.00]),
                'interest_rate': round(random.uniform(0.0350, 0.1850), 4),
                'term_months': random.choice([12, 24, 36, 48, 60, 84, 360]),
                'risk_level': 'medium'
            })
        elif category == 'Credit Cards':
            specs.update({
                'interest_rate': round(random.uniform(0.1299, 0.2999), 4),
                'fees': random.choice([0.00, 25.00, 50.00, 95.00]),
                'risk_level': 'medium'
            })
        elif category == 'Investments':
            specs.update({
                'minimum_amount': random.choice([0.00, 100.00, 500.00, 1000.00, 5000.00]),
                'interest_rate': round(random.uniform(0.0200, 0.0800), 4),
                'risk_level': random.choice(['low', 'medium', 'high']),
                'fees': round(random.uniform(0.00, 2.50), 2)
            })
        elif category == 'Insurance':
            specs.update({
                'minimum_amount': random.choice([25.00, 50.00, 100.00, 250.00]),
                'fees': round(random.uniform(15.00, 150.00), 2),
                'risk_level': 'low'
            })
        
        return specs

    # Additional methods for other business types would go here...
    
    def generate_realistic_customers(self, count: int) -> List[Dict]:
        """Generate realistic customer profiles with detailed information"""
        customers = []
        config = self.get_business_config()
        
        for _ in range(count):
            # Generate realistic customer profile
            gender = random.choice(['male', 'female'])
            first_name = self.fake.first_name_male() if gender == 'male' else self.fake.first_name_female()
            last_name = self.fake.last_name()
            
            # Age-based segments for realistic behavior
            age = random.randint(18, 75)
            segment = self.determine_customer_segment(age, config['customer_segments'])
            
            customers.append({
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f"{first_name} {last_name}",
                'email': f"{first_name.lower()}.{last_name.lower()}@{self.fake.domain_name()}",
                'phone': self.fake.phone_number(),
                'date_of_birth': self.fake.date_of_birth(minimum_age=age-2, maximum_age=age+2),
                'registration_date': self.fake.date_between(start_date='-3y', end_date='today'),
                'segment': segment,
                'lifetime_value': self.calculate_realistic_ltv(segment),
                'address': self.fake.street_address(),
                'city': random.choice(config['locations']),
                'postal_code': self.fake.postcode(),
                'country': 'United States',
                'preferred_contact': random.choice(['email', 'phone', 'sms']),
                'marketing_opt_in': random.choice([True, False]),
                'last_login': self.fake.date_between(start_date='-30d', end_date='today'),
                'account_status': random.choices(['active', 'inactive', 'suspended'], weights=[0.85, 0.12, 0.03])[0]
            })
        
        return customers
    
    def determine_customer_segment(self, age: int, segments: List[str]) -> str:
        """Determine customer segment based on age and business type"""
        if 'VIP' in segments:
            # Age-based segmentation for retail/ecommerce
            if age >= 45:
                return random.choices(segments, weights=[0.4, 0.3, 0.2, 0.1])[0]  # More premium
            elif age >= 30:
                return random.choices(segments, weights=[0.2, 0.4, 0.3, 0.1])[0]  # Balanced
            else:
                return random.choices(segments, weights=[0.1, 0.2, 0.4, 0.3])[0]  # More budget
        else:
            return random.choice(segments)
    
    def calculate_realistic_ltv(self, segment: str) -> float:
        """Calculate realistic lifetime value based on customer segment"""
        ltv_ranges = {
            'VIP': (2000, 10000),
            'Premium': (800, 3000),
            'Standard': (200, 1200),
            'Budget': (50, 500),
            'Basic': (50, 500),
            'Enterprise': (5000, 50000),
            'Private Banking': (10000, 100000)
        }
        
        range_values = ltv_ranges.get(segment, (100, 1000))
        return round(random.uniform(range_values[0], range_values[1]), 2)

# Usage example and export
async def generate_enhanced_business_database(
    business_type: str, 
    company_name: str, 
    company_description: str,
    db_path: str
) -> Dict[str, int]:
    """Generate comprehensive business database with realistic data"""
    
    generator = EnhancedBusinessDataGenerator(business_type, company_name, company_description)
    config = generator.get_business_config()
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Generate comprehensive data
    print(f"Generating enhanced {business_type} database for {company_name}...")
    
    # Generate products/services
    products = generator.generate_comprehensive_products()
    print(f"Generated {len(products)} products/services")
    
    # Generate customers
    customers = generator.generate_realistic_customers(config.get('customer_count', 500))
    print(f"Generated {len(customers)} customers")
    
    # Generate reviews for products
    all_reviews = []
    for i, product in enumerate(products[:50], 1):  # Reviews for first 50 products
        reviews = generator.generate_realistic_reviews(i, product['name'], product['category'])
        all_reviews.extend(reviews)
    
    print(f"Generated {len(all_reviews)} detailed reviews")
    
    # Insert data into database (implementation would continue here...)
    
    stats = {
        'products': len(products),
        'customers': len(customers),
        'reviews': len(all_reviews),
        'orders': 0,  # Would be generated
        'transactions': 0  # Would be generated
    }
    
    conn.close()
    return stats

if __name__ == "__main__":
    # Test the enhanced generator
    asyncio.run(generate_enhanced_business_database(
        "retail", 
        "Demo Retail Store", 
        "A comprehensive retail business for demonstration",
        "test_enhanced.db"
    ))