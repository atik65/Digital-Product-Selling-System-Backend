# 🛍️ Special Products (Landing Page) Frontend Handoff & Implementation Guide

> **API Route**: `GET /api/v1/special-products` (and alias `GET /api/v1/products/special` / `GET /special-products`)  
> **Target Page**: Website Landing Page / Storefront Showcase  
> **Response Contract**: 100% compliant with the legacy / BoostGhor-style category-grouped product schema.

---

## 📌 ১. ওভারভিউ (Overview)

এই এপিআইটি মূলত ওয়েবসাইটের **ল্যান্ডিং পেইজ (Landing Page)** এর জন্য তৈরি করা হয়েছে। এখানে একসাথে সমস্ত **Category** আসবে এবং প্রতিটি ক্যাটাগরির ভেতরে তার আন্ডারে থাকা সমস্ত **Products** নেস্টেড আকারে থাকবে (`products: [...]`)।

এতে করে ফ্রন্টএন্ডে আলাদা আলাদা করে ক্যাটাগরি এবং প্রোডাক্ট কল করতে হয় না, সিঙ্গেল ফেচেই পুরো ল্যান্ডিং পেইজের প্রোডাক্ট সেকশন রেন্ডার করা যায়।

---

## 🌐 ২. এন্ডপয়েন্ট রেফারেন্স (API Endpoints)

| Method | Endpoint | Description | Default Response Format |
| :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/special-products` | **Primary Endpoint** — ক্যাটাগরি অনুযায়ী প্রোডাক্টের গ্রুপ লিস্ট | Direct JSON Array `[...]` |
| **GET** | `/api/v1/products/special` | **Alias Endpoint** — একই ডেটা রিটার্ন করে | Direct JSON Array `[...]` |
| **GET** | `/special-products` | **Root Alias** — সরাসরি রুট পাথে অ্যাক্সেস | Direct JSON Array `[...]` |

### Query Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `active_only` | `boolean` | `true` | শুধুমাত্র একটিভ ক্যাটাগরি ও প্রোডাক্ট ফিল্টার করবে (`true` / `false`) |
| `category_id` | `integer` | `null` | নির্দিষ্ট একটি ক্যাটাগরির প্রোডাক্ট গ্রুপ পেতে চাইলে ক্যাটাগরি আইডি পাস করুন |
| `envelope` | `boolean` | `false` | `false` থাকলে সরাসরি raw array `[...]` রিটার্ন করে। `true` দিলে `{ success: true, status_code: 200, data: [...] }` হিসেবে র‍্যাপ করে দেয়। |

---

## 📘 ৩. TypeScript Interfaces

```typescript
export interface SpecialProduct {
  id: number;
  name: string;
  brand_id: number;           // প্যারেন্ট ক্যাটাগরি আইডি (Category ID)
  category_id: number;        // সাব-ক্যাটাগরি আইডি (ডিফল্ট: 0)
  lavel: number;              // ডিসপ্লে লেভেল / সর্টিং ক্রম (Sort Order)
  description: string;        // প্রোডাক্ট ডেসক্রিপশন (HTML ফরম্যাট বা টেক্সট)
  tag_line: string | null;    // ট্যাগলাইন (ডিফল্ট: "null")
  logo: string | null;        // প্রোডাক্ট লোগো/ইমেজ ফাইলের নাম বা ইউআরএল
  buy_price: string;          // বাই প্রাইস স্ট্রিং (যেমন: "1.000")
  sale_price: number;         // বিক্রয়মূল্য / সর্বনিম্ন প্যাকেজের দাম (যেমন: 1 বা 450)
  is_shop: number;            // শপ টাইপ আইডি (1 = ডিজিটাল সাবস্ক্রিপশন, 3 = সোশ্যাল সার্ভিস)
  quantity: number;           // স্টক কোয়ান্টিটি (যেমন: 999999)
  type: number;               // প্রোডাক্ট টাইপ (ডিফল্ট: 1)
  is_auto: number;            // অটোমেটেড ডেলিভারি ফ্ল্যাগ (1 = অটো, 0 = ম্যানুয়াল)
  is_active: number;          // স্ট্যাটাস (1 = একটিভ, 0 = নিষ্ক্রিয়)
  is_hot: string;             // হট আইটেম ব্যাজ ("0" বা "1")
  created_at: string | null;  // তৈরির সময় (ISO 8601)
  updated_at: string | null;  // আপডেটের সময় (ISO 8601)
  check_id: number;           // প্লেয়ার আইডি/চেক আইডি ফ্ল্যাগ (0 বা 1)
  slug: string | null;        // এসইও ফ্রেন্ডলি ইউআরএল স্ল্যাগ (যেমন: "netflix-premium")
  have_time_limite: number;   // টাইম লিমিট আছে কিনা (0 বা 1)
  limite_qty: number;         // লিমিট কোয়ান্টিটি
  limite_duration: number;    // লিমিট ডিউরেশন
  is_reseller: number;        // রিসেলারদের জন্য প্রযোজ্য কিনা (0 বা 1)
  input_name: string;         // কাস্টমারের কাছ থেকে চাওয়া প্রথম ইনপুট লেবেল (যেমন: "এখানে জিমেইল বসান")
  main_price: number;         // মেইন প্রাইস
  is_qty_minus: number;       // কোয়ান্টিটি কমার ফ্ল্যাগ
  is_user_show_qty: number;   // কাস্টমারকে কোয়ান্টিটি দেখানো হবে কিনা
  is_remove_char: number;     // স্পেশাল ক্যারেক্টার রিমুভ ফ্ল্যাগ
  sec_input_name: string | null; // দ্বিতীয় ইনপুট লেবেল (যদি ২য় কোনো ফিল্ড থাকে)
  redem_link: string | null;  // রিডিম লিংক
  package_design: number;     // প্যাকেজ কার্ড ডিজাইন লেআউট (ডিফল্ট: 2)
  check_unique_player_id: number;
  is_premium: number;         // প্রিমিয়াম প্রোডাক্ট কিনা (0 বা 1)
  premium_min_amount: number; // প্রিমিয়াম মিনিমাম এমাউন্ট (যেমন: 10000)
}

