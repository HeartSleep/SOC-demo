/**
 * GraphQL Client Configuration for SOC Platform
 * Provides Apollo Client setup with authentication and subscriptions
 */

import { ApolloClient, InMemoryCache, createHttpLink, split, ApolloLink } from '@apollo/client'
import { setContext } from '@apollo/client/link/context'
import { WebSocketLink } from '@apollo/client/link/ws'
import { getMainDefinition } from '@apollo/client/utilities'
import { onError } from '@apollo/client/link/error'
import { RetryLink } from '@apollo/client/link/retry'
import { BatchHttpLink } from '@apollo/client/link/batch-http'

// GraphQL endpoints
const GRAPHQL_ENDPOINT = import.meta.env.VITE_GRAPHQL_URL || 'http://localhost:8000/graphql'
const WS_ENDPOINT = import.meta.env.VITE_GRAPHQL_WS_URL || 'ws://localhost:8000/graphql'

/**
 * Create authentication link
 */
const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('access_token')

  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : ''
    }
  }
})

/**
 * Create error handling link
 */
const errorLink = onError(({ graphQLErrors, networkError, operation, forward }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, locations, path, extensions }) => {
      console.error(
        `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
      )

      // Handle specific error codes
      if (extensions?.code === 'UNAUTHENTICATED') {
        // Redirect to login
        window.location.href = '/login'
      }

      if (extensions?.code === 'RATE_LIMITED') {
        // Show rate limit message
        console.warn('Rate limit reached. Please wait before making more requests.')
      }
    })
  }

  if (networkError) {
    console.error(`[Network error]: ${networkError}`)

    // Retry on network errors
    if (networkError.message.includes('Failed to fetch')) {
      return forward(operation)
    }
  }
})

/**
 * Create retry link for resilience
 */
const retryLink = new RetryLink({
  delay: {
    initial: 300,
    max: Infinity,
    jitter: true
  },
  attempts: {
    max: 3,
    retryIf: (error, _operation) => {
      // Retry on network errors
      if (error && error.networkError) {
        return true
      }
      // Don't retry on authentication errors
      if (error && error.graphQLErrors) {
        return !error.graphQLErrors.some(e => e.extensions?.code === 'UNAUTHENTICATED')
      }
      return false
    }
  }
})

/**
 * Create HTTP link with batching
 */
const httpLink = new BatchHttpLink({
  uri: GRAPHQL_ENDPOINT,
  batchMax: 10, // Max number of operations to batch
  batchInterval: 20 // Ms to wait before batching
})

/**
 * Create WebSocket link for subscriptions
 */
const wsLink = new WebSocketLink({
  uri: WS_ENDPOINT,
  options: {
    reconnect: true,
    reconnectionAttempts: 5,
    connectionParams: () => {
      const token = localStorage.getItem('access_token')
      return {
        authorization: token ? `Bearer ${token}` : ''
      }
    },
    connectionCallback: (error: any) => {
      if (error) {
        console.error('WebSocket connection error:', error)
      } else {
        console.log('WebSocket connected')
      }
    }
  }
})

/**
 * Split link based on operation type
 */
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query)
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    )
  },
  wsLink,
  httpLink
)

/**
 * Create the Apollo Client instance
 */
export const apolloClient = new ApolloClient({
  link: ApolloLink.from([
    errorLink,
    authLink,
    retryLink,
    splitLink
  ]),
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          // Paginated fields
          users: {
            keyArgs: ['role', 'isActive'],
            merge(existing = { edges: [] }, incoming) {
              return {
                ...incoming,
                edges: [...existing.edges, ...incoming.edges]
              }
            }
          },
          assets: {
            keyArgs: ['assetType', 'criticality', 'tags'],
            merge(existing = { edges: [] }, incoming) {
              return {
                ...incoming,
                edges: [...existing.edges, ...incoming.edges]
              }
            }
          },
          vulnerabilities: {
            keyArgs: ['assetId', 'severity', 'status'],
            merge(existing = [], incoming = []) {
              return [...existing, ...incoming]
            }
          },
          tasks: {
            keyArgs: ['assignedTo', 'status', 'priority'],
            merge(existing = [], incoming = []) {
              return [...existing, ...incoming]
            }
          }
        }
      },
      User: {
        keyFields: ['id']
      },
      Asset: {
        keyFields: ['id']
      },
      Vulnerability: {
        keyFields: ['id']
      },
      Task: {
        keyFields: ['id']
      }
    }
  }),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all'
    },
    query: {
      fetchPolicy: 'cache-first',
      errorPolicy: 'all'
    }
  }
})

/**
 * Helper function to reset the Apollo Client cache
 */
export const resetApolloCache = async () => {
  await apolloClient.clearStore()
  await apolloClient.resetStore()
}

/**
 * Helper function to refetch all active queries
 */
export const refetchQueries = async () => {
  await apolloClient.refetchQueries({
    include: 'active'
  })
}

/**
 * Export client utilities
 */
export default {
  client: apolloClient,
  resetCache: resetApolloCache,
  refetchQueries
}