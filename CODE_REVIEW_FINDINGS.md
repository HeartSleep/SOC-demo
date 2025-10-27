# Code Review Findings - Logical Errors & Fixes

## Critical Issues 🔴

### 1. Database Query Execution Error
**File**: `backend/app/core/database.py:52`

**Issue**:
```python
await conn.execute("SELECT 1")  # ❌ Missing text() wrapper
```

**Problem**: Raw SQL strings need to be wrapped with `text()` in SQLAlchemy 2.0+

**Fix**:
```python
from sqlalchemy import text

async def init_database():
    # ...
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))  # ✅ Correct
```

**Severity**: CRITICAL - Will cause startup failure

---

### 2. Rate Limit Response Type Error
**File**: `backend/app/core/rate_limit.py:62-77`

**Issue**:
```python
response = Response(
    content={  # ❌ Response doesn't accept dict directly
        "error": "rate_limit_exceeded",
        ...
    },
    ...
)
```

**Problem**: `Response` expects bytes/string, not dict. Should use `JSONResponse`.

**Fix**:
```python
from fastapi.responses import JSONResponse

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning(...)

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail)
        },
        headers={
            "Retry-After": str(exc.detail.split()[-1]),
            "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(exc.detail.split()[-1])
        }
    )
```

**Severity**: CRITICAL - Will cause 500 errors when rate limit is exceeded

---

### 3. WebSocket Timestamp Duplication
**File**: `backend/app/core/websocket.py:155, 174, 200, 203`

**Issue**:
```python
async def broadcast_to_room(self, message: dict, room: str):
    if room in self.rooms:
        message["timestamp"] = datetime.utcnow().isoformat()  # ✅ Added here

        for user_id in self.rooms[room]:
            await self.send_personal_message(message, user_id)  # ❌ Adds timestamp again!
```

**Problem**: Timestamp is added multiple times in the call chain:
- `broadcast_to_room()` adds timestamp (line 174)
- Then calls `send_personal_message()` which adds timestamp again (line 155)
- Same issue in `broadcast()` method

**Fix Option 1** (Recommended - add internal flag):
```python
async def send_personal_message(self, message: dict, user_id: str, _skip_timestamp: bool = False):
    if user_id in self.active_connections:
        # Add timestamp only if not already added
        if not _skip_timestamp and "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")

async def broadcast_to_room(self, message: dict, room: str):
    if room in self.rooms:
        # Add timestamp once
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        for user_id in self.rooms[room]:
            await self.send_personal_message(message, user_id, _skip_timestamp=True)
    # ... rest of code
```

**Fix Option 2** (Simpler - only add at top level):
```python
async def send_personal_message(self, message: dict, user_id: str):
    if user_id in self.active_connections:
        # Don't add timestamp here, let caller handle it
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")

async def broadcast_to_room(self, message: dict, room: str):
    if room in self.rooms:
        # Add timestamp here
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        for user_id in self.rooms[room]:
            await self.send_personal_message(message, user_id)
```

**Severity**: HIGH - Will cause incorrect timestamps and message mutations

---

## High Priority Issues 🟡

### 4. CSRF Form Data Consumption
**File**: `backend/app/core/csrf.py:84-89`

**Issue**:
```python
if not csrf_token:
    if request.method == "POST":
        try:
            form = await request.form()  # ❌ Consumes request body
            csrf_token = form.get("csrf_token")
        except Exception:
            pass
```

**Problem**: Once `request.form()` is called, the request body is consumed and cannot be read again by the endpoint handler. This will break form-based endpoints.

**Fix**:
```python
if not csrf_token:
    # Try to get from form data if Content-Type is form
    content_type = request.headers.get("Content-Type", "")
    if request.method == "POST" and "form" in content_type:
        try:
            # Store form for later use
            request._form = await request.form()
            csrf_token = request._form.get("csrf_token")
        except Exception:
            pass
```

**Better Solution**: Don't support form-based CSRF for API endpoints, require header:
```python
# Remove form data check entirely for API-only applications
if not csrf_token:
    logger.warning(f"CSRF token missing for {request.url.path}")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="CSRF token missing. Include X-CSRF-Token header."
    )
```

