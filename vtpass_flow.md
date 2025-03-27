# VTPass API Integration Flow

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client as Frontend Client
    participant API as PayLink API
    participant Auth as Authentication Service
    participant Service as VTPass Service
    participant Cache as Response Cache
    participant VTPass as VTPass API
    
    Client->>API: Request (with JWT token)
    API->>Auth: Validate token
    Auth-->>API: Token validation result
    
    alt Invalid Token
        API-->>Client: 401 Unauthorized
    else Valid Token
        API->>Service: Forward request
        
        alt Cached Response Available
            Service->>Cache: Check cache
            Cache-->>Service: Return cached data
            Service-->>API: Return response
            API-->>Client: Return API response
        else No Cache Available
            Service->>Cache: Check cache
            Cache-->>Service: No data available
            
            Service->>VTPass: Make API request
            Note over Service,VTPass: Headers: API Key, Secret Key<br/>Public Key in payload
            
            VTPass-->>Service: Return response
            
            Service->>Cache: Store response
            Service-->>API: Return response
            API-->>Client: Return API response
        end
    end
```

## Flowchart Diagram

```mermaid
flowchart TD
    A[Frontend Client] --> B[PayLink API]
    B --> C{Authentication}
    C -->|Invalid| D[Return 401]
    C -->|Valid| E[VTPass Service]
    
    E --> F{Check Cache}
    F -->|Cache Hit| G[Return Cached Response]
    F -->|Cache Miss| H[Forward to VTPass API]
    
    H -->|API Key & Secret| I[VTPass API]
    I --> J[Process Response]
    J --> K[Cache Response]
    K --> L[Return to Client]
    G --> L
    
    subgraph PayLink Backend
    B
    C
    E
    F
    J
    K
    end
    
    subgraph External Services
    I
    end
```

## Process Documentation

### Authentication Process
1. **Client Authentication**: Frontend authenticates with PayLink API using JWT
2. **VTPass Authentication**: Backend authenticates with VTPass using:
   - API Key (in headers)
   - Secret Key (in headers)
   - Public Key (in request payload when required)

### API Request Flow
1. Frontend makes request to PayLink API endpoint
2. API validates the user's JWT token
3. Request is forwarded to the VTPass service layer
4. Service layer checks for cached response
5. If no cache exists, the request is forwarded to VTPass API
6. Response is cached for future requests
7. Response is returned to client

### Supported VTPass Operations
- Airtime Purchase
- Data Bundle Purchase
- Electricity Bill Payment
- Cable TV Subscription
- Internet Service Payment
- Education Payments

### Error Handling
- Network errors are retried with exponential backoff
- Invalid parameters trigger validation errors
- Timeouts are handled gracefully with client notification
- All transactions are logged for audit purposes 