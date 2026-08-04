"""Product search service.

Simple keyword search across product name, descriptions, tags, and category name.
Case-insensitive. Every whitespace-separated term must match at least one field.
"""


def search_products(config: dict, query: str) -> list:
    """Return products in this client's catalogue matching the query string."""
    query = (query or "").strip().lower()
    if not query:
        return []

    terms = query.split()
    category_map = config.get("_category_map", {})
    results = []

    for product in config.get("products", []):
        category = category_map.get(product.get("category_id"), {})
        haystack = " ".join([
            product.get("name", ""),
            product.get("short_description", ""),
            product.get("long_description", ""),
            " ".join(product.get("tags", [])),
            category.get("name", ""),
        ]).lower()

        if all(term in haystack for term in terms):
            results.append(product)

    return results
