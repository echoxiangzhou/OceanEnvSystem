import apiClient from './apiClient';
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
 * AuthService - handles user authentication and authorization
 */
class AuthService {
  /**
   * Login with username and password
   */
  async login(credentials: LoginCredentials): Promise<ApiResponse<LoginResponse>> {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
    
    if (response.data?.token) {
      // Store token in localStorage
      localStorage.setItem('auth_token', response.data.token);
      localStorage.setItem('user_info', JSON.stringify(response.data.user));
      
      // Set token in API client
      apiClient.setAuthToken(response.data.token);
    }
    
    return response;
  }

  /**
   * Logout current user
   */
  async logout(): Promise<ApiResponse<{ message: string }>> {
    const response = await apiClient.post<{ message: string }>('/auth/logout');
    
    // Clear auth data regardless of API response
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    apiClient.setAuthToken(null);
    
    return response;
  }

  /**
   * Get current authenticated user information
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    return apiClient.get<User>('/auth/me');
  }

  /**
   * Create a new API key
   */
  async createApiKey(name: string): Promise<ApiResponse<ApiKey>> {
    return apiClient.post<ApiKey>('/auth/apikeys', { name });
  }

  /**
   * Get list of API keys
   */
  async getApiKeys(): Promise<ApiResponse<ApiKey[]>> {
    return apiClient.get<ApiKey[]>('/auth/apikeys');
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token');
  }

  /**
   * Get stored user information
   */
  getStoredUser(): User | null {
    const userJson = localStorage.getItem('user_info');
    return userJson ? JSON.parse(userJson) : null;
  }

  /**
   * Initialize auth state from localStorage
   */
  initializeAuth(): void {
    const token = localStorage.getItem('auth_token');
    if (token) {
      apiClient.setAuthToken(token);
    }
  }
}

const authService = new AuthService();
export default authService;
