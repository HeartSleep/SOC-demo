# 🚀 GraphQL Integration for SOC Platform

## Overview

The SOC Platform now features a complete **GraphQL API** alongside the REST API, providing flexible data fetching, real-time subscriptions, and improved performance through query optimization.

## 🎯 Key Benefits

### Why GraphQL?

1. **Flexible Data Fetching**: Request exactly what you need, nothing more
2. **Single Request**: Fetch related data in one query instead of multiple REST calls
3. **Real-time Updates**: Built-in subscription support for live data
4. **Type Safety**: Strongly typed schema with auto-generated TypeScript types
5. **Self-Documenting**: Interactive GraphiQL explorer with schema introspection
6. **Performance**: Automatic query batching and caching

## 📁 Implementation Structure

```
backend/
├── app/
│   ├── graphql/
│   │   ├── schema.py           # GraphQL schema definition
│   │   ├── graphql_app.py      # FastAPI integration
│   │   └── resolvers/          # Field resolvers
│   │       ├── user_resolver.py
│   │       ├── asset_resolver.py
│   │       └── ...

frontend/
├── src/
│   ├── graphql/
│   │   ├── client.ts           # Apollo Client setup
│   │   ├── queries.ts          # GraphQL queries
│   │   ├── mutations.ts        # GraphQL mutations
│   │   └── subscriptions.ts    # GraphQL subscriptions
│   ├── composables/
│   │   └── useGraphQL.ts       # Vue composables
```

## 🔧 Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install strawberry-graphql strawberry-graphql[fastapi] graphene
```

### 2. Integration with FastAPI

```python
# In app/main.py
from app.graphql.graphql_app import integrate_graphql

app = FastAPI()

# Integrate GraphQL
integrate_graphql(app)
```

### 3. Access GraphQL Endpoints

- **GraphQL Endpoint**: `http://localhost:8000/graphql`
- **GraphiQL Interface**: `http://localhost:8000/graphql` (browser)
- **Health Check**: `http://localhost:8000/graphql/health`
- **Metrics**: `http://localhost:8000/graphql/metrics`

## 🎨 Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install @apollo/client graphql @vue/apollo-composable
```

### 2. Configure Apollo Client

```typescript
// In main.ts
import { apolloClient } from '@/graphql/client'
import { DefaultApolloClient } from '@vue/apollo-composable'

app.provide(DefaultApolloClient, apolloClient)
```

### 3. Environment Variables

```env
VITE_GRAPHQL_URL=http://localhost:8000/graphql
VITE_GRAPHQL_WS_URL=ws://localhost:8000/graphql
```

## 📊 Schema Overview

### Types

```graphql
type User {
  id: String!
  username: String!
  email: String!
  fullName: String!
  role: String!
  isActive: Boolean!
  permissions: [String!]!
  tasks: [Task!]!
  activityCount(days: Int = 7): Int!
}

type Asset {
  id: String!
  name: String!
  assetType: AssetType!
  status: String!
  criticality: Severity!
  vulnerabilities(severity: Severity, limit: Int): [Vulnerability!]!
  riskScore: Float!
  scanHistory(limit: Int): [ScanResult!]!
}

type Vulnerability {
  id: String!
  title: String!
  severity: Severity!
  status: String!
  cvssScore: Float!
  asset: Asset!
  remediation: String
}

enum AssetType {
  DOMAIN
  IP
  URL
  NETWORK
  APPLICATION
}

enum Severity {
  LOW
  MEDIUM
  HIGH
  CRITICAL
}
```

## 🔍 Query Examples

### Basic Query

```graphql
query GetAssets {
  assets(first: 10, criticality: HIGH) {
    edges {
      id
      name
      assetType
      riskScore
      vulnerabilities(severity: CRITICAL) {
        id
        title
        cvssScore
      }
    }
    totalCount
  }
}
```

### Nested Query with Fragments

```graphql
fragment AssetDetails on Asset {
  id
  name
  assetType
  criticality
  owner
}

fragment VulnerabilityInfo on Vulnerability {
  id
  title
  severity
  cvssScore
}

