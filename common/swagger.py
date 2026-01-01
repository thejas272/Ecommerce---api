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
    description=(
        "Search across relevant text fields for this endpoint.\n\n"
        "Examples (depending on API):\n"
        "- name, description\n"
        "- username, email\n"
        "- brand, category\n"
        "- log message"
    ),
    type=openapi.TYPE_STRING,
)

IS_ACTIVE_PARAM = openapi.Parameter(
    name="is_active",
    in_=openapi.IN_QUERY,
    description=(
        "Filter results by active status.\n\n"
        "- `true` → active records\n"
        "- `false` → inactive records"
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



# Audit Log params


U_ID_PARAM = openapi.Parameter(
    name="u_id",
    in_=openapi.IN_QUERY,
    description="Filter logs by user ID (actor who performed the action)",
    type=openapi.TYPE_NUMBER,
    required=False
)

ACTION_PARAM = openapi.Parameter(
    name="action",
    in_=openapi.IN_QUERY,
    description=(
        "Filter logs by action type.\n\n"
        "Allowed values:\n"
        "- `LOGIN` → Login events\n"
        "- `LOGOUT` → Logout events\n"
        "- `CREATE` → Record creation\n"
        "- `UPDATE` → Record updates\n"
        "- `SOFT_DELETE` → Record deactivation"
        ),
    type=openapi.TYPE_STRING,
    enum=["LOGIN", "LOGOUT", "CREATE", "UPDATE", "SOFT_DELETE"],
    required=False
)

MODEL_PARAM = openapi.Parameter(
    name="model",
    in_=openapi.IN_QUERY,
    description=(
        "Filter logs by entity type.\n\n"
        "Allowed values:\n"
        "- `brand`\n"
        "- `category`\n"
        "- `product`"
    ),
    type=openapi.TYPE_STRING,
    enum=["brand", "category", "product"],
    required=False
)

OBJECT_ID_PARAM = openapi.Parameter(
    name="object_id",
    in_=openapi.IN_QUERY,
    description="Filter logs by related object ID",
    type=openapi.TYPE_STRING,
    required=False
)

# User Param

ID_PARAM = openapi.Parameter(
    name="id",
    in_=openapi.IN_QUERY,
    description="Filter records by primary ID (context-dependent)",
    type=openapi.TYPE_NUMBER,
    required=False
)




IS_STAFF_PARAM = openapi.Parameter(
    name="is_staff",
    in_=openapi.IN_QUERY,
    description=(
        "Filter users by staff status.\n\n"
        "- `true` → users with staff status\n"
        "- `false` → users without staff status"
    ),
    type=openapi.TYPE_STRING,
    required=False
)


DATE_FROM_PARAM = openapi.Parameter(
    name="date_from",
    in_=openapi.IN_QUERY,
    description=(
        "Filter records created on or after this date.\n\n"
        "**Format:** `YYYY-MM-DD`\n\n"
        "Example: `2025-01-01`"
    ),
    type=openapi.TYPE_STRING,
    required=False
)


DATE_TO_PARAM = openapi.Parameter(
    name="date_to",
    in_=openapi.IN_QUERY,
    description=(
        "Filter records created on or before this date.\n\n"
        "**Format:** `YYYY-MM-DD`\n\n"
        "Example: `2025-01-31`"
    ),
    type=openapi.TYPE_STRING,
    required=False
)