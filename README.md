# PayLink Backend API

A Django REST API for the PayLink application with VTPass integration for utility payments.

## Features

- User authentication with JWT tokens
- Custom user model with VTPass integration
- Transaction management for utility payments
- API documentation using OpenAPI and Swagger

## Setup Instructions

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

1. Clone the repository
2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` and add your VTPass API keys

5. Run migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

## API Documentation

### Swagger UI

The API documentation is available through Swagger UI at:

```
http://localhost:8000/api/docs/
```

### Redoc

Alternative documentation using Redoc is available at:

```
http://localhost:8000/api/redoc/
```

### OpenAPI Schema

The raw OpenAPI schema is available at:

```
http://localhost:8000/api/schema/
```

## API Endpoints

### Authentication

- `POST /api/users/register/` - Register a new user
- `POST /api/users/login/` - Login and get JWT tokens
- `POST /api/users/token/refresh/` - Refresh JWT token

### User Profile

- `GET /api/users/profile/` - Get user profile
- `PUT/PATCH /api/users/profile/` - Update user profile
- `PUT /api/users/set-pin/` - Set transaction PIN

### VTPass Services

- `GET /api/users/balance/` - Get VTPass account balance
- `GET /api/users/services/{service_type}/` - Get services by type (e.g., airtime, data)
- `POST /api/users/purchase/` - Purchase a service
- `GET /api/users/transaction-status/{request_id}/` - Check transaction status
- `GET /api/users/transactions/` - List user transactions

## VTPass Integration

This backend integrates with VTPass Sandbox API for testing:

- **Base URL**: https://sandbox.vtpass.com/api
- **Documentation**: https://www.vtpass.com/documentation/

## Security

- JWT tokens for authentication
- PIN verification for transactions
- All sensitive data stored in environment variables

## License

This project is proprietary and confidential.
