# 🔐 Frontend Authentication Handoff & Implementation Guide

> **Digital Product Selling System Backend (FastAPI)**  
> **Module Focus**: Authentication & Authorization (Admin & Customer)  
> **API Version**: `v1` | **Base URL**: `http://localhost:8000/api/v1`  
> **Companion Postman Folder**: `01. Authentication & Profile`

---

## 📌 Document Purpose & Context

This document is a **standalone, production-grade guide** specifically created for the frontend developer and AI coding assistants to implement authentication in the **Admin Panel** first, and later in the customer storefront.

### Test Credentials (Pre-Seeded)
| Account Type | Email | Password | Role | Expected Behavior in Admin Panel |
| :--- | :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@example.com` | `admin123` | `admin` | ✅ **Login succeeds**, receives tokens & admin privileges |
| **Regular Customer** | `user@example.com` | `user123` | `customer` | ❌ **Login rejected (403 Forbidden)**: Non-admin denied |

---

## 📑 Table of Contents
1. [Authentication Architecture & Security Overview](#1-authentication-architecture--security-overview)
2. [Authentication Endpoints Specification](#2-authentication-endpoints-specification)
   - [Admin Login (`POST /auth/admin/login`)](#1-admin-credential-login)
   - [Token Refresh (`POST /auth/refresh`)](#2-token-refresh)
   - [Get Current Profile (`GET /auth/me`)](#3-get-current-user-profile)
   - [Update Profile (`PATCH /auth/me`)](#4-update-current-user-profile)
   - [Customer Google OAuth (`POST /auth/google`)](#5-customer-google-oauth2-login)
3. [Error Responses & Status Codes](#3-error-responses--status-codes)
4. [Complete Admin Panel Frontend Implementation](#4-complete-admin-panel-frontend-implementation)
   - [A. Token Storage Helper (`src/utils/token.ts`)](#a-token-storage-helper)
   - [B. Axios Client with Auto-Refresh Interceptor (`src/api/client.ts`)](#b-axios-client-with-auto-refresh-interceptor)
   - [C. Zustand Auth Store (`src/state/useAuthState.ts`)](#c-zustand-auth-store)
   - [D. Protected Route Guard (`src/routes/ProtectedRoute.tsx`)](#d-protected-route-guard)
   - [E. Admin Login Component (`src/pages/auth/login/Login.tsx`)](#e-admin-login-page-component)
5. [cURL Command Testing Suite](#5-curl-command-testing-suite)
6. [AI Prompting Recipe for Admin Panel](#6-ai-prompting-recipe-for-admin-panel)

---

## 1. Authentication Architecture & Security Overview

```text
       ┌──────────────────────────────────────────────────────────┐
       │                   Admin Login Flow                       │
       └────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │         POST /api/v1/auth/admin/login                    │
       │         Body: { email, password }                        │
       └────────────────────────────┬─────────────────────────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
              [Valid & Role=admin]         [Invalid or Role≠admin]
                     │                             │
                     ▼                             ▼
       ┌───────────────────────────┐ ┌───────────────────────────┐
       │ HTTP 200 OK               │ │ HTTP 401 Unauthorized /   │
       │ - access_token (60 min)   │ │ HTTP 403 Forbidden        │
       │ - refresh_token (7 days)  │ │ Show toast error message  │
       │ - user profile { ... }    │ └───────────────────────────┘
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ Save tokens in storage    │
       │ Redirect to / (Dashboard) │
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌──────────────────────────────────────────────────────────┐
       │ Subsequent Protected API Requests                        │
       │ Header: Authorization: Bearer <access_token>             │
       └────────────────────────────┬─────────────────────────────┘
                                    │
                          [If Token Expires 401]
                                    │
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ POST /api/v1/auth/refresh                                │
       │ Body: { refresh_token }                                  │
       │ ──► Grants new access_token & retries request            │
       └──────────────────────────────────────────────────────────┘