export interface SpecialCategory {
  id: number;
  name: string;               // ক্যাটাগরির নাম (যেমন: "বিনোদনমূলক সাবস্ক্রিপশন")
  logo: string | null;        // ক্যাটাগরি আইকন/ইমেজ ফাইলের নাম বা ইউআরএল
  created_at: string | null;  // তৈরির তারিখ
  updated_at: string | null;  // আপডেটের তারিখ
  lavel: number;              // ডিসপ্লে লেভেল / সর্টিং অর্ডার
  is_active: number;          // স্ট্যাটাস (1 = একটিভ)
  product_design: number;     // প্রোডাক্ট ডিসপ্লে ডিজাইন মোড (ডিফল্ট: 1)
  products: SpecialProduct[]; // এই ক্যাটাগরির আন্ডারে থাকা সমস্ত প্রোডাক্ট
}
```

---

## 📦 ৪. রেসপন্স স্যাম্পল (JSON Sample)

```json
[
  {
    "id": 32,
    "name": "বিনোদনমূলক সাবস্ক্রিপশন",
    "logo": "1771728617.jpg",
    "created_at": "2026-02-22T08:50:17.000+06:00",
    "updated_at": "2026-04-15T15:34:03.000+06:00",
    "lavel": 3,
    "is_active": 1,
    "product_design": 1,
    "products": [
      {
        "id": 135,
        "name": "NETFLIX",
        "brand_id": 32,
        "category_id": 0,
        "lavel": 2,
        "description": "<p>⦿ অর্ডার করার সময় অবশ্যই সঠিক Gmail Address প্রদান করুন।</p>",
        "tag_line": "null",
        "logo": "1776243949.jpg",
        "buy_price": "1.000",
        "sale_price": 450,
        "is_shop": 1,
        "quantity": 373773,
        "type": 1,
        "is_auto": 0,
        "is_active": 1,
        "is_hot": "0",
        "created_at": "2026-02-23T12:08:34.000+06:00",
        "updated_at": "2026-04-26T23:00:49.000+06:00",
        "check_id": 0,
        "slug": "netflix-premium",
        "have_time_limite": 0,
        "limite_qty": 0,
        "limite_duration": 0,
        "is_reseller": 0,
        "input_name": "এখানে আপনার জিমেইল বসান",
        "main_price": 0,
        "is_qty_minus": 0,
        "is_user_show_qty": 0,
        "is_remove_char": 0,
        "sec_input_name": "null",
        "redem_link": "null",
        "package_design": 2,
        "check_unique_player_id": 0,
        "is_premium": 0,
        "premium_min_amount": 10000
      }
    ]
  }
]
```

---

## 🖼️ ৫. ইমেজ ও মিডিয়া লোডিং নিয়ম (Media URLs)

- ডেটাবেজের `logo` ফিল্ডে যদি কোনো ফাইলের নাম থাকে (যেমন: `"1776243949.jpg"`):
  - ফুল ইমেজ URL হবে: `http://localhost:8000/media/1776243949.jpg` (অথবা আপনার প্রোডাকশন ডোমেন + `/media/` + `filename`).
