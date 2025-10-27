/**
 * Vue Composable for GraphQL Operations
 * Simplifies GraphQL usage in Vue components
 */

import { ref, computed, watch, onUnmounted } from 'vue'
import { useQuery, useMutation, useSubscription } from '@vue/apollo-composable'
import { DocumentNode } from 'graphql'
import { ApolloError } from '@apollo/client'
import { useNotification } from './useNotification'

export interface GraphQLOptions {
  fetchPolicy?: 'cache-first' | 'cache-and-network' | 'network-only' | 'cache-only'
  pollInterval?: number
  debounce?: number
  onCompleted?: (data: any) => void
  onError?: (error: ApolloError) => void
  notifyOnError?: boolean
}

/**
 * Composable for GraphQL queries
 */
export function useGraphQLQuery<TData = any, TVariables = any>(
  query: DocumentNode,
  variables?: TVariables | (() => TVariables),
  options: GraphQLOptions = {}
) {
  const { showError } = useNotification()
  const error = ref<ApolloError | null>(null)
  const data = ref<TData | null>(null)

  const {
    result,
    loading,
    error: queryError,
    refetch,
    fetchMore,
    onResult,
    onError: onQueryError
  } = useQuery<TData, TVariables>(query, variables, {
    fetchPolicy: options.fetchPolicy || 'cache-first',
    pollInterval: options.pollInterval,
    debounce: options.debounce
  })

  // Handle results
  onResult((queryResult) => {
    if (queryResult.data) {
      data.value = queryResult.data
      options.onCompleted?.(queryResult.data)
    }
  })

  // Handle errors
  onQueryError((err) => {
    error.value = err
    options.onError?.(err)

    if (options.notifyOnError !== false) {
      showError(`Query failed: ${err.message}`)
    }
  })

  return {
    data: computed(() => result.value as TData | null),
    loading,
    error,
    refetch,
    fetchMore
  }
}

/**
 * Composable for GraphQL mutations
 */
export function useGraphQLMutation<TData = any, TVariables = any>(
  mutation: DocumentNode,
  options: GraphQLOptions = {}
) {
  const { showSuccess, showError } = useNotification()

  const {
    mutate,
    loading,
    error,
    onDone,
    onError: onMutationError
  } = useMutation<TData, TVariables>(mutation, {
    fetchPolicy: options.fetchPolicy
  })

  // Handle completion
  onDone((result) => {
    if (result.data) {
      options.onCompleted?.(result.data)
    }
  })

  // Handle errors
  onMutationError((err) => {
    options.onError?.(err)

    if (options.notifyOnError !== false) {
      showError(`Mutation failed: ${err.message}`)
    }
  })

  // Enhanced mutate function with automatic notifications
  const execute = async (
    variables: TVariables,
    successMessage?: string,
    errorMessage?: string
  ): Promise<TData | null> => {
    try {
      const result = await mutate(variables)

      if (result?.data) {
        if (successMessage) {
          showSuccess(successMessage)
        }
        return result.data
      }
      return null
    } catch (err) {
      if (errorMessage) {
        showError(errorMessage)
      }
      throw err
    }
  }

  return {
    execute,
    mutate,
    loading,
    error
  }
}

/**
 * Composable for GraphQL subscriptions
 */
export function useGraphQLSubscription<TData = any, TVariables = any>(
  subscription: DocumentNode,
  variables?: TVariables | (() => TVariables),
  options: GraphQLOptions = {}
) {
  const { showError } = useNotification()
  const data = ref<TData | null>(null)
  const error = ref<ApolloError | null>(null)

  const {
    result,
    loading,
    error: subscriptionError,
    onResult,
    onError: onSubscriptionError,
    stop,
    restart
  } = useSubscription<TData, TVariables>(subscription, variables)

  // Handle results
  onResult((subscriptionResult) => {
    if (subscriptionResult.data) {
      data.value = subscriptionResult.data
      options.onCompleted?.(subscriptionResult.data)
    }
  })

  // Handle errors
  onSubscriptionError((err) => {
    error.value = err
    options.onError?.(err)

    if (options.notifyOnError !== false) {
      showError(`Subscription error: ${err.message}`)
    }
  })

  // Auto-cleanup on unmount
  onUnmounted(() => {
    stop()
  })

  return {
    data: computed(() => result.value as TData | null),
    loading,
    error,
    stop,
    restart
  }
}

/**
 * Composable for paginated GraphQL queries
 */
export function usePaginatedQuery<TData = any, TVariables = any>(
  query: DocumentNode,
  variables: TVariables | (() => TVariables),
  options: GraphQLOptions = {}
) {
  const hasNextPage = ref(false)
  const hasPreviousPage = ref(false)
  const totalCount = ref(0)
  const currentCursor = ref<string | null>(null)

  const { data, loading, error, fetchMore } = useGraphQLQuery<TData, TVariables>(
    query,
    variables,
    {
      ...options,
      onCompleted: (result) => {
        // Extract pagination info
        const pageInfo = result?.pageInfo
        if (pageInfo) {
          hasNextPage.value = pageInfo.hasNextPage
          hasPreviousPage.value = pageInfo.hasPreviousPage
          currentCursor.value = pageInfo.endCursor
        }

        // Extract total count
        if (result?.totalCount !== undefined) {
          totalCount.value = result.totalCount
        }

        options.onCompleted?.(result)
      }
    }
  )

  const loadMore = async () => {
    if (!hasNextPage.value || !currentCursor.value) return

    await fetchMore({
      variables: {
        ...((typeof variables === 'function' ? variables() : variables) as any),
        after: currentCursor.value
      }
    })
  }

  return {
    data,
    loading,
    error,
    hasNextPage,
    hasPreviousPage,
    totalCount,
    loadMore
  }
}

/**
 * Composable for optimistic updates
 */
export function useOptimisticUpdate() {
  const { client } = useApolloClient()

  const optimisticUpdate = <TData = any>(
    options: {
      mutation: DocumentNode
      variables: any
      optimisticResponse: any
      update: (cache: any, result: any) => void
    }
  ) => {
    return client.mutate({
      mutation: options.mutation,
      variables: options.variables,
      optimisticResponse: options.optimisticResponse,
      update: options.update
    })
  }

  return {
    optimisticUpdate
  }
}

/**
 * Composable for real-time data with subscriptions
 */
export function useRealtimeData<TData = any, TVariables = any>(
  query: DocumentNode,
  subscription: DocumentNode,
  variables?: TVariables | (() => TVariables),
  options: GraphQLOptions = {}
) {
  // Initial query
  const queryResult = useGraphQLQuery<TData, TVariables>(query, variables, options)

  // Real-time updates
  const subscriptionResult = useGraphQLSubscription<TData, TVariables>(
    subscription,
    variables,
    {
      ...options,
      onCompleted: (data) => {
        // Merge subscription data with query data
        if (queryResult.data.value) {
          Object.assign(queryResult.data.value, data)
        }
        options.onCompleted?.(data)
      }
    }
  )

  return {
    data: queryResult.data,
    loading: computed(() => queryResult.loading.value || subscriptionResult.loading.value),
    error: computed(() => queryResult.error.value || subscriptionResult.error.value),
    refetch: queryResult.refetch,
    stopSubscription: subscriptionResult.stop,
    restartSubscription: subscriptionResult.restart
  }
}

/**
 * Export all composables
 */
export default {
  useGraphQLQuery,
  useGraphQLMutation,
  useGraphQLSubscription,
  usePaginatedQuery,
  useOptimisticUpdate,
  useRealtimeData
}