```

### Key Security Specifications
- **Token Format**: PyJWT signed with `HS256`.
- **Payload Claims**:
  - `sub`: User ID as string (e.g., `"1"`)
  - `role`: `"admin"` or `"customer"`
  - `type`: `"access"` or `"refresh"`
  - `exp`: Expiration timestamp in UTC
  - `iat`: Issued-at timestamp in UTC
- **Lifespans**:
  - `access_token`: **60 minutes** (`ACCESS_TOKEN_EXPIRE_MINUTES`)
  - `refresh_token`: **7 days** (`REFRESH_TOKEN_EXPIRE_DAYS`)
- **Admin RBAC Enforcement**:
  All routes under `/api/v1/admin/*` strictly enforce `require_role("admin")`. If an authenticated customer token tries to call admin routes, the server immediately rejects the request with:
  `HTTP 403 Forbidden: "Access denied: this action requires one of 'admin' roles."`.
- **Rate Limiting**:
  `POST /api/v1/auth/admin/login` is protected with SlowAPI leaky-bucket rate limiting set to **10 requests per minute** per IP.

---

## 2. Authentication Endpoints Specification

### 1. Admin Credential Login

Authenticates an administrator with email and password.

- **Method**: `POST`
- **Path**: `/api/v1/auth/admin/login`
- **Access Level**: Public
- **Rate Limit**: 10 requests / minute
- **Headers**: `Content-Type: application/json`

#### Request Body Schema
```json
{
  "email": "admin@example.com",
  "password": "adminpassword123"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `email` | string (email) | Yes | Registered admin email address |
| `password` | string | Yes | Plain text password (min 6 characters) |

#### Success Response (`HTTP 200 OK`)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Admin authentication successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "admin@example.com",
      "username": "superadmin",
      "name": "Super Admin",
      "image": null,
      "phone": "+8801700000000",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-09-11T12:00:00Z",
      "updated_at": "2026-09-11T12:00:00Z"
    }
  }
}
```

#### Error Scenarios
| Status Code | Reason | Response Message |
| :--- | :--- | :--- |
| `401 Unauthorized` | Invalid password or user not found | `"Invalid email or password."` |
| `403 Forbidden` | Valid credentials, but `role == 'customer'` | `"Access denied: Only administrators can log in here."` |
| `403 Forbidden` | User account suspended | `"User account is inactive."` |
| `422 Unprocessable`| Missing email or password | Field validation errors list |
| `429 Too Many Req` | Exceeded 10 requests / minute | `"Rate limit exceeded: 10 per 1 minute. Please try again later."` |

---

### 2. Token Refresh

Exchanges a valid long-lived refresh token for a fresh short-lived access token.

- **Method**: `POST`
- **Path**: `/api/v1/auth/refresh`
- **Access Level**: Public
- **Rate Limit**: 20 requests / minute
- **Headers**: `Content-Type: application/json`

#### Request Body Schema
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Success Response (`HTTP 200 OK`)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

#### Error Scenarios
| Status Code | Reason | Response Message |
| :--- | :--- | :--- |
| `401 Unauthorized` | Expired refresh token | `"Token has expired. Please login again."` |
| `401 Unauthorized` | Invalid JWT signature or malformed token | `"Invalid authentication token."` |
| `401 Unauthorized` | Passing an `access` token instead of `refresh` | `"Invalid token type. Expected 'refresh' token."` |

---

### 3. Get Current User Profile

Fetches the profile of the currently logged-in user using the Bearer access token.

- **Method**: `GET`
- **Path**: `/api/v1/auth/me`
- **Access Level**: Authenticated (`admin` or `customer`)
- **Headers**:
  ```http
  Authorization: Bearer <access_token>
  ```

#### Success Response (`HTTP 200 OK`)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "admin@example.com",
    "username": "superadmin",
    "name": "Super Admin",
    "image": null,
    "phone": "+8801700000000",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-09-11T12:00:00Z",
    "updated_at": "2026-09-11T12:00:00Z"
  }
}
```

#### Error Scenarios
| Status Code | Reason | Response Message |
| :--- | :--- | :--- |
| `401 Unauthorized` | Missing Authorization header | `"Authentication credentials were not provided."` |
| `401 Unauthorized` | Expired access token | `"Token has expired. Please login again."` |
| `401 Unauthorized` | User account deleted in database | `"User associated with this token no longer exists."` |
| `403 Forbidden` | User account deactivated | `"User account is inactive."` |

---

### 4. Update Current User Profile

Updates editable profile information for the authenticated user.

- **Method**: `PATCH`
- **Path**: `/api/v1/auth/me`
- **Access Level**: Authenticated (`admin` or `customer`)
- **Headers**:
  ```http
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```

#### Request Body Schema (All fields optional)
```json
{
  "name": "Super Administrator",
  "username": "superadmin_v2",
  "phone": "+8801799887766",
  "image": "/media/avatars/admin_avatar.png"
}
```

#### Success Response (`HTTP 200 OK`)
Returns the updated `User` object wrapped in `StandardResponse<User>`.

---

### 5. Customer Google OAuth2 Login (Reference for Storefront)

Used by customer storefront to login via Google ID token.

- **Method**: `POST`
- **Path**: `/api/v1/auth/google`
- **Access Level**: Public
- **Headers**: `Content-Type: application/json`

#### Request Body Schema
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs...",
  "phone": "+8801700000000"
}
```
- Returns the identical `TokenResponse` structure with `role: "customer"`.

---

## 3. Error Responses & Status Codes

All errors conform to this unified envelope:

```json
{
  "success": false,
  "status_code": 401,
  "message": "Invalid email or password.",
  "errors": null,
  "request_id": "req-7b89f81a-bb6f-4b45-8c7e-0b44b4da3789"
}
```

When displaying errors on the frontend:
```ts
const errorMessage = error.response?.data?.message || "An unexpected error occurred.";
toast.error(errorMessage);
```

---

## 4. Complete Admin Panel Frontend Implementation

Here is the exact, drop-in code structure matching your Admin Panel stack (**React 19 + Vite + TypeScript / JavaScript + Zustand + Axios + Sonner**).

### A. Token Storage Helper
Create `src/utils/token.ts`:

```typescript
const ACCESS_TOKEN_KEY = 'admin_access_token';
const REFRESH_TOKEN_KEY = 'admin_refresh_token';
const USER_KEY = 'admin_user';

export const getAccessToken = (): string | null => localStorage.getItem(ACCESS_TOKEN_KEY);
export const getRefreshToken = (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY);

export const setAuthData = (accessToken: string, refreshToken?: string, user?: any) => {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
};

export const getStoredUser = () => {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

export const clearAuthData = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};
```

---

### B. Axios Client with Auto-Refresh Interceptor
Create `src/api/client.ts`:

```typescript
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { getAccessToken, getRefreshToken, setAuthData, clearAuthData } from '@/utils/token';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// 1. Request Interceptor: Attach Bearer Token
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
  async (error: AxiosError<any>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Ignore 401s from login or refresh endpoints
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/admin/login') &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
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
        clearAuthData();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const newAccessToken = response.data.data.access_token;
        setAuthData(newAccessToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }

        processQueue(null, newAccessToken);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        clearAuthData();
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

### C. Zustand Auth Store
Create `src/state/useAuthState.ts`:

```typescript
import { create } from 'zustand';
import { apiClient } from '@/api/client';
import { getAccessToken, getStoredUser, setAuthData, clearAuthData } from '@/utils/token';

export interface User {
  id: number;
  email: string;
  username: string;
  name?: string | null;
  image?: string | null;
  phone?: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  updateUser: (updatedUser: Partial<User>) => void;
}

export const useAuthState = create<AuthState>((set) => ({
  user: getStoredUser(),
  token: getAccessToken(),
  isAuthenticated: !!getAccessToken(),
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await apiClient.post('/auth/admin/login', { email, password });
      const { access_token, refresh_token, user } = response.data.data;

      // Ensure user has admin role
      if (user.role !== 'admin') {
        throw new Error('Access denied: You do not have administrator permissions.');
      }

      setAuthData(access_token, refresh_token, user);
      set({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    clearAuthData();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
    window.location.href = '/login';
  },

  checkAuth: async () => {
    const token = getAccessToken();
    if (!token) {
      set({ isAuthenticated: false, user: null });
      return;
    }

    try {
      const response = await apiClient.get('/auth/me');
      const user = response.data.data;

      if (user.role !== 'admin' || !user.is_active) {
        clearAuthData();
        set({ isAuthenticated: false, user: null });
        return;
      }

      set({ user, isAuthenticated: true });
    } catch (error) {
      clearAuthData();
      set({ isAuthenticated: false, user: null });
    }
  },

  updateUser: (updatedUser: Partial<User>) => {
    set((state) => {
      if (!state.user) return state;
      const newUser = { ...state.user, ...updatedUser };
      localStorage.setItem('admin_user', JSON.stringify(newUser));
      return { user: newUser };
    });
  },
}));
```

---

### D. Protected Route Guard
Create `src/routes/ProtectedRoute.tsx`:

```tsx
import React, { useEffect } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthState } from '@/state/useAuthState';

export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, user, checkAuth } = useAuthState();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user && user.role !== 'admin') {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};
```

---

### E. Admin Login Page Component
Create `src/pages/auth/login/Login.tsx`:

```tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'sonner';
import { Lock, Mail, Eye, EyeOff, Loader2, ShieldCheck } from 'lucide-react';
import { useAuthState } from '@/state/useAuthState';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuthState();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password);
      toast.success('Welcome back, Admin!');
      navigate('/');
    } catch (err: any) {
      const msg =
        err.response?.data?.message ||
        err.message ||
        'Authentication failed. Please check your credentials.';
      toast.error(msg);
    }
  };

  // Quick Demo Auto-Fill
  const handleFillDemoAdmin = () => {
    setValue('email', 'admin@example.com', { shouldValidate: true });
    setValue('password', 'admin123', { shouldValidate: true });
    toast.info('Admin demo credentials populated.');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600/10 border border-indigo-500/20 rounded-xl mb-3 text-indigo-400">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Admin Portal</h1>
          <p className="text-sm text-slate-400 mt-1">
            Sign in with your administrative credentials
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* Email */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <Mail className="w-5 h-5" />
              </span>
              <input
                type="email"
                {...register('email')}
                placeholder="admin@example.com"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm transition"
              />
            </div>
            {errors.email && (
              <p className="text-xs text-rose-400 mt-1.5">{errors.email.message}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <Lock className="w-5 h-5" />
              </span>
              <input
                type={showPassword ? 'text' : 'password'}
                {...register('password')}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-10 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.password && (
              <p className="text-xs text-rose-400 mt-1.5">{errors.password.message}</p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 text-white font-medium rounded-lg text-sm transition shadow-lg shadow-indigo-600/20"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign In to Dashboard'
            )}
          </button>
        </form>

        {/* Demo Helper Button */}
        <div className="mt-6 pt-6 border-t border-slate-800 text-center">
          <button
            type="button"
            onClick={handleFillDemoAdmin}
            className="text-xs text-indigo-400 hover:text-indigo-300 transition underline underline-offset-2"
          >
            Click to fill Demo Admin Credentials (admin@example.com)
          </button>
        </div>

      </div>
    </div>
  );
};
```

---

## 5. cURL Command Testing Suite

You can test every authentication route right from your terminal:

### 1. Successful Admin Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'
```

