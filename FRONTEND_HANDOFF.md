# 🚀 Frontend Developer API Handoff & Implementation Guide

> **Digital Product Selling System Backend (FastAPI)**  
> **API Version**: `v1` | **OpenAPI Spec**: `3.1.0` | **Total Endpoints**: `90`  
> **Companion File**: [`Digital_Product_Selling_System.postman_collection.json`](./Digital_Product_Selling_System.postman_collection.json)

---

## 📌 Document Purpose & AI Pair-Programming Directive

This handoff document is engineered as a **self-contained blueprint** for frontend developers and AI coding assistants (ChatGPT, Claude, Gemini, Cursor, Copilot). 

When building or extending the customer storefront or admin management panel:
1. **Attach this file** (`FRONTEND_HANDOFF.md`) and the Postman collection (`Digital_Product_Selling_System.postman_collection.json`) to your AI context.
2. The AI will have **100% complete knowledge** of all 90 endpoints, TypeScript interfaces, envelope shapes, pagination models, authentication cycles, dynamic field rendering rules, checkout flows, and error handling protocols.

---

## 📑 Table of Contents

1. [Quick Start & Local Environment](#1-quick-start--local-environment)
2. [Global Architecture & API Conventions](#2-global-architecture--api-conventions)
   - [Standard Success Response Envelope](#standard-success-response-envelope)
   - [Standard Error Response Envelope](#standard-error-response-envelope)
   - [Pagination Protocol](#pagination-protocol)
   - [Media & Static Asset URLs](#media--static-asset-urls)
3. [Authentication & Authorization Lifecycle](#3-authentication--authorization-lifecycle)
   - [JWT Bearer Token Flow](#jwt-bearer-token-flow)
   - [Customer vs. Admin Auth Gateways](#customer-vs-admin-auth-gateways)
   - [Automatic Token Refresh Cycle](#automatic-token-refresh-cycle)
   - [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
4. [Ready-to-Use Frontend Infrastructure](#4-ready-to-use-frontend-infrastructure)
   - [TypeScript Core Types & Models](#typescript-core-types--models)
   - [Configured Axios Client with Auto-Refresh Interceptors](#configured-axios-client-with-auto-refresh-interceptors)
5. [Core Domain Workflows & Business Rules](#5-core-domain-workflows--business-rules)
   - [Workflow A: Dynamic Customer Input Engine](#workflow-a-dynamic-customer-input-engine)
   - [Workflow B: Product & Multi-Tier Package Selection](#workflow-b-product--multi-tier-package-selection)
   - [Workflow C: Checkout, Coupon Validation & Order Creation](#workflow-c-checkout-coupon-validation--order-creation)
   - [Workflow D: Payment Settlement (Manual TrxID vs. Wallet Balance)](#workflow-d-payment-settlement-manual-trxid-vs-wallet-balance)
   - [Workflow E: Customer Wallet & Top-Up Approvals](#workflow-e-customer-wallet--top-up-approvals)
   - [Workflow F: Gamified Lottery & Lucky Spin Engine](#workflow-f-gamified-lottery--lucky-spin-engine)
   - [Workflow G: Marketing CMS (Banners, Popups & Site Settings)](#workflow-g-marketing-cms-banners-popups--site-settings)
   - [Workflow H: Admin Management & Analytical Dashboard](#workflow-h-admin-management--analytical-dashboard)
6. [Complete 16-Module API Catalog](#6-complete-16-module-api-catalog)
7. [AI Prompting Recipes & Frontend Code Generators](#7-ai-prompting-recipes--frontend-code-generators)
8. [Postman Workspace Navigation & Testing Tips](#8-postman-workspace-navigation--testing-tips)

---

## 1. Quick Start & Local Environment

### Server Addresses & Ports
| Service | URL | Notes |
| :--- | :--- | :--- |
| **Backend API Base URL** | `http://localhost:8000` | Local development host |
| **API Route Prefix** | `http://localhost:8000/api/v1` | All business endpoints live here |
| **Interactive Swagger UI**| `http://localhost:8000/docs` | Test endpoints in browser |
| **ReDoc Documentation** | `http://localhost:8000/redoc` | Clean documentation view |
| **OpenAPI Schema JSON** | `http://localhost:8000/openapi.json`| Raw OpenAPI 3.1 JSON |
| **Static Uploads Base** | `http://localhost:8000/media/` | Uploaded images, icons & QR codes |

### Frontend `.env` Example
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_MEDIA_BASE_URL=http://localhost:8000
```

### Pre-Seeded Test Accounts
The database comes pre-seeded with test accounts ready for instant development:

| Role | Email | Password | Allowed Access |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@example.com` | `admin123` | Full access to `/api/v1/admin/*`, verification queues, CMS, settings |
| **Customer** | `user@example.com` | `user123` | Customer checkout, orders, wallet, topups, lotteries |

---

## 2. Global Architecture & API Conventions

### Standard Success Response Envelope
Every single 2xx response returned by the backend is wrapped in the `StandardResponse<T>` schema:

```json
{
  "success": true,
  "status_code": 200,
  "message": "Operation successful",
  "data": { ... }
}
```

- When writing frontend service layers or React Query hooks, **always extract `response.data.data`** as the actual payload.

### Standard Error Response Envelope
Every 4xx or 5xx error returns a standardized JSON structure with correlation tracing:

```json
{
  "success": false,
  "status_code": 400,
  "message": "Dynamic field 'player_id' is required for this product.",
  "errors": null,
  "request_id": "req-9b88e1a2-3847-4cfb-b8aa-8d2a3f789012"
}
```

- **Pydantic 422 Validation Errors**: `errors` will contain an array of parameter path errors (`[{"loc": ["body", "quantity"], "msg": "Input should be greater than or equal to 1"}]`).
- **HTTP 429 Rate Limited**: Critical auth routes enforce SlowAPI limits (`10/min` or `15/min`). Displays retry message.
- **Request Tracing**: `request_id` matches the backend log trace ID and `X-Request-ID` response header.

### Pagination Protocol
All paginated list endpoints (`/products`, `/admin/orders`, `/admin/users`, `/wallet/transactions`, etc.) follow this universal query and response specification:

#### Query Parameters
- `page`: Integer $\ge 1$ (Default: `1`)
- `size`: Integer $\ge 1$ (Default: `10`)
- Optional filters: `search`, `status`, `category_id`, etc.

#### Paginated Response Envelope
```json
{
  "success": true,
  "status_code": 200,
  "message": "Records retrieved successfully",
  "data": {
    "items": [ ... ],
    "pagination": {
      "total": 54,
      "current_page": 1,
      "last_page": 6,
      "next_page": 2,
      "prev_page": null,
      "from": 1,
      "to": 10
    }
  }
}
```

> **TypeScript Tip**: Note that `from` and `to` are formatted with `from` / `to` in JSON (mapped in Pydantic via aliases).

### Media & Static Asset URLs
When images or banners are uploaded or returned:
- The API returns **relative URLs**, e.g.: `"/media/products/2c89f81a-bb6f-4b45.png"`.
- To render in the frontend:
  ```ts
  const getImageUrl = (path?: string | null) => {
    if (!path) return "/placeholder.png";
    if (path.startsWith("http://") || path.startsWith("https://")) return path;
    return `${import.meta.env.VITE_MEDIA_BASE_URL}${path}`;
  };
  ```

---

## 3. Authentication & Authorization Lifecycle

```text
               ┌───────────────────────┐
               │    Customer Login     │
               │  POST /auth/google    │
               │ (Google OAuth2 Token) │
               └──────────┬────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│               JWT Tokens Generated                     │
│  - access_token (60 min expiry, in Auth header)       │
│  - refresh_token (7 day expiry, stored securely)       │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ├─────────────────────────────────────────┐
                          ▼                                         ▼
            ┌───────────────────────────┐             ┌───────────────────────────┐
            │   Normal API Requests     │             │    Token Expires (401)    │
            │ Authorization: Bearer ... │             │  POST /auth/refresh       │
            └───────────────────────────┘             │  New access_token granted │
                                                      └───────────────────────────┘
```

### JWT Bearer Token Flow
- All protected endpoints require the HTTP Authorization header:
  ```http
  Authorization: Bearer <access_token>
  ```
- Access tokens expire after **60 minutes** (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- Refresh tokens expire after **7 days** (`REFRESH_TOKEN_EXPIRE_DAYS`).

### Customer vs. Admin Auth Gateways

#### 1. Customer Login (Google OAuth2 ID Token)
- **Endpoint**: `POST /api/v1/auth/google`
- **Payload**:
  ```json
  {
    "id_token": "eyJhbGciOiJSUzI1NiIs...",
    "phone": "+8801700000000"
  }
  ```
- Automatically registers a new customer if they don't exist yet, creates their primary wallet ledger, and returns the tokens + user profile.

#### 2. Admin Login (Credentials)
- **Endpoint**: `POST /api/v1/auth/admin/login`
- **Payload**:
  ```json
  {
    "email": "admin@example.com",
    "password": "adminpassword123"
  }
  ```
- Validates administrative credentials, checks `role == 'admin'`, and returns tokens.

#### 3. Token Refresh
- **Endpoint**: `POST /api/v1/auth/refresh`
- **Payload**:
  ```json
  {
    "refresh_token": "<stored_refresh_token>"
  }
  ```
- **Returns**: `{ "access_token": "...", "token_type": "bearer" }`.

### Automatic Token Refresh Cycle
A complete Axios interceptor is provided below in [Section 4](#configured-axios-client-with-auto-refresh-interceptors) that seamlessly queues failed requests, refreshes the token via `/auth/refresh`, and retries without user disruption.

### Role-Based Access Control (RBAC)
- `customer`: Can view catalog, initiate checkout, view personal orders, submit payment TrxIDs, check wallet balance, request top-ups, spin lotteries, and update personal profile.
- `admin`: Can access everything, plus all routes under `/api/v1/admin/*` (dashboard metrics, customer user toggling, category reordering, dynamic field builder, coupon management, order fulfillment, manual payment approvals, wallet adjustments, and CMS settings).

---

## 4. Ready-to-Use Frontend Infrastructure

### TypeScript Core Types & Models

Save this file as `src/types/api.ts`:

```typescript
// ==========================================
// 1. API Envelope & Pagination Interfaces
// ==========================================

export interface StandardResponse<T> {
  success: boolean;
  status_code: number;
  message: string;
  data: T;
}

export interface ErrorResponse {
  success: false;
  status_code: number;
  message: string;
  errors?: Array<{ loc: string[]; msg: string; type: string }> | null;
  request_id?: string;
}

export interface PaginationMeta {
  total: number;
  current_page: number;
  last_page: number;
  next_page: number | null;
  prev_page: number | null;
  from: number;
  to: number;
}

export interface PaginatedData<T> {
  items: T[];
  pagination: PaginationMeta;
}

export interface PaginationParams {
  page?: number;
  size?: number;
  search?: string;
}

// ==========================================
// 2. User & Authentication Models
// ==========================================

export type UserRole = 'customer' | 'admin';

export interface User {
  id: number;
  google_id?: string | null;
  email: string;
  username: string;
  name?: string | null;
  image?: string | null;
  phone?: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ==========================================
// 3. Catalog & Dynamic Input Fields
// ==========================================

export interface Category {
  id: number;
  name: string;
  slug: string;
  icon?: string | null;
  sort_order: number;
  is_active: boolean;
  created_at: string;
}

export type InputFieldType = 'text' | 'email' | 'number' | 'url' | 'textarea';

export interface ProductInputField {
  id: number;
  product_id: number;
  name: string;
  label: string;
  type: InputFieldType;
  placeholder?: string | null;
  is_required: boolean;
  sort_order: number;
  created_at?: string;
}

export interface Package {
  id: number;
  product_id: number;
  name: string;
  price: number;
  compare_price?: number | null;
  duration?: string | null;
  description?: string | null;
  is_active: boolean;
  sort_order: number;
  created_at?: string;
}

export interface ProductCard {
  id: number;
  name: string;
  slug: string;
  image?: string | null;
  category_id?: number | null;
  category_name?: string | null;
  starting_price?: number | null;
  is_active: boolean;
  sort_order: number;
}

export interface ProductDetail extends ProductCard {
  description?: string | null;
  instructions?: string | null;
  packages: Package[];
  input_fields: ProductInputField[];
}

// ==========================================
// 4. Coupons & Discounts
// ==========================================

export type CouponType = 'FIXED' | 'PERCENTAGE';

export interface Coupon {
  id: number;
  code: string;
  type: CouponType;
  value: number;
  max_discount?: number | null;
  minimum_order_amount: number;
  usage_limit?: number | null;
  used_count: number;
  per_user_limit: number;
  starts_at?: string | null;
  expires_at?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface CouponValidateRequest {
  code: string;
  package_id: number;
  quantity?: number;
}

export interface CouponValidateResponse {
  valid: boolean;
  code: string;
  discount_type: CouponType;
  discount_amount: number;
  message: string;
}

// ==========================================
// 5. Orders & Checkout
// ==========================================

export type OrderStatus =
  | 'PENDING'
  | 'PAYMENT_PENDING'
  | 'PAID'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'FAILED'
  | 'REFUNDED';

export interface OrderItem {
  id: number;
  product_id: number;
  package_id: number;
  product_name: string;
  package_name: string;
  unit_price: number;
  quantity: number;
  total_price: number;
  input_values?: Record<string, any> | null;
}

export interface Order {
  id: number;
  user_id: number;
  order_number: string;
  subtotal: number;
  discount: number;
  total_amount: number;
  coupon_id?: number | null;
  status: OrderStatus;
  customer_note?: string | null;
  admin_note?: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface CheckoutPreviewRequest {
  package_id: number;
  quantity?: number;
  coupon_code?: string | null;
  input_values?: Record<string, any> | null;
}

export interface CheckoutPreviewResponse {
  package_id: number;
  package_name: string;
  product_name: string;
  unit_price: number;
  quantity: number;
  subtotal: number;
  discount: number;
  total: number;
  coupon_applied?: string | null;
  input_valid: boolean;
  validation_errors?: string[] | null;
}

export interface DirectOrderCreate {
  package_id: number;
  quantity?: number;
  coupon_code?: string | null;
  input_values: Record<string, any>;
  customer_note?: string | null;
  payment_method_id?: number | null;
}

// ==========================================
// 6. Payment Methods & Payments
// ==========================================

export interface PaymentMethod {
  id: number;
  name: string;
  account_number: string;
  instructions?: string | null;
  logo?: string | null;
  is_active: boolean;
  sort_order: number;
}

export type PaymentStatus =
  | 'PENDING'
  | 'VERIFYING'
  | 'VERIFIED'
  | 'REJECTED'
  | 'EXPIRED';

export interface Payment {
  id: number;
  order_id: number;
  user_id: number;
  payment_method_id: number;
  amount: number;
  transaction_id: string;
  sender_number: string;
  status: PaymentStatus;
  verified_by?: number | null;
  verified_at?: string | null;
  admin_note?: string | null;
  created_at: string;
}

export interface PaymentSubmitRequest {
  order_id: number;
  payment_method_id: number;
  transaction_id: string;
  sender_number: string;
}

// ==========================================
// 7. Wallet & Top-Ups
// ==========================================

export interface Wallet {
  id: number;
  user_id: number;
  balance: number;
  updated_at: string;
}

export type WalletTxType = 'TOPUP' | 'PURCHASE' | 'REFUND' | 'ADJUSTMENT' | 'BONUS';

export interface WalletTransaction {
  id: number;
  wallet_id: number;
  type: WalletTxType;
  amount: number;
  balance_before: number;
  balance_after: number;
  reference_type?: string | null;
  reference_id?: string | null;
  description?: string | null;
  created_at: string;
}

export type TopUpStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface TopUp {
  id: number;
  user_id: number;
  payment_method_id: number;
  amount: number;
  transaction_id: string;
  sender_number: string;
  status: TopUpStatus;
  admin_note?: string | null;
  verified_by?: number | null;
  verified_at?: string | null;
  created_at: string;
}

export interface TopUpCreateRequest {
  payment_method_id: number;
  amount: number;
  transaction_id: string;
  sender_number: string;
}

// ==========================================
// 8. Lottery & Lucky Spin
// ==========================================

export type PrizeDiscountType = 'PERCENTAGE' | 'FIXED' | 'FREE';

export interface LotteryPrize {
  id: number;
  lottery_id: number;
  product_id?: number | null;
  package_id?: number | null;
  discount_type: PrizeDiscountType;
  discount_value: number;
  probability: number;
  quantity: number;
  created_at: string;
}

export interface Lottery {
  id: number;
  name: string;
  description?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  is_active: boolean;
  prizes: LotteryPrize[];
  created_at: string;
}

export interface LotteryEligibility {
  eligible: boolean;
  remaining_attempts: number;
  message: string;
}

export interface LotterySpinResult {
  success: boolean;
  won: boolean;
  message: string;
  prize?: LotteryPrize | null;
}

export interface LotteryEntry {
  id: number;
  lottery_id: number;
  user_id: number;
  lottery_prize_id?: number | null;
  created_at: string;
  prize?: LotteryPrize | null;
}

// ==========================================
// 9. Marketing (Banners & Popups) & Settings
// ==========================================

export interface Banner {
  id: number;
  image: string;
  mobile_image?: string | null;
  title?: string | null;
  description?: string | null;
  button_text?: string | null;
  button_url?: string | null;
  sort_order: number;
  is_active: boolean;
}

export type PopupDisplayType = 'ON_FIRST_VISIT' | 'ONCE_PER_USER' | 'AFTER_X_SECONDS';

export interface Popup {
  id: number;
  title: string;
  content?: string | null;
  image?: string | null;
  button_text?: string | null;
  button_url?: string | null;
  display_type: PopupDisplayType;
  starts_at?: string | null;
  ends_at?: string | null;
  is_active: boolean;
}

export interface SiteSetting {
  id: number;
  site_name: string;
  site_title: string;
  logo?: string | null;
  favicon?: string | null;
  telegram_url?: string | null;
  facebook_url?: string | null;
  support_phone?: string | null;
  support_email?: string | null;
}

export interface DashboardSummary {
  today_orders: number;
  today_sales: number;
  pending_payments: number;
  pending_orders: number;
  total_users: number;
  pending_topups: number;
}
```

---

### Configured Axios Client with Auto-Refresh Interceptors

Save this file as `src/api/client.ts`:

```typescript
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ErrorResponse, StandardResponse } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 20000,
});

// Helper functions for auth token persistence
export const getAccessToken = () => localStorage.getItem('access_token');
export const getRefreshToken = () => localStorage.getItem('refresh_token');
export const setTokens = (access: string, refresh?: string) => {
  localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
};
export const clearAuth = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_profile');
};

// 1. Request Interceptor: Attach Bearer JWT
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 2. Response Interceptor: Queue-Based 401 Auto-Refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If 401 and not already retried
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Exclude auth login endpoints from triggering refresh
      if (
        originalRequest.url?.includes('/auth/admin/login') ||
        originalRequest.url?.includes('/auth/google') ||
        originalRequest.url?.includes('/auth/refresh')
      ) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearAuth();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const response = await axios.post<StandardResponse<{ access_token: string }>>(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const newAccessToken = response.data.data.access_token;
        setTokens(newAccessToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }

        processQueue(null, newAccessToken);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        clearAuth();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

---

## 5. Core Domain Workflows & Business Rules

### Workflow A: Dynamic Customer Input Engine

Digital goods like **Free Fire Diamonds** require a `Player ID`, **PUBG Mobile** requires `Player ID (UID)` + `Character Name`, and **Netflix** requires `Customer Email`. 

#### Backend Mechanics
1. Each product defines zero or more dynamic input fields stored in `product_input_fields`.
2. When loading product details (`GET /api/v1/products/{slug}`), the `input_fields` array is returned directly.
3. Every input field contains:
   - `name`: Technical key (`"player_id"`, `"zone_id"`, etc.)
   - `label`: UI label (`"Player ID (UID)"`)
   - `type`: Input type (`"text"`, `"email"`, `"number"`, `"url"`, `"textarea"`)
   - `placeholder`: Suggested example value
   - `is_required`: Boolean flag
   - `sort_order`: Display sequence

#### Frontend Form Handling
1. Generate form controls dynamically based on `product.input_fields`.
2. Store values in an object dictionary:
   ```json
   {
     "player_id": "1829384920",
     "zone_id": "9021"
   }
   ```
3. Pass this object directly as `input_values` when requesting checkout preview (`POST /api/v1/checkout/preview`) or creating an order (`POST /api/v1/orders`).
4. The backend validates required fields and regex patterns at runtime. If invalid, `POST /checkout/preview` returns `input_valid: false` with `validation_errors: ["Field 'player_id' is required"]`.

---

### Workflow B: Product & Multi-Tier Package Selection

1. **Landing Page Showcase (All Categories & Products)**: 
   - `GET /api/v1/special-products`
   - Returns all active categories with their nested products in a single call (100% compliant with legacy/BoostGhor landing contract).
   - Companion documentation: See [`SPECIAL_PRODUCTS_HANDOFF.md`](./SPECIAL_PRODUCTS_HANDOFF.md) for full TypeScript models and React landing section code.
2. **Category Filter**: `GET /api/v1/products?category_id=1&page=1&size=12`
3. **Product Page**: `GET /api/v1/products/{slug}` returns packages and dynamic fields together.
4. **Packages**: Each package represents a purchase tier (e.g. `115 Diamonds - ৳85`, `610 Diamonds - ৳430`).
   - `price`: Actual sale price.
   - `compare_price`: Strike-through original price (e.g., `৳95`). Calculate discount percentage:
     $$\text{Discount \%} = \frac{\text{compare\_price} - \text{price}}{\text{compare\_price}} \times 100$$
   - `is_active`: Only allow selection if `true`.

---

### Workflow C: Checkout, Coupon Validation & Order Creation

```text
Select Package ──► Fill Dynamic Inputs ──► Apply Coupon Code
                          │
                          ▼
            POST /api/v1/checkout/preview
   (Returns Subtotal, Discount, Total, Input Validations)
                          │
                          ▼
               POST /api/v1/orders
   (Creates Order in PAYMENT_PENDING state, returns order_number)
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
   Option 1: Manual Gateway    Option 2: Wallet Balance
   POST /payments/submit       POST /orders/{order_number}/pay-with-wallet
```

#### Step 1: Real-Time Preview (`POST /api/v1/checkout/preview`)
- Call preview whenever package, quantity, or coupon code changes.
- **Request Body**:
  ```json
  {
    "package_id": 1,
    "quantity": 1,
    "coupon_code": "DISCOUNT20",
    "input_values": { "player_id": "1829384920" }
  }
  ```
- **Response**: Returns recalculated `subtotal`, `discount`, `total`, and `input_valid`.

#### Step 2: Create Order (`POST /api/v1/orders`)
- **Request Body**:
  ```json
  {
    "package_id": 1,
    "quantity": 1,
    "coupon_code": "DISCOUNT20",
    "input_values": { "player_id": "1829384920" },
    "customer_note": "Please deliver fast",
    "payment_method_id": 1
  }
  ```
- **Response**: Returns created `Order` object with `order_number` (e.g., `"ORD-20261001-A9F2"`), status `"PAYMENT_PENDING"`.

---

### Workflow D: Payment Settlement (Manual TrxID vs. Wallet Balance)

Once the order is created, the customer completes settlement through one of two methods:

#### Option A: Manual Payment Gateway (bKash / Nagad / Rocket)
1. Customer views active payment methods (`GET /api/v1/payment-methods`).
2. Each method displays:
   - `name`: `"bKash Personal"`
   - `account_number`: `"01700112233"`
   - `instructions`: `"Send Money to this personal bKash number and enter TrxID below."`
   - `logo`: QR Code / Gateway image URL
3. Customer performs "Send Money" on their mobile banking app.
4. Customer submits transaction details:
   - **Endpoint**: `POST /api/v1/payments/submit`
   - **Body**:
     ```json
     {
       "order_id": 12,
       "payment_method_id": 1,
       "transaction_id": "9K48X78L9",
       "sender_number": "+8801711223344"
     }
     ```
5. Payment status enters `"VERIFYING"`.
6. Order status remains `"PAYMENT_PENDING"`.
7. Once admin clicks **Verify** (`POST /admin/payments/{id}/verify`) or automated Android SMS webhook verifies it:
   - Payment status $\rightarrow$ `"VERIFIED"`
   - Order status $\rightarrow$ `"PAID"`

#### Option B: 1-Click Pay with Wallet Balance
- **Endpoint**: `POST /api/v1/orders/{order_number}/pay-with-wallet`
- Deducts order total atomically from customer's stored wallet balance.
- If balance is insufficient, returns 400 Bad Request (`"Insufficient wallet balance"`).
- On success:
  - Wallet balance deducted, ledger transaction created (`type: "PURCHASE"`).
  - Order immediately transitions to `"PAID"`.

---

### Workflow E: Customer Wallet & Top-Up Approvals

Customers can keep pre-funded wallet credits to make instant 1-click checkouts:

1. **View Balance**: `GET /api/v1/wallet/me` $\rightarrow$ `{ balance: 540.00 }`.
2. **Request Top-Up**:
   - Customer sends money to admin's bKash/Nagad number.
   - Submits `POST /api/v1/wallet/topup`:
     ```json
     {
       "payment_method_id": 1,
       "amount": 500.0,
       "transaction_id": "TRX_TOPUP_8899",
       "sender_number": "+8801700112233"
     }
     ```
   - Request enters `"PENDING"`.
3. **Admin Reviews & Approves**:
   - Admin views `GET /api/v1/admin/topups?status=PENDING`.
   - Admin clicks Approve: `POST /api/v1/admin/topups/{topup_id}/approve`.
   - Customer's wallet is atomically credited by ৳500 with a `"TOPUP"` ledger entry.
4. **Transaction Audit Ledger**:
   - `GET /api/v1/wallet/transactions` provides chronological history of all credits and debits (`TOPUP`, `PURCHASE`, `REFUND`, `ADJUSTMENT`).

---

### Workflow F: Gamified Lottery & Lucky Spin Engine

A promotional prize wheel engine for customer retention:

1. **Check Campaign**: `GET /api/v1/lottery/active` returns active lottery details and available prizes (discounts, free diamonds, gift vouchers).
2. **Check Eligibility**:
   - `GET /api/v1/lottery/my-eligibility`
   - Returns `{ eligible: true, remaining_attempts: 1, message: "You have 1 spin available!" }`.
3. **Trigger Spin Animation & Submit**:
   - Frontend starts the wheel spin animation.
   - Calls `POST /api/v1/lottery/{lottery_id}/spin`.
   - Backend calculates verifiable random prize based on prize probabilities and remaining quantities.
   - Response:
     ```json
     {
       "success": true,
       "won": true,
       "message": "Congratulations! You won 500 Diamonds!",
       "prize": {
         "id": 3,
         "discount_type": "FREE",
         "discount_value": 500,
         "probability": 0.05
       }
     }
     ```
   - Animate the wheel stopping at the corresponding prize segment!
4. **History**: `GET /api/v1/lottery/my-history` returns all past customer spin records.

---

### Workflow G: Marketing CMS (Banners, Popups & Site Settings)

#### 1. Hero Carousel Banners (`GET /api/v1/banners`)
- Returns active promotional banners ordered by `sort_order`.
- Contains `image`, `mobile_image`, `title`, `description`, `button_text`, and `button_url`.

#### 2. Announcement Popup Modal (`GET /api/v1/popups/active`)
- Returns active modal (or `null` if none active).
- `display_type`:
  - `"ON_FIRST_VISIT"`: Show once per browser session (check `sessionStorage`).
  - `"ONCE_PER_USER"`: Show once ever per user/browser (store popup ID in `localStorage`).
  - `"AFTER_X_SECONDS"`: Delay display by 5-10 seconds after page load.

#### 3. Global Site Settings (`GET /api/v1/settings`)
- Brand name, logos, Telegram link, WhatsApp support, phone number, and maintenance alerts.

---

### Workflow H: Admin Management & Analytical Dashboard

The admin panel consumes the following dedicated operational routes:

1. **Analytics Summary (`GET /api/v1/admin/dashboard/summary`)**:
   - Today's Sales Volume (`today_sales`)
   - Today's Order Count (`today_orders`)
   - Pending Payments Queue Count (`pending_payments`)
   - Pending Orders Queue Count (`pending_orders`)
   - Total Registered Users (`total_users`)
   - Pending Wallet Top-Ups (`pending_topups`)
2. **Live Feed (`GET /api/v1/admin/dashboard/recent-activity`)**:
   - Real-time streams of recent order placements and incoming payment verification logs.
3. **Category Drag-and-Drop Reordering**:
   - `PATCH /api/v1/admin/categories/{category_id}/reorder` with `{ "new_order": 2 }`.
4. **Order Fulfillment Workflow**:
   - Update status: `PATCH /api/v1/admin/orders/{order_id}/status` with `{ "status": "COMPLETED" }`.
   - Update internal delivery notes: `PATCH /api/v1/admin/orders/{order_id}/note` with `{ "admin_note": "Diamonds sent to UID 1829384920" }`.

---

## 6. Complete 16-Module API Catalog

Every endpoint in the Postman collection is detailed below:

### 01. Authentication & Profile
| Method | Endpoint | Auth | Purpose | Key Body / Query |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/admin/login` | Public | Admin credential login | `{ email, password }` |
| `POST` | `/api/v1/auth/google` | Public | Customer Google OAuth2 login | `{ id_token, phone? }` |
| `POST` | `/api/v1/auth/refresh` | Public | Refresh expired access token | `{ refresh_token }` |
| `GET` | `/api/v1/auth/me` | Customer / Admin | Get current authenticated user profile | None |
| `PATCH`| `/api/v1/auth/me` | Customer / Admin | Update name, username, phone, image | `{ name?, username?, phone?, image? }` |

### 02. Admin - Dashboard
| Method | Endpoint | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/dashboard/summary` | Admin | KPI cards (today's sales, pending payments, orders) |
| `GET` | `/api/v1/admin/dashboard/recent-activity` | Admin | Chronological recent orders and payment activity stream |

### 03. Admin - User Management
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/users` | Admin | List users with pagination and search | `page`, `size`, `search`, `is_active` |
| `GET` | `/api/v1/admin/users/{user_id}` | Admin | Get single user full profile and orders | Path: `user_id` |
| `PATCH`| `/api/v1/admin/users/{user_id}/status` | Admin | Activate or suspend user account | Body: `{ is_active: boolean }` |

### 04. Categories
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/categories` | Public | Browse active categories | None |
| `GET` | `/api/v1/categories/{slug}` | Public | Get single category by slug | Path: `slug` |
| `GET` | `/api/v1/admin/categories` | Admin | List all categories (active & inactive) | None |
| `POST` | `/api/v1/admin/categories` | Admin | Create category | Body: `{ name, slug, icon?, sort_order?, is_active? }` |
| `PUT` | `/api/v1/admin/categories/{id}` | Admin | Update category | Path: `category_id`, Body: Category update fields |
| `DELETE`| `/api/v1/admin/categories/{id}` | Admin | Delete category (soft delete) | Path: `category_id` |
| `PATCH`| `/api/v1/admin/categories/{id}/reorder` | Admin | Change category display sequence | Body: `{ new_order: number }` |

### 05. Products & Dynamic Fields
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/products` | Public | Catalog list with filters & pagination | Query: `category_id`, `search`, `page`, `size` |
| `GET` | `/api/v1/products/{slug}` | Public | Product detail with packages & fields | Path: `slug` |
| `GET` | `/api/v1/products/{id}/fields` | Public | Get required customer input fields | Path: `product_id` |
| `GET` | `/api/v1/admin/products` | Admin | List all products for admin management | Query: `category_id`, `search`, `page`, `size` |
| `POST` | `/api/v1/admin/products` | Admin | Create digital product | Body: `{ category_id, name, slug, image?, description?, instructions?, sort_order? }` |
| `PUT` | `/api/v1/admin/products/{id}` | Admin | Update product details | Path: `product_id`, Body: Product update fields |
| `DELETE`| `/api/v1/admin/products/{id}` | Admin | Delete product | Path: `product_id` |
| `PATCH`| `/api/v1/admin/products/{id}/status` | Admin | Toggle product active status | Path: `product_id`, Body: `{ is_active: boolean }` |
| `POST` | `/api/v1/admin/products/{id}/fields` | Admin | Add dynamic input field to product | Body: `{ name, label, type, placeholder?, is_required, sort_order? }` |
| `PUT` | `/api/v1/admin/fields/{field_id}` | Admin | Update input field configuration | Path: `field_id`, Body: Input field update |
| `DELETE`| `/api/v1/admin/fields/{field_id}` | Admin | Delete input field configuration | Path: `field_id` |

### 06. Packages
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/products/{id}/packages` | Public | List active purchase packages for a product | Path: `product_id` |
| `POST` | `/api/v1/admin/products/{id}/packages` | Admin | Create package option for product | Path: `product_id`, Body: `{ name, price, compare_price?, duration?, sort_order? }` |
| `PUT` | `/api/v1/admin/packages/{id}` | Admin | Update package details | Path: `package_id`, Body: Package update fields |
| `PATCH`| `/api/v1/admin/packages/{id}/status`| Admin | Toggle package active status | Path: `package_id`, Body: `{ is_active: boolean }` |
| `DELETE`| `/api/v1/admin/packages/{id}` | Admin | Delete package | Path: `package_id` |

### 07. Coupons & Discounts
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/coupons/validate` | Customer | Validate coupon against package | Body: `{ code, package_id, quantity? }` |
| `GET` | `/api/v1/admin/coupons` | Admin | List all promotional coupons | Query: `is_active` |
| `POST` | `/api/v1/admin/coupons` | Admin | Create coupon | Body: `{ code, type: "FIXED" \| "PERCENTAGE", value, max_discount?, minimum_order_amount?, usage_limit?, per_user_limit?, expires_at? }` |
| `PUT` | `/api/v1/admin/coupons/{id}` | Admin | Update coupon configuration | Path: `coupon_id` |
| `DELETE`| `/api/v1/admin/coupons/{id}` | Admin | Delete coupon | Path: `coupon_id` |

### 08. Orders & Checkout
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/checkout/preview` | Authenticated | Live calculation of subtotal, discount, errors | Body: `{ package_id, quantity?, coupon_code?, input_values? }` |
| `POST` | `/api/v1/orders` | Authenticated | Place direct order | Body: `{ package_id, quantity, coupon_code?, input_values, customer_note?, payment_method_id? }` |
| `GET` | `/api/v1/orders/my-orders` | Customer | List customer's orders | Query: `page`, `size`, `status_filter` |
| `GET` | `/api/v1/orders/{order_number}`| Authenticated | Get order details by order number | Path: `order_number` |
| `POST` | `/api/v1/orders/{order_number}/cancel`| Authenticated | Cancel unpaid pending order | Path: `order_number` |
| `GET` | `/api/v1/admin/orders` | Admin | List all platform orders | Query: `page`, `size`, `status_filter`, `search` |
| `PATCH`| `/api/v1/admin/orders/{id}/status` | Admin | Update order status | Path: `order_id`, Body: `{ status: OrderStatus }` |
| `PATCH`| `/api/v1/admin/orders/{id}/note` | Admin | Update internal fulfillment note | Path: `order_id`, Body: `{ admin_note: string }` |

### 09. Payment Methods
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/payment-methods` | Public | List active payment methods (bKash, etc.)| None |
| `GET` | `/api/v1/admin/payment-methods` | Admin | List all payment methods for admin | None |
| `POST` | `/api/v1/admin/payment-methods` | Admin | Create payment gateway channel | Body: `{ name, account_number, instructions?, logo?, sort_order? }` |
| `PUT` | `/api/v1/admin/payment-methods/{id}`| Admin | Update payment gateway channel | Path: `method_id` |
| `DELETE`| `/api/v1/admin/payment-methods/{id}`| Admin | Delete payment gateway channel | Path: `method_id` |

### 10. Payments & Webhooks
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/payments/submit` | Authenticated | Submit manual transaction ID | Body: `{ order_id, payment_method_id, transaction_id, sender_number }` |
| `GET` | `/api/v1/payments/order/{id}` | Authenticated | Get payment record for an order | Path: `order_id` |
| `GET` | `/api/v1/admin/payments` | Admin | List payments in verification queue | Query: `page`, `size`, `status_filter` |
| `POST` | `/api/v1/admin/payments/{id}/verify`| Admin | Approve payment (marks order PAID) | Path: `payment_id`, Body: `{ admin_notes? }` |
| `POST` | `/api/v1/admin/payments/{id}/reject`| Admin | Reject payment (reverts order) | Path: `payment_id`, Body: `{ admin_notes? }` |
| `POST` | `/api/v1/payments/webhook/sms` | Webhook (Secret) | Automated Android SMS reconciliation | Header: `X-Device-Secret`, Body: `{ sender, message, sim_slot?, device_id?, timestamp? }` |
| `GET` | `/api/v1/admin/payments/sms-logs`| Admin | View raw incoming SMS device logs | Query: `page`, `size`, `is_matched`, `search` |

### 11. Wallet & Top-Ups
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/wallet/me` | Customer | Get customer wallet balance | None |
| `GET` | `/api/v1/wallet/transactions` | Customer | Customer wallet ledger history | Query: `page`, `size` |
| `POST` | `/api/v1/orders/{order_number}/pay-with-wallet`| Authenticated | 1-Click order payment using wallet | Path: `order_number` |
| `POST` | `/api/v1/wallet/topup` | Customer | Submit wallet top-up request with TrxID | Body: `{ payment_method_id, amount, transaction_id, sender_number }` |
| `GET` | `/api/v1/wallet/topups/me` | Customer | Customer's top-up request history | None |
| `GET` | `/api/v1/admin/topups` | Admin | List top-up review queue | Query: `page`, `size`, `status_filter` |
| `POST` | `/api/v1/admin/topups/{id}/approve` | Admin | Approve top-up & credit customer balance | Path: `topup_id`, Body: `{ admin_notes? }` |
| `POST` | `/api/v1/admin/topups/{id}/reject` | Admin | Reject top-up request | Path: `topup_id`, Body: `{ admin_notes? }` |
| `POST` | `/api/v1/admin/wallets/{user_id}/adjust` | Admin | Admin manual balance credit or debit | Path: `user_id`, Body: `{ amount, type: "CREDIT" \| "DEBIT", description }` |

### 12. Lottery & Lucky Spin
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/lottery/active` | Authenticated | Get active lottery wheel & prize pool | None |
| `GET` | `/api/v1/lottery/my-eligibility`| Authenticated | Check customer's remaining spins | None |
| `POST` | `/api/v1/lottery/{id}/spin` | Authenticated | Spin wheel and receive randomized prize | Path: `lottery_id` |
| `GET` | `/api/v1/lottery/my-history` | Authenticated | View customer's past won prizes | None |
| `GET` | `/api/v1/admin/lotteries` | Admin | List all lottery campaigns | None |
| `POST` | `/api/v1/admin/lotteries` | Admin | Create lottery campaign | Body: `{ name, description?, starts_at?, ends_at?, is_active? }` |
| `POST` | `/api/v1/admin/lotteries/{id}/prizes` | Admin | Add prize to campaign | Path: `lottery_id`, Body: `{ product_id?, package_id?, discount_type, discount_value, probability, quantity }` |
| `GET` | `/api/v1/admin/lotteries/{id}/entries` | Admin | Audit customer entry spin logs | Path: `lottery_id`, Query: `page`, `size` |

### 13. Marketing (Banners & Popups)
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/banners` | Public | Active homepage banners for carousel | None |
| `GET` | `/api/v1/admin/banners` | Admin | List all banners for admin | None |
| `POST` | `/api/v1/admin/banners` | Admin | Create promotional banner | Body: `{ image, mobile_image?, title?, description?, button_text?, button_url?, sort_order?, is_active? }` |
| `PUT` | `/api/v1/admin/banners/{id}` | Admin | Update banner | Path: `banner_id` |
| `DELETE`| `/api/v1/admin/banners/{id}` | Admin | Delete banner | Path: `banner_id` |
| `GET` | `/api/v1/popups/active` | Public | Active announcement popup modal | None |
| `GET` | `/api/v1/admin/popups` | Admin | List all announcement popups | None |
| `POST` | `/api/v1/admin/popups` | Admin | Create announcement popup | Body: `{ title, content?, image?, button_text?, button_url?, display_type, starts_at?, ends_at?, is_active? }` |
| `PUT` | `/api/v1/admin/popups/{id}` | Admin | Update popup | Path: `popup_id` |
| `DELETE`| `/api/v1/admin/popups/{id}` | Admin | Delete popup | Path: `popup_id` |

### 14. Site Settings
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/settings` | Public | Get branding, support links & contacts | None |
| `PUT` | `/api/v1/admin/settings` | Admin | Update site branding & contact lines | Body: `{ site_name?, site_title?, logo?, favicon?, telegram_url?, facebook_url?, support_phone?, support_email? }` |

### 15. Media Uploads
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/media/upload` | Authenticated | Upload image/file (`multipart/form-data`)| Query: `folder` (`"products"`, `"avatars"`, etc.), Form-Data: `file` |
| `DELETE`| `/api/v1/media` | Authenticated | Delete uploaded media by relative URL | Query: `file_url` (`/media/products/uuid.png`) |

### 16. System Health
| Method | Endpoint | Auth | Purpose | Key Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Public | Comprehensive health check probe | None |
| `GET` | `/health` | Public | Root-level health check for load balancers | None |

---

## 7. AI Prompting Recipes & Frontend Code Generators

When using AI coding assistants (ChatGPT, Claude, Gemini, Copilot), use the following ready-made prompts:

### Recipe 1: Dynamic Product Details & Package Selector Form
```markdown
I have attached FRONTEND_HANDOFF.md and Digital_Product_Selling_System.postman_collection.json.
Please build a React component with TypeScript, Tailwind CSS, and TanStack Query for the Product Details page:
1. Fetch product details by slug using GET /api/v1/products/:slug.
2. Render the product hero (image, title, description, instructions).
3. Render a selectable grid of packages with active state, price, and strike-through compare_price.
4. Dynamically render the form controls based on product.input_fields (handling 'text', 'number', 'email', 'textarea').
5. Call POST /api/v1/checkout/preview with debounce as inputs/packages change to show real-time subtotal and validation status.
6. Provide a "Proceed to Checkout" button that redirects to the payment page with the created order.
```

### Recipe 2: Payment Modal (TrxID Manual Gateway & Wallet Balance)
```markdown
I have attached FRONTEND_HANDOFF.md.
Please generate a checkout modal component in React:
1. Fetch active payment methods via GET /api/v1/payment-methods.
2. Fetch current wallet balance via GET /api/v1/wallet/me.
3. Allow customer to toggle between "Pay with Wallet" (if balance >= total) and "Manual Mobile Banking" (bKash/Nagad/Rocket).
4. If "Pay with Wallet": call POST /api/v1/orders/:order_number/pay-with-wallet on submit.
5. If "Manual Mobile Banking": display the account number, instructions, and provide inputs for transaction_id and sender_phone, then call POST /api/v1/payments/submit.
6. Use react-hook-form, zod validation, and sonner for toast notifications.
```

### Recipe 3: Admin Paginated Orders Table with Status Updating
```markdown
Based on FRONTEND_HANDOFF.md:
Create an Admin Orders Management page using React, TanStack Table (or standard Tailwind table), and TanStack Query:
1. Query GET /api/v1/admin/orders with query parameters for page, size, status_filter, and search debounce.
2. Render columns: Order Number, Customer, Package/Product, Total Amount, Status badge with colored states, Date, Actions.
3. Add a dropdown to update order status via PATCH /api/v1/admin/orders/:order_id/status.
4. Add a dialog to view and edit internal fulfillment notes via PATCH /api/v1/admin/orders/:order_id/note.
5. Implement pagination controls using the PaginationMeta object.
```

### Recipe 4: Gamified Lucky Spin Wheel Component
```markdown
Using FRONTEND_HANDOFF.md:
Create an interactive canvas/SVG Lucky Wheel component in React:
1. Fetch active lottery via GET /api/v1/lottery/active and check eligibility via GET /api/v1/lottery/my-eligibility.
2. Render wheel segments corresponding to lottery.prizes.
3. When the user clicks "Spin Now", disable the button, start spinning CSS animation, and call POST /api/v1/lottery/:lottery_id/spin.
4. Ease the rotation to stop precisely on the won prize segment returned by the API.
5. Display a celebratory winning dialog with confetti effect!
```

---

## 8. Postman Workspace Navigation & Testing Tips

The companion collection [`Digital_Product_Selling_System.postman_collection.json`](./Digital_Product_Selling_System.postman_collection.json) is organized to mirror this document:

```text
📁 Digital Product Selling System API
  ├── 📁 01. Authentication & Profile
  ├── 📁 02. Admin - Dashboard
  ├── 📁 03. Admin - User Management
  ├── 📁 04. Categories
  ├── 📁 05. Products & Dynamic Fields
  ├── 📁 06. Packages
  ├── 📁 07. Coupons & Discounts
  ├── 📁 08. Orders & Checkout
  ├── 📁 09. Payment Methods
  ├── 📁 10. Payments & Webhooks
  ├── 📁 11. Wallet & Top-Ups
  ├── 📁 12. Lottery & Lucky Spin
  ├── 📁 13. Marketing (Banners & Popups)
  ├── 📁 14. Site Settings
  ├── 📁 15. Media Uploads
  └── 📁 16. System Health
```

### Postman Automated Token Capture
- **Admin Login Request**: Executing `POST /api/v1/auth/admin/login` runs an automatic Postman test script that stores `access_token` and `admin_token` into collection variables.
- **Customer Google Login**: Executing `POST /api/v1/auth/google` stores `access_token` and `refresh_token` into collection variables.
- **No Manual Copy-Pasting**: All subsequent requests automatically use `{{access_token}}` or `{{admin_token}}` in their Bearer Auth settings.

---

<div align="center">
  <sub>Engineered for maximum velocity, zero ambiguity, and seamless AI pair-programming.</sub>
</div>
