"""
Script to initialize business documents in the vector database
"""

import asyncio
import os
from pathlib import Path
import sys
from io import BytesIO
from fastapi import UploadFile

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.document_manager import DocumentManager

# Sample business documents content
SAMPLE_DOCUMENTS = [
    {
        "filename": "luxury_market_analysis_2024.md",
        "category": "market_research",
        "content": """# Luxury Market Analysis 2024

## Executive Summary
The global luxury goods market has shown remarkable resilience and growth in 2024, with particular strength in handbags and accessories.

## Key Findings

### Market Performance
- Global luxury handbag market reached $64.3 billion in 2024
- Year-over-year growth of 8.5% despite economic uncertainties
- Premium segment (+$2,000) showing strongest growth at 12.3%

### Top Performing Product Categories
1. **Designer Handbags**: Leading category with 35% market share
   - Louis Vuitton maintains #1 position with 18% market share
   - Hermès showing strongest growth at 15% YoY
   - Chanel maintaining premium positioning with average price increase of 10%

2. **Leather Accessories**: Second strongest category
   - Wallets and small leather goods growing 11% YoY
   - Belts showing steady 7% growth
   - Phone cases and tech accessories emerging as new growth driver

3. **Seasonal Collections**: High performance indicators
   - Spring/Summer 2024 collections exceeded sales targets by 22%
   - Limited edition releases sold out 40% faster than 2023
   - Collaboration pieces showing 300% higher sell-through rates

### Regional Performance
- **North America**: 28% of total sales, 9% growth
- **Asia-Pacific**: 35% of total sales, 12% growth (led by China recovery)
- **Europe**: 25% of total sales, 6% growth
- **Middle East & Africa**: 12% of total sales, 15% growth

### Consumer Trends
- 67% of purchases now include sustainability considerations
- Online sales represent 23% of total luxury purchases (up from 18% in 2023)
- Personalization services driving 31% higher average transaction values
- Younger demographics (25-35) account for 42% of new customer acquisitions

### Brand Performance Metrics
- Customer retention rates averaging 78% across top luxury brands
- Net Promoter Scores averaging 72 for premium handbag brands
- Social media engagement rates up 25% YoY
- Influencer collaborations driving 18% of brand awareness

## Recommendations
1. Continue investment in premium product lines
2. Expand personalization offerings
3. Strengthen digital presence and e-commerce capabilities
4. Focus on sustainability initiatives to attract younger consumers
5. Develop limited edition and collaboration strategies
"""
    },
    {
        "filename": "financial_performance_q3_2024.md",
        "category": "financial",
        "content": """# Q3 2024 Financial Performance Report

## Revenue Summary
Total revenue for Q3 2024: $45.2 million (23% increase YoY)

### Revenue Breakdown by Category
- **Premium Handbags**: $28.6 million (63% of total revenue)
- **Accessories**: $12.1 million (27% of total revenue)
- **Limited Editions**: $4.5 million (10% of total revenue)

### Top Performing Products
1. **Classic Tote Collection**: $8.2 million revenue
   - Average selling price: $1,850
   - Units sold: 4,432
   - 15% increase from Q2 2024

2. **Executive Briefcase Line**: $6.7 million revenue
   - Average selling price: $2,340
   - Units sold: 2,863
   - 28% increase from Q2 2024

3. **Evening Clutch Series**: $4.1 million revenue
   - Average selling price: $890
   - Units sold: 4,607
   - 31% increase from Q2 2024

4. **Crossbody Collection**: $5.8 million revenue
   - Average selling price: $1,250
   - Units sold: 4,640
   - 19% increase from Q2 2024

5. **Travel Luggage Set**: $3.2 million revenue
   - Average selling price: $3,200
   - Units sold: 1,000
   - 45% increase from Q2 2024

### Profitability Metrics
- Gross margin: 68.5% (industry average: 62%)
- Operating margin: 24.3%
- Net profit margin: 18.7%
- EBITDA: $12.8 million

### Channel Performance
- **Flagship Stores**: $22.6 million (50% of revenue)
- **Online Direct**: $13.6 million (30% of revenue)
- **Authorized Retailers**: $7.2 million (16% of revenue)
- **Wholesale Partners**: $1.8 million (4% of revenue)

### Geographic Performance
- **North America**: $20.3 million (45% of revenue)
- **Europe**: $13.6 million (30% of revenue)
- **Asia Pacific**: $9.0 million (20% of revenue)
- **Other Markets**: $2.3 million (5% of revenue)

### Key Performance Indicators
- Customer acquisition cost: $145 (down 12% from Q2)
- Customer lifetime value: $2,850 (up 18% from Q2)
- Average order value: $1,680 (up 8% from Q2)
- Repeat customer rate: 34% (up 5% from Q2)
- Inventory turnover: 4.2x (optimal range: 4-6x)

## Financial Outlook
Projected Q4 2024 revenue: $52-55 million (holiday season boost expected)
"""
    },
    {
        "filename": "customer_satisfaction_survey_2024.md",
        "category": "customer_research",
        "content": """# Customer Satisfaction Survey Results 2024

## Survey Overview
- **Response Rate**: 2,847 customers (18.3% response rate)
- **Survey Period**: August - September 2024
- **Method**: Email survey + in-store tablet surveys

## Overall Satisfaction Metrics
- **Overall Satisfaction**: 4.3/5.0 (86% satisfaction rate)
- **Net Promoter Score**: 68 (Excellent range)
- **Customer Effort Score**: 4.1/5.0

## Product Satisfaction by Category

### Handbags (4.4/5.0)
**Highest Rated Aspects:**
- Quality of materials (4.6/5.0)
- Craftsmanship (4.5/5.0)
- Design aesthetics (4.4/5.0)
- Durability (4.3/5.0)

**Areas for Improvement:**
- Color variety (3.8/5.0)
- Size options (3.9/5.0)
- Price value perception (3.7/5.0)

### Customer Service (4.2/5.0)
**Strengths:**
- Staff knowledge (4.5/5.0)
- Responsiveness (4.2/5.0)
- Problem resolution (4.1/5.0)

**Improvement Areas:**
- Wait times (3.6/5.0)
- Follow-up service (3.8/5.0)

### Shopping Experience
**In-Store Experience (4.1/5.0):**
- Store ambiance: 4.4/5.0
- Product displays: 4.2/5.0
- Checkout process: 3.9/5.0
- Store layout: 4.0/5.0

**Online Experience (3.9/5.0):**
- Website navigation: 4.1/5.0
- Product images: 4.0/5.0
- Shipping speed: 3.7/5.0
- Return process: 3.8/5.0

## Customer Demographics
- **Age Groups**: 25-35 (34%), 36-45 (28%), 46-55 (22%), 56+ (16%)
- **Income Levels**: $75k-$100k (32%), $100k-$150k (28%), $150k+ (25%), <$75k (15%)
- **Purchase Frequency**: Monthly (15%), Quarterly (35%), Bi-annually (32%), Annually (18%)

## Customer Preferences
**Most Valued Features:**
1. Premium materials (89% of respondents)
2. Timeless design (82% of respondents)
3. Brand reputation (78% of respondents)
4. Craftsmanship quality (85% of respondents)
5. Warranty/after-sales service (72% of respondents)

**Purchase Motivations:**
1. Special occasions (42%)
2. Professional needs (38%)
3. Personal reward (35%)
4. Gift giving (28%)
5. Investment piece (25%)

## Customer Loyalty Metrics
- **Repeat Purchase Rate**: 68% (purchased within last 18 months)
- **Referral Rate**: 45% (recommended to friends/family)
- **Brand Loyalty Score**: 7.2/10
- **Price Sensitivity**: 32% would pay 10-15% premium for quality

## Feedback Themes
**Positive Feedback (Top Mentions):**
- "Exceptional quality materials"
- "Beautiful craftsmanship"
- "Excellent customer service"
- "Timeless designs"
- "Great investment pieces"

**Improvement Suggestions:**
- More color options (mentioned by 34% of respondents)
- Extended size range (mentioned by 28% of respondents)
- Faster shipping options (mentioned by 31% of respondents)
- More frequent sales/promotions (mentioned by 26% of respondents)
- Better online product visualization (mentioned by 22% of respondents)

## Action Items Based on Feedback
1. Expand color palette for core collections
2. Introduce more size variations for popular styles
3. Improve shipping speed and tracking
4. Enhance website product photography and 360° views
5. Develop loyalty program with exclusive benefits
"""
    },
    {
        "filename": "marketing_campaign_analysis_2024.md",
        "category": "marketing",
        "content": """# Marketing Campaign Analysis 2024

## Campaign Performance Overview
Total marketing spend: $3.2 million across all channels (Q1-Q3 2024)
Overall ROI: 4.2x (industry benchmark: 3.1x)

## Channel Performance Analysis

### Digital Marketing ($1.8M - 56% of budget)

**Social Media Advertising ($720k)**
- **Instagram**: $380k spend, 2.1M impressions, 4.8% CTR
  - Best performing content: Product showcases (6.2% CTR)
  - ROI: 5.1x
  - Audience: 78% female, 65% age 25-45
  
- **Facebook**: $240k spend, 1.6M impressions, 3.2% CTR
  - Best performing: Video content and user testimonials
  - ROI: 3.8x
  
- **TikTok**: $100k spend, 890k impressions, 7.1% CTR
  - Exceptional performance with younger demographics (18-30)
  - ROI: 6.3x
  - Top content: Behind-the-scenes craftsmanship videos

**Google Ads ($680k)**
- Search campaigns: $450k, 18% conversion rate
- Shopping campaigns: $230k, 12% conversion rate
- Display remarketing: $150k, 3.2% conversion rate
- Overall ROI: 4.7x

**Email Marketing ($180k)**
- 85,000 active subscribers
- Open rate: 28.5% (industry average: 21.3%)
- Click rate: 4.8% (industry average: 2.6%)
- Revenue per email: $12.40
- ROI: 8.2x (highest performing channel)

**Influencer Partnerships ($220k)**
- 12 macro-influencers (100k-1M followers)
- 25 micro-influencers (10k-100k followers)
- Average engagement rate: 6.8%
- ROI: 3.9x
- Best performing: Lifestyle and fashion influencers

### Traditional Marketing ($900k - 28% of budget)

**Print Advertising ($400k)**
- Fashion magazines: Vogue, Harper's Bazaar, Elle
- Brand awareness lift: 23%
- ROI: 2.1x (brand building focus)

**PR & Events ($300k)**
- Fashion week presence: $180k
- VIP customer events: $120k
- Media coverage value: $680k earned media
- ROI: 2.8x

**Outdoor Advertising ($200k)**
- Premium location billboards
- Transit advertising in luxury areas
- Brand awareness lift: 18%
- ROI: 1.9x

### Retail Marketing ($500k - 16% of budget)

**In-Store Displays & Visual Merchandising ($300k)**
- Window displays refresh quarterly
- In-store experience enhancements
- Conversion rate improvement: 15%

**Point-of-Sale Materials ($120k)**
- Brochures, catalogs, digital displays
- Upselling success rate: 22%

**Customer Experience Programs ($80k)**
- Personal shopping services
- VIP customer events
- Customer retention improvement: 12%

## Campaign-Specific Results

### Spring/Summer 2024 Launch
- **Budget**: $850k (March-May)
- **Channels**: Social media (60%), Google Ads (25%), Influencers (15%)
- **Results**: 
  - 45% increase in brand awareness
  - 28% increase in website traffic
  - $4.1M revenue attributed to campaign
  - ROI: 4.8x

### Holiday Preview Campaign
- **Budget**: $620k (October-November)
- **Channels**: Email (40%), Social media (35%), PR (25%)
- **Results**:
  - 67% increase in email subscribers
  - 52% increase in pre-orders
  - $3.8M revenue attributed to campaign
  - ROI: 6.1x

### Limited Edition Collection Launch
- **Budget**: $340k (August)
- **Channels**: Influencers (50%), Social media (30%), Email (20%)
- **Results**:
  - Sold out in 72 hours
  - 156% increase in social media followers
  - $2.1M revenue (entire collection)
  - ROI: 6.2x

## Customer Acquisition Analysis
- **Cost per acquisition**: $145 (down from $167 in 2023)
- **Customer lifetime value**: $2,850 (up from $2,340 in 2023)
- **Payback period**: 3.2 months (improved from 4.1 months)

## Key Insights & Recommendations

### High-Performing Strategies
1. Video content significantly outperforms static images (2.3x engagement)
2. User-generated content drives highest trust and conversion
3. Email marketing delivers highest ROI across all channels
4. Micro-influencers often outperform macro-influencers on engagement
5. Behind-the-scenes content builds strong brand connection

### Optimization Opportunities
1. Increase TikTok budget allocation (highest ROI potential)
2. Develop more video content across all platforms
3. Expand user-generated content campaigns
4. Improve Google Shopping campaign optimization
5. Test connected TV advertising for brand awareness

### 2025 Strategy Recommendations
1. Shift 20% of traditional advertising budget to digital
2. Invest in content creation capabilities (video studio)
3. Develop comprehensive influencer relationship program
4. Implement advanced marketing automation
5. Expand into emerging social platforms (YouTube Shorts, Pinterest Video)
"""
    }
]

