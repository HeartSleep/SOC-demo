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
 * Helpers for merging paginated and list data
 */
type MergeOptions = {
  args?: Record<string, any>
}

const hasCursorArgs = (args?: Record<string, any>) => {
  if (!args) return false
  return typeof args.after !== 'undefined' || typeof args.before !== 'undefined'
}

const shouldResetConnection = (args?: Record<string, any>) => {
  if (!args) return true
  if (args.reset === true) return true
  return !hasCursorArgs(args)
}

const dedupeEdges = (edges: any[] = []) => {
  const seen = new Map<string, number>()
  const result: any[] = []

  edges.forEach((edge) => {
    if (!edge) return

    let identity: string

    if (edge?.node?.id) {
      identity = edge.node.id
    } else if (edge?.node?._id) {
      identity = edge.node._id
    } else if (edge?.cursor) {
      identity = edge.cursor
    } else {
      try {
        identity = JSON.stringify(edge)
      } catch {
        identity = String(edge)
      }
    }

    if (seen.has(identity)) {
      const index = seen.get(identity)!
      const existingEdge = result[index]

      const mergedNode =
        typeof existingEdge?.node === 'object' &&
        existingEdge?.node !== null &&
        typeof edge?.node === 'object' &&
        edge?.node !== null
          ? { ...existingEdge.node, ...edge.node }
          : edge?.node ?? existingEdge?.node

      result[index] = {
        ...existingEdge,
        ...edge,
        node: mergedNode
      }
    } else {
      seen.set(identity, result.length)
      result.push({
        ...edge,
        node:
          typeof edge?.node === 'object' && edge?.node !== null
            ? { ...edge.node }
            : edge?.node
      })
    }
  })

  return result
}

const mergeConnectionField = (
  existing: any = { edges: [] },
  incoming: any,
  options: MergeOptions = {}
) => {
  if (!incoming) {
    return existing ?? { edges: [] }
  }

  const args = options.args
  const existingEdges = existing?.edges ?? []
  const incomingEdges = incoming?.edges ?? []

  let mergedEdges: any[]

  if (shouldResetConnection(args)) {
    mergedEdges = incomingEdges
  } else if (args?.before !== undefined && args.before !== null) {
    mergedEdges = [...incomingEdges, ...existingEdges]
  } else {
    mergedEdges = [...existingEdges, ...incomingEdges]
  }

  const edges = dedupeEdges(mergedEdges)

  return {
    ...existing,
    ...incoming,
    edges,
    pageInfo: {
      ...(existing?.pageInfo ?? {}),
      ...(incoming?.pageInfo ?? {})
    },
    totalCount:
      typeof incoming?.totalCount === 'number'
        ? incoming.totalCount
        : existing?.totalCount
  }
}

const dedupeItems = (items: any[] = []) => {
  const seen = new Map<string, number>()
  const result: any[] = []

  items.forEach((item) => {
    if (item === undefined || item === null) {
      return
    }

    let identity: string

    if (typeof item === 'object' && item !== null) {
      if ('id' in item && item.id) {
        identity = item.id
      } else if ('__ref' in item && (item as any).__ref) {
        identity = (item as any).__ref
      } else {
        try {
          identity = JSON.stringify(item)
        } catch {
          identity = String(item)
        }
      }
    } else {
      identity = String(item)
    }

    if (seen.has(identity)) {
      const index = seen.get(identity)!
      const existingItem = result[index]

      if (
        typeof existingItem === 'object' &&
        existingItem !== null &&
        typeof item === 'object' &&
        item !== null
      ) {
        result[index] = {
          ...existingItem,
          ...item
        }
      } else {
        result[index] = item
      }
    } else {
      seen.set(identity, result.length)
      if (typeof item === 'object' && item !== null) {
        result.push({ ...item })
      } else {
        result.push(item)
      }
    }
  })

  return result
}

const mergeArrayField = (
  existing: any[] = [],
  incoming: any[] | undefined,
  options: MergeOptions = {}
) => {
  if (!incoming || incoming.length === 0) {
    return existing
  }

  const args = options.args
  const shouldReset =
    !args ||
    args.reset === true ||
    (typeof args.offset === 'number' && args.offset === 0) ||
    (typeof args.skip === 'number' && args.skip === 0)

  const combined = shouldReset ? incoming : [...existing, ...incoming]

  return dedupeItems(combined)
}

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
          // Paginated connection fields with proper deduplication
          users: {
            keyArgs: ['role', 'isActive'],
            merge(existing, incoming, { args }) {
              return mergeConnectionField(existing, incoming, { args })
            }
          },
          assets: {
            keyArgs: ['assetType', 'criticality', 'tags'],
            merge(existing, incoming, { args }) {
              return mergeConnectionField(existing, incoming, { args })
            }
          },
          // Array fields with proper deduplication
          vulnerabilities: {
            keyArgs: ['assetId', 'severity', 'status'],
            merge(existing, incoming, { args }) {
              return mergeArrayField(existing, incoming, { args })
            }
          },
          tasks: {
            keyArgs: ['assignedTo', 'status', 'priority'],
            merge(existing, incoming, { args }) {
              return mergeArrayField(existing, incoming, { args })
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