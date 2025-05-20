import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { authService } from '../services';
import { ApiResponse } from '../types/api';

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: User;
}

interface ApiKey {
  id: string;
  name: string;
  key: string;
  created_at: string;
}

/**
 * Custom hook for login
 */
export const useLogin = (options?: UseMutationOptions<
  ApiResponse<LoginResponse>,
  Error,
  LoginCredentials
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<LoginResponse>,
    Error,
    LoginCredentials
  >({
    mutationFn: (credentials) => authService.login(credentials),
    onSuccess: (data) => {
      if (data.data) {
        // Update current user query
        queryClient.setQueryData(['currentUser'], { data: data.data.user });
      }
    },
    ...options
  });
};

/**
 * Custom hook for logout
 */
export const useLogout = (options?: UseMutationOptions<
  ApiResponse<{ message: string }>,
  Error,
  void
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<{ message: string }>,
    Error,
    void
  >({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      // Clear current user query
      queryClient.setQueryData(['currentUser'], null);
      // Invalidate all queries to force refetch after login
      queryClient.invalidateQueries();
    },
    ...options
  });
};

/**
 * Custom hook for fetching current user
 */
export const useCurrentUser = (options?: UseQueryOptions<ApiResponse<User>, Error>) => {
  return useQuery<ApiResponse<User>, Error>({
    queryKey: ['currentUser'],
    queryFn: () => authService.getCurrentUser(),
    // Don't fetch if user is not authenticated
    enabled: authService.isAuthenticated(),
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options
  });
};

/**
 * Custom hook for creating API keys
 */
export const useCreateApiKey = (options?: UseMutationOptions<
  ApiResponse<ApiKey>,
  Error,
  string
>) => {
  const queryClient = useQueryClient();
  
  return useMutation<
    ApiResponse<ApiKey>,
    Error,
    string
  >({
    mutationFn: (name) => authService.createApiKey(name),
    onSuccess: () => {
      // Invalidate API keys query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
    },
    ...options
  });
};

/**
 * Custom hook for fetching API keys
 */
export const useApiKeys = (options?: UseQueryOptions<ApiResponse<ApiKey[]>, Error>) => {
  return useQuery<ApiResponse<ApiKey[]>, Error>({
    queryKey: ['apiKeys'],
    queryFn: () => authService.getApiKeys(),
    // Don't fetch if user is not authenticated
    enabled: authService.isAuthenticated(),
    ...options
  });
};

/**
 * Custom hook for authentication status
 */
export const useAuth = () => {
  const currentUserQuery = useCurrentUser();

  // Initialize auth from local storage
  authService.initializeAuth();

  const isAuthenticated = authService.isAuthenticated();
  const storedUser = authService.getStoredUser();

  return {
    isAuthenticated,
    currentUser: currentUserQuery.data?.data || storedUser,
    isLoading: currentUserQuery.isLoading,
    error: currentUserQuery.error,
  };
};