**Severity**: HIGH - Will break form-based endpoints

---

### 5. SQLAlchemy Column Default with Mutable Types
**File**: All model files (user.py, asset.py, task.py, etc.)

**Issue**:
```python
permissions = Column(ARRAY(String), default=list, nullable=False)  # ❌ Mutable default
tags = Column(ARRAY(String), default=list, nullable=False)
```

**Problem**: Using mutable default values (`list`, `dict`) can cause all instances to share the same object.

**Fix**:
```python
from sqlalchemy.sql import expression

permissions = Column(ARRAY(String), default=expression.cast([], ARRAY(String)), nullable=False)

# Or use server_default for database-level default
permissions = Column(ARRAY(String), server_default='{}', nullable=False)

# Or handle in Python with callable
def default_list():
    return []

permissions = Column(ARRAY(String), default=default_list, nullable=False)
```

**Best Practice for SQLAlchemy 2.0**:
```python
from typing import List as ListType

permissions: Mapped[ListType[str]] = mapped_column(ARRAY(String), default=lambda: [], nullable=False)
```

**Severity**: HIGH - Can cause data corruption between instances

---

### 6. Duplicate Index Definitions
**File**: All model files

**Issue**:
```python
# Column already has index=True
username = Column(String(50), unique=True, nullable=False, index=True)

# Then redundantly defined in __table_args__
__table_args__ = (
    Index('idx_user_username', 'username'),  # ❌ Duplicate index
    ...
)
```

**Problem**: Creates duplicate indexes, wasting space and slowing inserts.

**Fix**:
```python
# Option 1: Remove index=True from column
username = Column(String(50), unique=True, nullable=False)

__table_args__ = (
    Index('idx_user_username', 'username'),
    ...
)

# Option 2: Remove from __table_args__
username = Column(String(50), unique=True, nullable=False, index=True)

__table_args__ = (
    # Remove idx_user_username
    Index('idx_user_email', 'email'),
    ...
)
```

**Severity**: MEDIUM - Performance impact on writes

---

## Medium Priority Issues 🟢

### 7. Redis Connection Not Closed on Shutdown
**File**: `backend/app/core/websocket.py`

**Issue**: Redis connection is opened but never properly closed in lifespan cleanup.

**Fix**:
```python
class ConnectionManager:
    async def disconnect_redis(self):
        """Close Redis connection"""
        if self.pubsub:
            await self.pubsub.unsubscribe("ws:broadcast")
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        logger.info("Redis disconnected for WebSocket")

# In main.py lifespan cleanup:
async def lifespan(app: FastAPI):
    # ... startup code ...
    yield

    # Cleanup
    try:
        await manager.disconnect_redis()  # ✅ Add this
        await close_database()
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")
```

**Severity**: MEDIUM - Resource leak

---

### 8. Missing Import in rate_limit.py
**File**: `backend/app/core/rate_limit.py`

**Issue**:
```python
from fastapi import Request, Response  # Response imported
from slowapi import Limiter, _rate_limit_exceeded_handler  # ❌ _rate_limit_exceeded_handler not used
```

**Problem**:
1. `Response` type is wrong (should be `JSONResponse`)
2. `_rate_limit_exceeded_handler` is imported but not used (we define our own)

**Fix**:
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
```

**Severity**: MEDIUM - Type confusion

---

### 9. Incorrect SQL Text Usage in Migration Check
**File**: `backend/app/core/database.py:51-52`

**Issue**: Already covered in Issue #1

---

### 10. Missing Error Handling in WebSocket Disconnect
**File**: `backend/app/core/websocket.py:100-104`

**Issue**:
```python
if user_id in self.active_connections:
    self.active_connections[user_id].remove(websocket)  # ❌ Can raise ValueError if not in list
```

**Problem**: If websocket is not in the list, `remove()` will raise `ValueError`.

**Fix**:
```python
if user_id in self.active_connections:
    try:
        self.active_connections[user_id].remove(websocket)
    except ValueError:
        logger.warning(f"WebSocket not found in connections for user {user_id}")

    if not self.active_connections[user_id]:
        del self.active_connections[user_id]
