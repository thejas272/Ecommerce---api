# E-Commerce Backend API (Django REST Framework)

🚧 **Status:** Under Active Development

A modular and scalable **E-Commerce Backend API** built using **Django REST Framework**.  
The project focuses on clean REST design, JWT-based authentication, role-based admin access, soft deletes, and clear separation between public and admin APIs.

---

## 📌 Key Features Implemented

### 🔐 Authentication & User Management
- Custom User model (based on `AbstractUser`)
- JWT authentication using **SimpleJWT**
  - Access token
  - Refresh token
  - Refresh token blacklisting (logout)
- User registration
- User login
- Token refresh
- Logout
- Password change
- User profile (`/me/`) APIs
- Rate limiting for:
  - Login
  - Refresh token

---

### 🛍️ Product Catalog Management

#### Categories
- Hierarchical categories implemented using **django-mptt**
- Efficient tree traversal (parent, children, descendants)
- Slug-based public access
- Soft delete using `is_active`
- Public and Admin APIs separated

#### Brands
- Slug-based public access
- Soft delete (`is_active`)
- Admin-only management APIs

#### Products
- Linked to Category and Brand
- Slug-based public product detail API
- Soft delete (`is_active`)
- Inventory support (`stock`)
- Price handling using `DecimalField`
- Uniqueness enforced per `(name, brand)`
- Slug auto-generated

---

### 🧑‍💼 Admin vs Public API Separation

- **Public APIs**
  - Only return `is_active=True` records
  - Slug-based detail access
  - Read-only access

- **Admin APIs**
  - Access controlled using:
    - `IsAuthenticated`
    - `DjangoModelPermissions`
  - Can view **active + inactive** records
  - Can create, update, soft-delete, and restore records
  - Uses ID-based access
  - Separate serializers for admin responses

---

## 📋 Logging

- Application-level logging configured for debugging and monitoring
- Useful for tracking API errors, validation failures, and system behavior
- Designed to be extendable for production-grade log aggregation

---

### 📖 API Documentation
- Swagger UI integrated using **drf-yasg**
- Clear separation using Swagger tags:
  - Public APIs
  - Admin APIs (`Admin / Products`, `Admin / Categories`, etc.)

---



## 🆕 Recent Updates

- Added application-level logging for admin operations
- Integrated **django-mptt** for efficient hierarchical category management
- Implemented filtering for both public and admin listing APIs



## 🧭 API Structure (Current)

### 🔓 Public APIs

```text
GET  /api/catalog/categories/
GET  /api/catalog/categories/{slug}/

GET  /api/catalog/brands/
GET  /api/catalog/brands/{slug}/

GET  /api/catalog/products/
GET  /api/catalog/products/{slug}/

```

### 🔐 Authentication APIs


```text
POST /api/accounts/register/
POST /api/accounts/login/
POST /api/accounts/token/refresh/
POST /api/accounts/logout/

GET   /api/accounts/me/
PATCH /api/accounts/me/
PATCH /api/accounts/me/password/

```


### 🧑‍💼 Admin APIs

#### Admin Category APIs

```text

GET    /api/catalog/admin/categories/
POST   /api/catalog/admin/categories/
GET    /api/catalog/admin/categories/{id}/
PATCH  /api/catalog/admin/categories/{id}/
DELETE /api/catalog/admin/categories/{id}/

```

#### Admin Brand APIs


```text

GET    /api/catalog/admin/brands/
POST   /api/catalog/admin/brands/
GET    /api/catalog/admin/brands/{id}/
PATCH  /api/catalog/admin/brands/{id}/
DELETE /api/catalog/admin/brands/{id}/

```

#### Admin Product APIs


```text

GET    /api/catalog/admin/products/
POST   /api/catalog/admin/products/
GET    /api/catalog/admin/products/{id}/
PATCH  /api/catalog/admin/products/{id}/
DELETE /api/catalog/admin/products/{id}/

```


## ⚙️ Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- JWT (djangorestframework-simplejwt)
- drf-yasg (Swagger / ReDoc)




## 🚀 Local Setup Instructions

# Clone the repository
```bash
git clone https://github.com/thejas272/Ecommerce---api
```


# Create virtual environment
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```


# Install dependencies
```bash
pip install -r requirements.txt
```


# Apply migrations
```bash
python manage.py migrate
```


# Create superuser
```bash
python manage.py createsuperuser
```


# Run development server
```bash
python manage.py runserver
```



## 📖 API Documentation


```text

/swagger/

/redoc/

```


## 🛠️ Work in Progress

- Cart APIs
- Order & checkout flow
- Payment integration (mock)
- Reviews & ratings
- Inventory optimizations
- Admin analytics & reports