- ফ্রন্টএন্ডে ইমেজ হেল্পার ফাংশন:
```typescript
export const getMediaUrl = (filename: string | null | undefined): string => {
  if (!filename || filename === "null") return "/placeholder-product.png";
  if (filename.startsWith("http://") || filename.startsWith("https://")) return filename;
  const baseUrl = import.meta.env.VITE_MEDIA_BASE_URL || "http://localhost:8000";
  return `${baseUrl}/media/${filename.replace(/^\/+/, "")}`;
};
```

---

## 💻 ৬. React / Next.js ল্যান্ডিং পেইজ ইমপ্লিমেন্টেশন এক্সাম্পল

নিচের কম্পোনেন্টটি আপনার ল্যান্ডিং পেইজে সরাসরি ব্যবহার করতে পারেন। এটি ক্যাটাগরি ট্যাব এবং প্রোডাক্ট গ্রিড কার্ড সুন্দরভাবে প্রদর্শন করে:

```tsx
import React, { useState, useEffect } from "react";
import axios from "axios";
import { SpecialCategory, SpecialProduct } from "@/types/special_product";

export const LandingSpecialProductsSection: React.FC = () => {
  const [categories, setCategories] = useState<SpecialCategory[]>([]);
  const [activeCategoryId, setActiveCategoryId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSpecialProducts = async () => {
      try {
        setLoading(true);
        // API Call
        const res = await axios.get<SpecialCategory[]>(
          "http://localhost:8000/api/v1/special-products"
        );
        setCategories(res.data);
        if (res.data.length > 0) {
          setActiveCategoryId(res.data[0].id);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load products");
      } finally {
        setLoading(false);
      }
    };

    fetchSpecialProducts();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error || categories.length === 0) {
    return null; // বা এরর মেসেজ রেন্ডার করুন
  }

  const currentCategory = categories.find((c) => c.id === activeCategoryId) || categories[0];

  return (
    <section className="py-12 bg-slate-950 text-white min-h-screen px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            জনপ্রিয় ডিজিটাল সার্ভিস ও প্রোডাক্টস
          </h2>
          <p className="mt-3 max-w-2xl mx-auto text-slate-400">
            সহজেই অর্ডার করুন আপনার প্রয়োজনীয় সাবস্ক্রিপশন এবং ডিজিটাল সার্ভিস
          </p>
        </div>

        {/* Category Pills / Navigation Tabs */}
        <div className="flex overflow-x-auto gap-3 pb-4 mb-8 no-scrollbar scroll-smooth">
          {categories.map((cat) => {
            const isActive = cat.id === activeCategoryId;
            return (
              <button
                key={cat.id}
                onClick={() => setActiveCategoryId(cat.id)}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium whitespace-nowrap transition-all duration-200 shadow-sm ${
                  isActive
                    ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-blue-500/25 ring-2 ring-blue-400"
                    : "bg-slate-850 bg-slate-900/80 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-800"
                }`}
              >
                <span>{cat.name}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-black/30">
                  {cat.products?.length || 0}
                </span>
              </button>
            );
          })}
        </div>

        {/* Products Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
          {currentCategory?.products?.map((prod: SpecialProduct) => (
            <div
              key={prod.id}
              className="group relative bg-slate-900/90 rounded-2xl border border-slate-800 overflow-hidden hover:border-slate-700 hover:shadow-xl transition-all duration-300 flex flex-col justify-between"
            >
              {/* Product Card Top & Image */}
              <div className="p-4 flex flex-col items-center text-center">
                <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-slate-800/80 p-2 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform duration-300 shadow-inner">
                  <img
                    src={
                      prod.logo && prod.logo !== "null"
                        ? `http://localhost:8000/media/${prod.logo}`
                        : "/fallback-product.png"
                    }
                    alt={prod.name}
                    className="w-full h-full object-contain rounded-xl"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src =
                        "https://placehold.co/150x150/1e293b/white?text=" +
                        encodeURIComponent(prod.name.slice(0, 3));
                    }}
                  />
                </div>

                {/* Product Name */}
                <h3 className="font-bold text-sm sm:text-base text-slate-100 group-hover:text-blue-400 transition-colors line-clamp-1">
                  {prod.name}
                </h3>

                {/* Dynamic Input Prompt Hint */}
                {prod.input_name && prod.input_name !== "null" && (
                  <p className="mt-1 text-xs text-slate-400 line-clamp-1">
                    {prod.input_name}
                  </p>
                )}
              </div>

              {/* Product Card Bottom / Action */}
              <div className="p-3 sm:p-4 pt-0 border-t border-slate-800/60 bg-slate-900/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400">শুরু মাত্র</span>
                  <span className="text-sm sm:text-base font-bold text-emerald-400">
                    ৳{prod.sale_price}
                  </span>
                </div>

                <a
                  href={`/products/${prod.slug && prod.slug !== "null" ? prod.slug : prod.id}`}
                  className="block w-full text-center py-2 px-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs sm:text-sm shadow-md transition-all active:scale-95"
                >
                  অর্ডার করুন
                </a>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {(!currentCategory?.products || currentCategory.products.length === 0) && (
          <div className="text-center py-16 text-slate-500">
            এই ক্যাটাগরিতে বর্তমানে কোনো প্রোডাক্ট পাওয়া যায়নি।
          </div>
        )}
      </div>
    </section>
  );
};
```

---

## ⚡ ৭. TanStack Query (React Query) হুক এক্সাম্পল

```typescript
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { SpecialCategory } from "@/types/special_product";