```

**Severity**: MEDIUM - Can cause disconnect errors

---

## Low Priority Issues / Improvements 🔵

### 11. Hardcoded Salt in CSRF
**File**: `backend/app/core/csrf.py:16-19`

**Issue**:
```python
csrf_serializer = URLSafeTimedSerializer(
    settings.CSRF_SECRET_KEY,
    salt="csrf-token"  # ⚠️ Hardcoded salt
)
```

**Recommendation**: Move to settings for easier rotation.

**Fix**:
```python
# In config.py
CSRF_TOKEN_SALT: str = "csrf-token-v1"

# In csrf.py
csrf_serializer = URLSafeTimedSerializer(
    settings.CSRF_SECRET_KEY,
    salt=settings.CSRF_TOKEN_SALT
)
```

**Severity**: LOW - Security best practice

---

### 12. datetime.utcnow() Deprecation
**File**: Multiple files

**Issue**:
```python
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # ⚠️ utcnow deprecated
```

**Problem**: `datetime.utcnow()` is deprecated in Python 3.12+

**Fix**:
```python
from datetime import datetime, timezone

created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

# Or use server-side default
from sqlalchemy.sql import func
created_at = Column(DateTime, server_default=func.now(), nullable=False)
```

**Severity**: LOW - Future compatibility

---

### 13. Missing Type Hints in WebSocket Manager
**File**: `backend/app/core/websocket.py`

**Issue**: Some methods lack proper type hints.

**Recommendation**: Add type hints for better IDE support and error catching.

**Severity**: LOW - Code quality

---

### 14. No Connection Pool Monitoring
**File**: `backend/app/core/database.py`

**Issue**: No way to monitor connection pool health.

**Recommendation**: Add endpoint to check pool status:
```python
def get_pool_status() -> dict:
    """Get connection pool statistics"""
    if not engine:
        return {"status": "not_initialized"}

    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow()
    }
```

**Severity**: LOW - Observability improvement

---

## Summary of Required Fixes

### Must Fix Before Production:
1. ✅ Add `text()` wrapper to SQL execute (database.py:52)
2. ✅ Change Response to JSONResponse (rate_limit.py:62)
3. ✅ Fix WebSocket timestamp duplication (websocket.py)
4. ✅ Fix SQLAlchemy mutable defaults (all models)
5. ✅ Fix CSRF form data consumption (csrf.py:84)

### Should Fix Soon:
6. ✅ Remove duplicate indexes (all models)
7. ✅ Add Redis connection cleanup (websocket.py)
8. ✅ Fix imports in rate_limit.py
9. ✅ Add error handling to WebSocket disconnect

### Nice to Have:
10. Move CSRF salt to config
11. Update to datetime.now(timezone.utc)
12. Add type hints
13. Add pool monitoring

---

## Testing Recommendations

After fixes, test:

1. **Database Connection**:
   ```bash
   python3 -c "import asyncio; from app.core.database import init_database; asyncio.run(init_database())"
   ```

2. **Rate Limiting**:
   ```bash
   for i in {1..70}; do curl http://localhost:8000/health; done
   ```

3. **WebSocket Timestamps**:
   ```javascript
   ws.onmessage = (e) => {
     const msg = JSON.parse(e.data);
     console.log('Timestamp count:', JSON.stringify(msg).match(/timestamp/g)?.length);
   };
   ```

4. **CSRF Token**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/test \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   # Should get CSRF error
   ```

---

## Files Needing Updates

1. `backend/app/core/database.py` - SQL text() wrapper
2. `backend/app/core/rate_limit.py` - JSONResponse fix
3. `backend/app/core/websocket.py` - Timestamp logic + cleanup
4. `backend/app/core/csrf.py` - Form data handling
5. `backend/app/api/models/*.py` - All 5 model files (defaults + indexes)
6. `backend/app/main.py` - Add Redis cleanup

---

**Priority**: Fix issues #1-5 immediately before any testing or deployment.