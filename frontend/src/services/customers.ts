/**
 * Customer-related API service functions
 */

import apiClient from './api';
import type {
  Customer,
  CustomerListParams,
  PaginatedResponse,
  ApiResponse,
} from '@/types/api';

/**
 * List customers with pagination
 * GET /customers
 */
export const listCustomers = async (
  params?: CustomerListParams
): Promise<PaginatedResponse<Customer>> => {
  const response = await apiClient.get<PaginatedResponse<Customer>>('/customers', {
    params,
  });

  return response.data;
};

/**
 * Get customer details
 * GET /customers/{customerId}
 */
export const getCustomer = async (customerId: string): Promise<Customer> => {
  const response = await apiClient.get<ApiResponse<Customer>>(
    `/customers/${customerId}`
  );

  if (!response.data.data) {
    throw new Error('Customer not found');
  }

  return response.data.data;
};

/**
 * Create new customer
 * POST /customers
 */
export const createCustomer = async (customer: Customer): Promise<Customer> => {
  const response = await apiClient.post<ApiResponse<Customer>>(
    '/customers',
    customer
  );

  if (!response.data.data) {
    throw new Error('Failed to create customer');
  }

  return response.data.data;
};

/**
 * Update customer (all fields)
 * PUT /customers/{customerId}
 */
export const updateCustomer = async (
  customerId: string,
  customer: Customer
): Promise<Customer> => {
  const response = await apiClient.put<ApiResponse<Customer>>(
    `/customers/${customerId}`,
    customer
  );

  if (!response.data.data) {
    throw new Error('Failed to update customer');
  }

  return response.data.data;
};

/**
 * Partially update customer
 * PATCH /customers/{customerId}
 */
export const patchCustomer = async (
  customerId: string,
  data: Partial<Customer>
): Promise<Customer> => {
  const response = await apiClient.patch<ApiResponse<Customer>>(
    `/customers/${customerId}`,
    data
  );

  if (!response.data.data) {
    throw new Error('Failed to update customer');
  }

  return response.data.data;
};