query GetAssetWithDetails($id: String!) {
  asset(id: $id) {
    ...AssetDetails
    vulnerabilities(limit: 10) {
      ...VulnerabilityInfo
      remediation
    }
    scanHistory(limit: 5) {
      id
      scanType
      completedAt
      findingsCount
    }
  }
}
```

### Search Query

```graphql
query GlobalSearch($query: String!) {
  search(query: $query, types: ["User", "Asset", "Vulnerability"]) {
    ... on User {
      __typename
      id
      username
      email
    }
    ... on Asset {
      __typename
      id
      name
      criticality
    }
    ... on Vulnerability {
      __typename
      id
      title
      severity
    }
  }
}
```

## 🔄 Mutation Examples

### Create Asset

```graphql
mutation CreateAsset($input: CreateAssetInput!) {
  createAsset(input: $input) {
    id
    name
    assetType
    status
    criticality
  }
}

# Variables
{
  "input": {
    "name": "api.example.com",
    "assetType": "DOMAIN",
    "tags": ["production", "api"],
    "criticality": "HIGH",
    "organization": "Example Corp",
    "owner": "DevOps Team"
  }
}
```

### Update Task Status

```graphql
mutation UpdateTaskProgress($id: String!, $status: TaskStatus!, $progress: Int) {
  updateTaskStatus(id: $id, status: $status, progress: $progress) {
    id
    status
    progress
    updatedAt
  }
}
```

## 📡 Subscription Examples

### Real-time System Metrics

```graphql
subscription SystemMetrics {
  systemMetricsStream {
    cpuUsage
    memoryUsageMb
    errorRate
    requestsPerMinute
    activeUsers
    timestamp
  }
}
```

### Vulnerability Alerts

```graphql
subscription CriticalAlerts {
  vulnerabilityAlerts(minSeverity: HIGH) {
    id
    title
    severity
    cvssScore
    asset {
      id
      name
      criticality
    }
    discoveredAt
  }
}
```

### Task Progress

```graphql
subscription TaskProgress($taskId: String!) {
  taskUpdates(taskId: $taskId) {
    id
    progress
    status
    logs(limit: 5)
  }
}
```

## 💻 Frontend Usage

### Using Composables

```vue
<script setup lang="ts">
import { useGraphQLQuery, useGraphQLMutation, useGraphQLSubscription } from '@/composables/useGraphQL'
import { GET_ASSETS, CREATE_ASSET, VULNERABILITY_ALERTS } from '@/graphql'

// Query
const { data: assets, loading, refetch } = useGraphQLQuery(GET_ASSETS, {
  first: 20,
  criticality: 'HIGH'
})

// Mutation
const { execute: createAsset } = useGraphQLMutation(CREATE_ASSET)

const handleCreate = async () => {
  const result = await createAsset(
    { input: newAssetData },
    'Asset created successfully',
    'Failed to create asset'
  )
  if (result) {
    await refetch()
  }
}

// Subscription
const { data: alerts } = useGraphQLSubscription(VULNERABILITY_ALERTS, {
  minSeverity: 'HIGH'
})
</script>

<template>
  <div>
    <LoadingSpinner v-if="loading" />

    <AssetList :assets="assets?.edges" />

    <AlertNotification
      v-for="alert in alerts"
      :key="alert.id"
      :alert="alert"
    />
  </div>
</template>
```

### Paginated Query

```vue
<script setup lang="ts">
import { usePaginatedQuery } from '@/composables/useGraphQL'
import { GET_USERS } from '@/graphql/queries'

const { data, loading, hasNextPage, loadMore } = usePaginatedQuery(
  GET_USERS,
  { first: 20 }
)
</script>

<template>
  <div>
    <UserList :users="data?.users?.edges" />

    <button
      v-if="hasNextPage"
      @click="loadMore"
      :disabled="loading"
    >
      Load More
    </button>
  </div>
</template>
```

### Real-time Data

```vue
<script setup lang="ts">
import { useRealtimeData } from '@/composables/useGraphQL'
import { GET_SYSTEM_METRICS, SYSTEM_METRICS_STREAM } from '@/graphql'

const { data: metrics } = useRealtimeData(
  GET_SYSTEM_METRICS,
  SYSTEM_METRICS_STREAM
)
</script>

<template>
  <MetricsDashboard :metrics="metrics" />
