/**
 * Customer service - API calls for customer operations
 */
import api, { unwrapApiResponse } from './api';
import type {
  Customer,
  CustomerUpdate,
  CustomerListParams,
  PaginatedResponse,
  ApiResponse,
} from '@/types/openapi';

export const customerService = {
  /**
   * List customers (paginated)
   */
  async listCustomers(params?: CustomerListParams): Promise<PaginatedResponse<Customer>> {
    const response = await api.get<PaginatedResponse<Customer>>('/customers', { params });
    return response.data;
  },

  /**
   * Get customer by ID
   */
  async getCustomer(customerId: string): Promise<Customer> {
    const response = await api.get<ApiResponse<Customer>>(`/customers/${customerId}`);
    return unwrapApiResponse(response.data);
  },

  /**
   * Create new customer
   */
  async createCustomer(customer: Customer): Promise<Customer> {
    const response = await api.post<ApiResponse<Customer>>('/customers', customer);
    return unwrapApiResponse(response.data);
  },

  /**
   * Update customer (full replace)
   */
  async updateCustomer(customerId: string, customer: Customer): Promise<Customer> {
    const response = await api.put<ApiResponse<Customer>>(
      `/customers/${customerId}`,
      customer
    );
    return unwrapApiResponse(response.data);
  },

  /**
   * Partially update customer
   */
  async patchCustomer(customerId: string, updates: CustomerUpdate): Promise<Customer> {
    const response = await api.patch<ApiResponse<Customer>>(
      `/customers/${customerId}`,
      updates
    );
    return unwrapApiResponse(response.data);
  },
};
