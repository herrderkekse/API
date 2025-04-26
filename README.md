MariaDB
pip install fastapi uvicorn[standard] jinja2 sqlalchemy aiomysql python-jose[cryptography] passlib[bcrypt] python-multipart pydantic-settings

# API Documentation

## Authentication Endpoints

### POST /auth/token
Login endpoint to obtain access token.

**Request Body (form-data):**
- `username`: string
- `password`: string

**Response:**
```json
{
    "access_token": "string",
    "token_type": "bearer",
    "user_id": integer
}
```

## User Endpoints

### GET /user/all
Get all users (admin only).

**Response:** Array of UserResponse objects
```json
[
    {
        "uid": integer,
        "name": string,
        "cash": float,
        "creation_time": datetime,
        "is_admin": boolean
    }
]
```

### GET /user/{uid}
Get user by ID. Users can only access their own data unless they are admins.

**Path Parameters:**
- `uid`: integer

**Response:** UserResponse object

### POST /user
Create new user (admin only).

**Request Body:**
```json
{
    "name": string,
    "password": string,
    "is_admin": boolean (optional, default: false)
}
```

**Response:** UserResponse object

### PATCH /user/{uid}
Update user information. Users can only update their own data unless they are admins.

**Path Parameters:**
- `uid`: integer

**Request Body:**
```json
{
    "name": string (optional),
    "cash": float (optional)
}
```

**Response:** UserResponse object

### DELETE /user/{uid}
Delete user. Users can only delete their own account unless they are admins.

**Path Parameters:**
- `uid`: integer

**Response:**
```json
{
    "message": "User deleted successfully"
}
```

## Device Endpoints

### GET /device/all
Get all devices.

**Response:** Array of DeviceResponse objects
```json
[
    {
        "id": integer,
        "name": string,
        "type": string,
        "hourly_cost": float,
        "user_id": integer (nullable),
        "end_time": datetime (nullable),
        "time_left": float (nullable)
    }
]
```

### GET /device/{device_id}
Get device by ID.

**Path Parameters:**
- `device_id`: integer (1-5)

**Response:** DeviceResponse object

### POST /device/start/{device_id}
Start a device.

**Path Parameters:**
- `device_id`: integer (1-5)

**Request Body:**
```json
{
    "user_id": integer,
    "duration_minutes": integer
}
```

**Response:** DeviceResponse object

### POST /device/stop/{device_id}
Stop a device (admin only).

**Path Parameters:**
- `device_id`: integer (1-5)

**Response:**
```json
{
    "message": "Device stopped successfully",
    "device": DeviceResponse,
    "refund_amount": float
}
```

### WebSocket /device/ws/timeleft/{device_id}
WebSocket endpoint for real-time device time updates.

**Path Parameters:**
- `device_id`: integer (1-5)

**WebSocket Messages:**
```json
{
    "device_id": integer,
    "time_left": integer,
    "status": string,
    "user_id": integer (nullable)
}
```

### WebSocket /device/ws/status/{device_id}
WebSocket endpoint for real-time device status updates.

**Path Parameters:**
- `device_id`: integer (1-5)

**WebSocket Messages:**
```json
{
    "device_id": integer,
    "running": boolean,
    "end_time": string (ISO format, only when running: true)
}
```

## Authentication

All endpoints except `/auth/token` require Bearer token authentication. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Idempotency

For POST requests, you can include an idempotency key in the header to prevent duplicate operations:

```
X-Idempotency-Key: <unique_key>
```

## Error Responses

All endpoints may return the following error responses:

- 400 Bad Request: Invalid input data
- 401 Unauthorized: Invalid or missing authentication
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Requested resource not found
- 500 Internal Server Error: Server-side error
