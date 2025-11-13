---
trigger: always_on
---

# Full-Stack Integration

## Communication Flow
```
ClientFramework (Next.js)  ←→  ServerFramework (FastAPI)
     Port 1109                      Port 1996
```

## GraphQL Integration
- **Client**: graphql-request queries ServerFramework's Strawberry GraphQL endpoint
- **Server**: Auto-generates GraphQL schema from Pydantic BLL models
- **Real-time**: GraphQL subscriptions via graphql-ws and broadcaster
- **Type Safety**: Zod schemas (client) match Pydantic models (server)

## Data Model Synchronization
```
ServerFramework (Python)          ClientFramework (TypeScript)
├── Pydantic Models              ├── Zod Schemas
│   └── ProviderModel            │   └── ProviderSchema
├── GraphQL Types (auto)         ├── TypeScript Types (inferred)
│   └── ProviderType             │   └── Provider
└── Database (SQLAlchemy)        └── SWR Cache
```

## Authentication Flow
1. **JWT Generation**: ServerFramework's UserManager.generate_jwt_token()
2. **Storage**: Client stores in cookies with domain configuration
3. **Validation**: Next.js middleware validates JWT before protected routes
4. **OAuth2**: Client handles flow, exchanges code with ServerFramework

## Development Workflow
1. Define Pydantic model in ServerFramework BLL
2. Model automatically generates GraphQL schema
3. Create matching Zod schema in ClientFramework
4. Use SWR hook to fetch data
5. Components consume typed data

## Key Integration Points
- `/graphql` - Main GraphQL endpoint
- `/v1/user/authorize` - Login endpoint
- `/v1/extension` - Extension management
- `/v1/provider` - Provider configuration
- WebSocket - Real-time subscriptions

## Environment Configuration
### Client (.env)
- APP_URI=http://localhost:1109
- API_URI=http://localhost:1996
- AUTH_URI=/user
- PRIVATE_ROUTES=/chat,/team,/settings

### Server (.env)
- SERVER_URI=http://localhost:1996
- DATABASE_TYPE=sqlite
- ROOT_ID, SYSTEM_ID
- APP_EXTENSIONS=email,auth_mfa
