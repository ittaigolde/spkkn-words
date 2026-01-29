"""
Google Merchant Center Product Feed API.
Generates product feed for all words in the registry.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timezone

from ..database import get_db
from ..models import Word
from ..utils import is_word_available

router = APIRouter(prefix="/api/product-feed", tags=["product-feed"])


@router.get("/google-merchant")
async def get_google_merchant_feed(
    db: Session = Depends(get_db),
    limit: int = Query(None, description="Limit number of products (for testing)")
):
    """
    Generate Google Merchant Center product feed in JSON format.

    Returns product data for all words in the registry.
    Format follows Google Merchant Center Content API specification.
    """
    # Query all words (or limited set for testing)
    query = db.query(Word)
    if limit:
        query = query.limit(limit)

    words = query.all()

    # Generate product entries
    products = []
    for word in words:
        # Determine availability
        available = is_word_available(word.lockout_ends_at)
        availability = "in_stock" if available else "out_of_stock"

        # Create product entry
        product = {
            "id": str(word.id),  # Unique product ID
            "title": f"Word: {word.text.upper()}",  # Product title
            "description": f"Own the word '{word.text.upper()}' in The Word Registry. Claim ownership, attach your message, and be part of an interactive word ownership game.",
            "link": f"https://spkkn.com/word/{word.text}",  # Product page URL
            "image_link": f"https://spkkn.com/api/product-feed/word-image/{word.text}",  # Image URL (we'll create this endpoint)
            "price": f"{float(word.price):.2f} USD",  # Price with currency
            "availability": availability,  # in_stock or out_of_stock
            "condition": "new",  # Always new for digital products
            "brand": "The Word Registry",  # Brand name
            "google_product_category": "Software > Computer Software > Educational Software",  # Best fit category
            "product_type": "Digital Goods > Word Ownership",  # Custom category
            "identifier_exists": "false",  # No GTIN/MPN for digital unique items
            # Additional useful fields
            "item_group_id": "words",  # Group all words together
            "custom_label_0": "available" if available else "locked",  # Custom filter
            "custom_label_1": f"price_tier_{int(float(word.price))}",  # Price tier for filtering
        }

        # Add owner info if owned
        if word.owner_name:
            product["custom_label_2"] = "owned"
            product["description"] += f" Currently owned by {word.owner_name}."
        else:
            product["custom_label_2"] = "unclaimed"
            product["description"] += " Currently unclaimed - be the first owner!"

        products.append(product)

    return {
        "kind": "content#productsCustomBatchResponse",
        "products": products,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_products": len(products)
    }


@router.get("/google-merchant/rss")
async def get_google_merchant_feed_rss(
    db: Session = Depends(get_db),
    limit: int = Query(None, description="Limit number of products (for testing)")
):
    """
    Generate Google Merchant Center product feed in RSS/XML format.

    Alternative format for merchants who prefer XML.
    """
    # Query all words
    query = db.query(Word)
    if limit:
        query = query.limit(limit)

    words = query.all()

    # Build RSS XML feed
    items = []
    for word in words:
        available = is_word_available(word.lockout_ends_at)
        availability = "in stock" if available else "out of stock"

        item = f"""
    <item>
      <g:id>{word.id}</g:id>
      <g:title>Word: {word.text.upper()}</g:title>
      <g:description>Own the word '{word.text.upper()}' in The Word Registry. Claim ownership, attach your message, and be part of an interactive word ownership game.</g:description>
      <g:link>https://spkkn.com/word/{word.text}</g:link>
      <g:image_link>https://spkkn.com/api/product-feed/word-image/{word.text}</g:image_link>
      <g:price>{float(word.price):.2f} USD</g:price>
      <g:availability>{availability}</g:availability>
      <g:condition>new</g:condition>
      <g:brand>The Word Registry</g:brand>
      <g:google_product_category>Software > Computer Software > Educational Software</g:google_product_category>
      <g:product_type>Digital Goods > Word Ownership</g:product_type>
    </item>"""
        items.append(item)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
  <channel>
    <title>The Word Registry Product Feed</title>
    <link>https://spkkn.com</link>
    <description>Word ownership products from The Word Registry</description>
    {''.join(items)}
  </channel>
</rss>"""

    return xml


@router.get("/word-image/{word_text}")
async def get_word_image(word_text: str):
    """
    Generate a product image for a word.

    For now, returns a redirect to a placeholder.
    TODO: Generate actual word card images dynamically.
    """
    # For now, redirect to a generic placeholder
    # Later we can generate custom images with the word text
    from fastapi.responses import RedirectResponse

    # Using a generic placeholder for now
    # TODO: Generate custom image with word text overlaid
    placeholder_url = "https://via.placeholder.com/800x600/4F46E5/FFFFFF?text=" + word_text.upper()

    return RedirectResponse(url=placeholder_url)
