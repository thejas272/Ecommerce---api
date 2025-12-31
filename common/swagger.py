from drf_yasg import openapi



# -- Product -- Brand -- Category    Params 

CATEGORY_PARAM = openapi.Parameter(
    name="category",
    in_=openapi.IN_QUERY,
    description="Filter by category slug",
    type=openapi.TYPE_STRING,
)

BRAND_PARAM = openapi.Parameter(
    name="brand",
    in_=openapi.IN_QUERY,
    description="Filter by brand slug",
    type=openapi.TYPE_STRING,
)

SEARCH_PARAM = openapi.Parameter(
    name="search",
    in_=openapi.IN_QUERY,
    description="Search by name, description, brand, or category",
    type=openapi.TYPE_STRING,
)

IS_ACTIVE_PARAM = openapi.Parameter(
    name="is_active",
    in_=openapi.IN_QUERY,
    description=(
        "Filter products/brands/categories by Active.\n\n"
        "- `true` → Active products/brands/categories\n"
        "- `false` → InActive products/brands/categories "
    ),
    type=openapi.TYPE_STRING,
    enum=["true", "false"],
    required=False,
)



# Category only Param

PARENT_PARAM = openapi.Parameter(
    name="parent",
    in_=openapi.IN_QUERY,
    description=(
        "Filter categories by parent.\n\n"
        "- Use `null` to fetch root categories\n"
        "- Use a category slug to fetch its children"
    ),
    type=openapi.TYPE_STRING,
    required=False,
)






# Product Only Params

MIN_PRICE_PARAM = openapi.Parameter(
    name="min_price",
    in_=openapi.IN_QUERY,
    description="Minimum price",
    type=openapi.TYPE_NUMBER,
)


MAX_PRICE_PARAM = openapi.Parameter(
    name="max_price",
    in_=openapi.IN_QUERY,
    description="Maximum price",
    type=openapi.TYPE_NUMBER,
)

SORT_PARAM = openapi.Parameter(
    name="sort",
    in_=openapi.IN_QUERY,
    description="Sort products",
    type=openapi.TYPE_STRING,
    enum=["price_asc", "price_desc", "newest", "oldest"],
    required=False,
)

IN_STOCK_PARAM = openapi.Parameter(
    name="in_stock",
    in_=openapi.IN_QUERY,
    description=(
        "Filter products by stock availability.\n\n"
        "- `true` → products with stock > 0\n"
        "- `false` → products with stock = 0"
    ),
    type=openapi.TYPE_STRING,
    enum=["true", "false"],
    required=False,
)