### 2. Verify Current Profile (`GET /me`)
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN_HERE>"
```

### 3. Refresh Access Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<PASTE_REFRESH_TOKEN_HERE>"
  }'
```

### 4. Update Profile Info (`PATCH /me`)
```bash
curl -X PATCH "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN_HERE>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Super Admin Updated",
    "phone": "+8801700998877"
  }'
```

### 5. Attempt Non-Admin Login (Verifying 403 Rejection)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "user123"
  }'
```
*Expected Result*: Returns `403 Forbidden` with `"Access denied: Only administrators can log in here."`.

---

## 6. AI Prompting Recipe for Admin Panel

When prompting an AI assistant inside your Admin Panel codebase, copy and paste this exact prompt:

```markdown
I have attached AUTH_HANDOFF.md and Digital_Product_Selling_System.postman_collection.json.
Please implement the Admin Authentication system in this project:
1. Review the endpoints in AUTH_HANDOFF.md (specifically POST /api/v1/auth/admin/login, POST /api/v1/auth/refresh, and GET /api/v1/auth/me).
2. Set up our Axios client with request interceptor for Bearer JWT and response interceptor for automatic 401 token refresh queue.
3. Implement our Zustand auth state in src/state/useAuthState.ts managing user, token, isAuthenticated, login, logout, and checkAuth.
4. Wire up the Login page in src/pages/auth/login using React Hook Form + Zod, displaying error toasts via Sonner. Include a quick-fill demo button for admin@example.com / admin123.
5. Create a ProtectedRoute component in src/routes that guards all admin pages and redirects unauthenticated users to /login.
```

---

<div align="center">
  <sub>Engineered for rock-solid security, instant developer onboarding, and seamless AI execution.</sub>
</div>