</template>
```

## 🛡️ Security Features

### 1. Authentication
- JWT token validation for queries/mutations
- WebSocket authentication for subscriptions
- Role-based access control

### 2. Rate Limiting
- 100 requests per minute per IP
- Configurable limits per operation type
- WebSocket connection limits

### 3. Query Depth Limiting
- Maximum query depth: 10 levels
- Prevents malicious deep queries
- Configurable per operation

### 4. Query Complexity Analysis
- Cost analysis for expensive operations
- Automatic rejection of complex queries
- Field-level complexity scoring

## 📈 Performance Optimizations

### 1. Query Batching
- Automatic batching of multiple queries
- Reduces network overhead
- Configurable batch interval (20ms)

### 2. Caching
- Apollo Client cache
- Server-side caching with TTL
- Cache invalidation strategies

### 3. DataLoader Pattern
- N+1 query prevention
- Automatic batching of database queries
- Request-level caching

### 4. Persisted Queries
- Query whitelisting for production
- Reduced payload size
- Enhanced security

## 🧪 Testing

### GraphiQL Explorer

Access the interactive explorer at `http://localhost:8000/graphql`

Features:
- Schema documentation
- Auto-completion
- Query history
- Variable editor
- Real-time results

### Unit Testing

```python
# Test resolver
async def test_get_user_resolver():
    result = await schema.execute(
        """
        query {
          user(id: "123") {
            id
            username
            email
          }
        }
        """
    )
    assert result.data["user"]["id"] == "123"
```

### Integration Testing

```typescript
// Test Vue component with GraphQL
import { mount } from '@vue/test-utils'
import { createMockClient } from 'mock-apollo-client'

test('loads assets', async () => {
  const mockClient = createMockClient()
  mockClient.setRequestHandler(
    GET_ASSETS,
    () => Promise.resolve({ data: mockAssets })
  )

  const wrapper = mount(AssetList, {
    global: {
      provide: {
        [DefaultApolloClient]: mockClient
      }
    }
  })

  await flushPromises()
  expect(wrapper.findAll('.asset-item')).toHaveLength(mockAssets.length)
})
```

## 📊 Metrics & Monitoring

### GraphQL Metrics Endpoint

```bash
curl http://localhost:8000/graphql/metrics
```

Response:
```json
{
  "total_requests": 15234,
  "avg_duration_ms": 45.2,
  "success_rate": 0.998,
  "operations": [
    "GetAssets",
    "CreateUser",
    "SystemMetricsStream"
  ],
  "cache_hit_rate": 0.75
}
```

### Monitoring Dashboard

The GraphQL integration includes:
- Request/response times per operation
- Error rates and types
- Cache hit rates
- Active subscriptions
- Query complexity scores

## 🔄 Migration from REST

### Gradual Migration Strategy

1. **Phase 1**: Run GraphQL alongside REST
2. **Phase 2**: Migrate read operations to GraphQL
3. **Phase 3**: Migrate write operations
4. **Phase 4**: Implement subscriptions
5. **Phase 5**: Deprecate REST endpoints

### REST to GraphQL Mapping

| REST Endpoint | GraphQL Operation |
|--------------|-------------------|
| `GET /api/v1/users` | `query { users }` |
| `POST /api/v1/users` | `mutation { createUser }` |
| `GET /api/v1/users/:id` | `query { user(id: $id) }` |
| `PUT /api/v1/users/:id` | `mutation { updateUser }` |
| `DELETE /api/v1/users/:id` | `mutation { deleteUser }` |
| WebSocket `/ws` | `subscription { ... }` |

## 🚀 Best Practices

1. **Use Fragments** for reusable selections
2. **Implement DataLoaders** to prevent N+1 queries
3. **Use Subscriptions** sparingly for truly real-time data
4. **Batch Mutations** when possible
5. **Cache Aggressively** with proper invalidation
6. **Monitor Performance** with built-in metrics
7. **Version Schema** changes carefully
8. **Document Resolvers** thoroughly
9. **Test Subscriptions** with connection handling
10. **Secure Endpoints** with proper authentication

## 🎉 Summary

The GraphQL integration provides:

- ✅ **Flexible querying** with exact data requirements
- ✅ **Real-time subscriptions** for live updates
- ✅ **Type safety** with auto-generated types
- ✅ **Performance optimization** through batching and caching
- ✅ **Self-documenting API** with GraphiQL
- ✅ **Security features** including rate limiting and depth limiting
- ✅ **Vue.js integration** with composables
- ✅ **Monitoring and metrics** for observability
- ✅ **Gradual migration path** from REST
- ✅ **Production-ready** with all enterprise features

The platform now offers both REST and GraphQL APIs, allowing clients to choose the best approach for their specific needs!