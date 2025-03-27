# PayLink API Documentation

This document provides a comprehensive reference for the PayLink API endpoints, request/response formats, and authentication requirements.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://paylinkapi.onrender.com`

## Authentication

The API uses JWT (JSON Web Token) for authentication. Include the token in the Authorization header for protected endpoints:

```
Authorization: Bearer <access_token>
```

### Authentication Endpoints

#### Register User

```
POST /api/users/register/
```

Creates a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "securepassword",
  "phone_number": "+2348012345678"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "username",
  "phone_number": "+2348012345678"
}
```

#### Login

```
POST /api/users/login/
```

Authenticates a user and returns access and refresh tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "username"
  }
}
```

#### Refresh Token

```
POST /api/users/token/refresh/
```

Obtains a new access token using a refresh token.

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout

```
POST /api/users/logout/
```

Blacklists the refresh token, effectively logging out the user.

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (205 Reset Content):**
```json
{
  "detail": "Successfully logged out."
}
```

## User Endpoints

### Get User Profile

```
GET /api/users/profile/
```

Returns the authenticated user's profile information.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "username",
  "phone_number": "+2348012345678",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St",
  "state": "Lagos",
  "vtpass_account_id": "VT-12345678",
  "vtpass_balance": "1000.00",
  "preferred_network": "MTN",
  "bank_name": "Access Bank",
  "account_number": "0123456789",
  "account_name": "John Doe",
  "kyc_level": 1
}
```

### Update User Profile

```
PATCH /api/users/profile/
```

Updates the authenticated user's profile information.

**Request Body:**
```json
{
  "phone_number": "+2348012345678",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St",
  "state": "Lagos"
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "username",
  "phone_number": "+2348012345678",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St",
  "state": "Lagos"
}
```

## VTPass Integration Endpoints

### Get Services

```
GET /api/vtpass/services/{service_type}/
```

Returns available services for the specified service type.

**Parameters:**
- `service_type` (path): Type of service (airtime, data, electricity, tv, etc.)

**Response (200 OK):**
```json
{
  "code": "success",
  "response_description": "Services retrieved successfully",
  "content": [
    {
      "id": "mtn",
      "name": "MTN",
      "description": "MTN Airtime"
    },
    {
      "id": "airtel",
      "name": "Airtel",
      "description": "Airtel Airtime"
    }
  ]
}
```

### Get Service Variations

```
GET /api/vtpass/service-variations/{service_id}/
```

Returns available variations for a specific service.

**Parameters:**
- `service_id` (path): ID of the service

**Response (200 OK):**
```json
{
  "code": "success",
  "response_description": "Variations retrieved successfully",
  "content": {
    "variations": [
      {
        "variation_code": "mtn-1gb",
        "name": "1GB",
        "amount": "1000.00"
      },
      {
        "variation_code": "mtn-2gb",
        "name": "2GB",
        "amount": "2000.00"
      }
    ]
  }
}
```

### Purchase Service

```
POST /api/vtpass/purchase/
```

Purchases a service through VTPass.

**Request Body:**
```json
{
  "service_id": "mtn",
  "variation_code": "mtn-1gb",
  "amount": "1000.00",
  "phone": "08012345678",
  "billersCode": "12345678" // Only required for certain services
}
```

**Response (200 OK):**
```json
{
  "code": "success",
  "response_description": "Transaction successful",
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "product_name": "MTN 1GB Data",
    "amount": "1000.00",
    "transaction_id": "12345678",
    "phone": "08012345678"
  }
}
```

### Get Transaction History

```
GET /api/vtpass/transactions/
```

Returns the authenticated user's transaction history.

**Query Parameters:**
- `page` (optional): Page number for pagination
- `limit` (optional): Number of items per page
- `status` (optional): Filter by transaction status (pending, successful, failed)
- `type` (optional): Filter by transaction type (airtime, data, electricity, etc.)

**Response (200 OK):**
```json
{
  "count": 10,
  "next": "https://paylinkapi.onrender.com/api/vtpass/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "transaction_type": "data",
      "service_id": "mtn",
      "amount": "1000.00",
      "phone_number": "08012345678",
      "status": "successful",
      "created_at": "2025-03-27T10:30:45Z"
    }
  ]
}
```

### Get Transaction Details

```
GET /api/vtpass/transactions/{transaction_id}/
```

Returns details of a specific transaction.

**Parameters:**
- `transaction_id` (path): ID of the transaction

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "transaction_type": "data",
  "service_id": "mtn",
  "amount": "1000.00",
  "phone_number": "08012345678",
  "email": "user@example.com",
  "request_id": "12345678",
  "vtpass_reference": "VT12345678",
  "status": "successful",
  "response_data": {
    "product_name": "MTN 1GB Data",
    "unique_element": "08012345678",
    "unit_cost": "1000.00",
    "quantity": 1,
    "service_verification": null,
    "channel": "api",
    "amount": "1000.00",
    "commission": "20.00",
    "total_amount": "1000.00",
    "wallet_balance": "9000.00",
    "currency": "NGN",
    "transaction_date": "27-Mar-2025 10:30:45",
    "transaction_reference": "VT12345678"
  },
  "created_at": "2025-03-27T10:30:45Z",
  "updated_at": "2025-03-27T10:31:00Z"
}
```

## Status Codes

The API uses standard HTTP status codes:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

## Rate Limiting

The API implements rate limiting to prevent abuse. Limits are as follows:

- Anonymous requests: 100 requests per hour
- Authenticated requests: 1000 requests per hour

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1616992800
```

## API Versioning

The API uses URL-based versioning. The current version is embedded in the path:

```
/api/v1/users/profile/
```

Future versions will use incremented version numbers:

```
/api/v2/users/profile/
```

## Error Responses

Error responses follow a standard format:

```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "Invalid parameters",
  "errors": [
    {
      "field": "email",
      "message": "This field is required."
    }
  ]
}
```

Common error codes:

- `INVALID_CREDENTIALS`: Authentication failed
- `VALIDATION_ERROR`: Request validation failed
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `PERMISSION_DENIED`: Not authorized to access the resource
- `SERVER_ERROR`: Unexpected server error 