async def create_sample_documents():
    """
    Create sample documents as text files and upload them through the document manager
    """
    print("Creating sample business documents...")
    
    # Initialize document manager
    doc_manager = DocumentManager()
    
    documents_created = 0
    
    for doc_data in SAMPLE_DOCUMENTS:
        try:
            print(f"Creating: {doc_data['filename']}")
            
            # Create a temporary UploadFile-like object
            content_bytes = doc_data['content'].encode('utf-8')
            
            # Create a mock UploadFile object
            class MockUploadFile:
                def __init__(self, filename: str, content: bytes):
                    self.filename = filename
                    self.content = BytesIO(content)
                
                async def read(self):
                    return self.content.read()
            
            mock_file = MockUploadFile(doc_data['filename'], content_bytes)
            
            # Upload through document manager
            result = await doc_manager.upload_document(
                file=mock_file,
                category=doc_data['category']
            )
            
            print(f"✅ Successfully created: {doc_data['filename']}")
            print(f"   Document ID: {result['id']}")
            print(f"   Content length: {result['content_length']} characters")
            print(f"   Category: {result['category']}")
            print()
            
            documents_created += 1
            
        except Exception as e:
            print(f"❌ Error creating {doc_data['filename']}: {str(e)}")
    
    print(f"Successfully created {documents_created} sample documents!")
    return documents_created

async def main():
    """
    Main function to load sample documents
    """
    try:
        await create_sample_documents()
        print("\n🎉 Sample documents loaded successfully!")
        print("You can now test the system with questions about:")
        print("- Luxury market trends and performance")
        print("- Financial metrics and revenue data")
        print("- Customer satisfaction and feedback")
        print("- Marketing campaign results and ROI")
        
    except Exception as e:
        print(f"❌ Error loading sample documents: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)