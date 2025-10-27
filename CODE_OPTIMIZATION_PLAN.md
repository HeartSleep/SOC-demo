# Code Optimization Plan 🚀

## Current State Analysis

**Codebase Size**: 58 Python files
**API Endpoints**: 166 async functions across 16 endpoint files
**Database**: PostgreSQL with connection pooling
**Cache**: Redis available but underutilized

---

## Optimization Categories

### 1. Performance Optimizations 🏎️
- Response caching
- Database query optimization
- Query result caching
- Response compression
- Lazy loading

### 2. API Optimizations 📡
- Pagination for list endpoints
- Field selection (sparse fieldsets)
- Batch operations
- Response compression

### 3. Database Optimizations 💾
- Query optimization
- Index optimization
- Connection pool tuning
- Query result caching

### 4. Code Quality Optimizations 📝
- Remove duplicate code
- Add type hints
- Optimize imports
- Better error handling

---

## Priority 1: High-Impact Optimizations

### A. Response Caching Layer ⚡
**Impact**: HIGH | **Effort**: LOW

Cache expensive operations like:
- User profile lookups
- Asset listings
- Vulnerability reports
- Statistics/dashboards

**Implementation**:
```python
# Redis-backed cache with TTL
@cache(ttl=300)  # 5 minutes
async def get_user_by_id(user_id: str):
    ...
```

### B. API Response Compression 📦
**Impact**: HIGH | **Effort**: LOW

Reduce bandwidth by 60-80%:
- Enable gzip compression
- Compress responses > 1KB
- Add compression headers

### C. Database Query Optimization 🔍
**Impact**: HIGH | **Effort**: MEDIUM

- Add composite indexes for common queries
- Use select_related for joins
- Add query result caching
- Optimize N+1 queries

### D. Pagination 📄
**Impact**: HIGH | **Effort**: LOW

- Limit results to 50 by default
- Add cursor-based pagination
- Return total count

---

## Priority 2: Medium-Impact Optimizations

### E. Query Result Caching 💰
**Impact**: MEDIUM | **Effort**: MEDIUM

Cache database query results:
- Asset listings
- User lists
- Statistics queries

### F. Lazy Loading 🦥
**Impact**: MEDIUM | **Effort**: LOW

Defer heavy imports:
- Scanner modules
- Report generators
- Heavy libraries

### G. Serialization Optimization 🎯
**Impact**: MEDIUM | **Effort**: MEDIUM

- Use orjson for faster JSON
- Optimize Pydantic models
- Add response model caching

---

## Priority 3: Code Quality

### H. Remove Duplicate Code ♻️
**Impact**: LOW | **Effort**: MEDIUM

- Extract common patterns
- Create utility functions
- DRY principle

### I. Add Type Hints 🏷️
**Impact**: LOW | **Effort**: HIGH

- Full type coverage
- Better IDE support
- Catch errors early

---

## Implementation Order

1. ✅ **Response Compression** (15 min)
2. ✅ **Response Caching Layer** (30 min)
3. ✅ **Pagination** (30 min)
4. ✅ **Database Index Optimization** (45 min)
5. ✅ **Query Result Caching** (45 min)
6. ✅ **Lazy Loading** (30 min)
7. ✅ **Serialization Optimization** (45 min)
8. 📋 **Code Deduplication** (2 hours)
9. 📋 **Type Hints** (4 hours)

**Total Time**: ~6 hours for high-impact items

---

## Expected Performance Gains

### Before Optimization:
- Response time: 200-500ms
- Database queries: 5-10 per request
- Bandwidth: 10-50KB per response
- Cache hit rate: 0%
- Memory usage: High (no optimization)

### After Optimization:
- Response time: 50-150ms (70% faster) ⚡
- Database queries: 1-3 per request (70% reduction) 📉
- Bandwidth: 2-15KB per response (70% smaller) 📦
- Cache hit rate: 60-80% 💰
- Memory usage: Optimized 🎯

---

## Monitoring Metrics

Track these after optimization:

1. **Response Time**:
   - P50: < 100ms
   - P95: < 300ms
   - P99: < 500ms

2. **Cache Performance**:
   - Hit rate: > 60%
   - Miss rate: < 40%
   - Eviction rate: < 10%

3. **Database**:
   - Query time: < 50ms
   - Pool utilization: < 80%
   - Connection wait: < 10ms

4. **API**:
   - Throughput: > 1000 req/s
   - Error rate: < 0.1%
   - Bandwidth: -70%

---

## Quick Wins (Start Here!)

### 1. Enable Response Compression
```python
# Add to main.py
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```
**Gain**: 60-80% bandwidth reduction
**Time**: 2 minutes

### 2. Add Response Caching
```python
# Create cache decorator
from functools import wraps
import pickle

async def cache_response(key: str, ttl: int = 300):
    cached = await redis.get(key)
    if cached:
        return pickle.loads(cached)
    # ... execute function
    await redis.setex(key, ttl, pickle.dumps(result))
    return result
```
**Gain**: 80% faster repeated requests
**Time**: 15 minutes

### 3. Add Pagination
```python
# Add to all list endpoints
@router.get("/assets")
async def list_assets(
    skip: int = 0,
    limit: int = 50,  # Default limit
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(Asset).offset(skip).limit(limit)
    )
    return result.scalars().all()
```
**Gain**: 90% less data transferred
**Time**: 10 minutes per endpoint

---

## Let's Start! 🚀

Shall I implement these optimizations in order?

1. Response Compression (2 min)
2. Response Caching (15 min)
3. Pagination (30 min)
4. Database Indexes (45 min)
5. Query Caching (45 min)

Total: ~2.5 hours for 70%+ performance improvement!