export const useSpecialProducts = (activeOnly = true) => {
  return useQuery<SpecialCategory[]>({
    queryKey: ["special-products", { activeOnly }],
    queryFn: async () => {
      const response = await axios.get<SpecialCategory[]>(
        "http://localhost:8000/api/v1/special-products",
        {
          params: { active_only: activeOnly },
        }
      );
      return response.data;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes caching
  });
};
```

---

## 🎯 ৮. চেকলিস্ট ও হ্যান্ডঅফ সামারি

- [x] **URL**: `GET /api/v1/special-products`
- [x] **Envelope**: ডিফল্টভাবে রুট JSON Array `[...]` রিটার্ন করে (কোনো র‍্যাপার ছাড়াই)। যদি র‍্যাপার প্রয়োজন হয়, `?envelope=true` ব্যবহার করা যাবে।
- [x] **Key Matching**: ব্যবহারকারীর দেওয়া JSON রেসপন্স স্যাম্পলের প্রতিটি ক্যাটাগরি ও প্রোডাক্ট ফিল্ড ১০০% হুবহু বিদ্যমান।
- [x] **Prices**: প্রোডাক্টের সাথে অ্যাসোসিয়েটেড প্যাকেজগুলোর সর্বনিম্ন দাম অনুযায়ী `sale_price` ও `buy_price` ডায়নামিকালি জেনারেট হয়।
- [x] **Inputs**: ডাইনামিক ইনপুট ফিল্ড কনফিগারেশনের ভিত্তিতে `input_name` এবং `sec_input_name` স্বয়ংক্রিয়ভাবে ম্যাপ করা হয়।
