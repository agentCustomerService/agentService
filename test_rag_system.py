#!/usr/bin/env python3
"""
Utility script to create sample policy documents and test RAG system
"""

from pathlib import Path
from rag_policies import load_policies_from_pdf, list_loaded_policies, search_policies
import json


def create_sample_policies_text():
    """Create sample policy documents."""
    
    # Sample Cancellation Policy
    cancellation_policy = """
    CANCELLATION POLICY
    
    Our Cancellation Policy outlines the terms and conditions under which customers may cancel their orders.
    
    1. CANCELLATION ELIGIBILITY
    Orders may be cancelled within 24 hours of purchase for a full refund. After 24 hours, cancellation 
    is subject to availability and may incur a cancellation fee.
    
    2. CANCELLATION PROCESS
    To cancel an order, customers must:
    - Contact our customer service team
    - Provide their order number
    - State the reason for cancellation
    
    3. ORDER STATUS IMPACT
    - Orders in "Processing" status: 100% cancellation allowed
    - Orders in "Shipped" status: Subject to return shipping policies
    - Orders in "Delivered" status: Please refer to return policy instead
    
    4. CANCELLATION FEES
    - Cancellations within 24 hours: No fee
    - Cancellations after 24 hours but before shipping: $5-10 processing fee
    - Cancellations after shipping: See return policy for options
    
    5. CANCELLATION CONFIRMATION
    Once cancelled, customers will receive a confirmation email within 24 hours with details of any refund.
    """
    
    # Sample Refund Policy
    refund_policy = """
    REFUND POLICY
    
    We are committed to ensuring customer satisfaction. Our refund policy covers all aspects of returning 
    purchases and receiving refunds.
    
    1. REFUND ELIGIBILITY
    You may request a refund for:
    - Defective or damaged items
    - Items not as described
    - Orders cancelled within 24 hours
    - Returns within 30 days of receipt
    
    2. REFUND TIMELINE
    - Refund processing: 5-10 business days after return approval
    - Credit to original payment method: 1-3 business days after processing
    - Note: Some payment methods may take longer to reflect refunds
    
    3. REFUND AMOUNTS
    - Full refunds: Items returned in original condition
    - Partial refunds: Discounted items, used items (25-50% deduction)
    - Restocking fee: 10% for non-defective returns
    - Original shipping: Non-refundable (return shipping paid by customer)
    
    4. DEFECTIVE OR DAMAGED ITEMS
    - Full refund including return shipping
    - No restocking fee applies
    - Customer must provide photographic evidence
    
    5. RETURN SHIPPING
    - Customers are responsible for return shipping costs
    - We provide a prepaid shipping label for defective items
    - Insurance is recommended for high-value items
    
    6. NON-RETURNABLE ITEMS
    The following items cannot be returned or refunded:
    - Clearance or sale items (final sale)
    - Custom or personalized items
    - Items without original packaging
    - Digital products or downloads
    - Food and beverage products
    
    7. REFUND EXCEPTIONS
    We reserve the right to deny refunds for:
    - Items showing signs of heavy use
    - Missing original tags or accessories
    - Items outside the 30-day return window
    - Purchases made more than 60 days ago
    
    8. CONTACT FOR REFUNDS
    Please contact refunds@company.com with your order number and reason for return.
    """
    
    # Save as text files (can be converted to PDF separately)
    policies_dir = Path(__file__).parent / "policies"
    policies_dir.mkdir(exist_ok=True)
    
    with open(policies_dir / "cancellation_policy.txt", "w") as f:
        f.write(cancellation_policy)
    
    with open(policies_dir / "refund_policy.txt", "w") as f:
        f.write(refund_policy)
    
    return {
        "cancellation": str(policies_dir / "cancellation_policy.txt"),
        "refund": str(policies_dir / "refund_policy.txt")
    }


def test_rag_system():
    """Test the RAG system with sample policies."""
    
    print("=" * 60)
    print("Testing RAG Policy System")
    print("=" * 60)
    
    # Create sample policies
    print("\n1. Creating sample policies...")
    policies_files = create_sample_policies_text()
    print(f"✓ Created policies at: {policies_files}")
    
    # List loaded policies
    print("\n2. Listing loaded policies...")
    policies = list_loaded_policies()
    print(f"Loaded policies: {len(policies)}")
    for policy in policies:
        print(f"  - {policy['name']}: {policy['chunks_count']} chunks")
    
    # Test search
    print("\n3. Testing policy search...")
    test_queries = [
        "Can I cancel my order?",
        "What's the refund process?",
        "How long do I have to return?",
        "Are there any cancellation fees?"
    ]
    
    for query in test_queries:
        print(f"\n  Query: {query}")
        results = search_policies(query, k=2)
        if results:
            for result in results:
                print(f"    - {result['content'][:100]}...")
        else:
            print("    - No results")
    
    print("\n" + "=" * 60)
    print("RAG System Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_rag_system()
