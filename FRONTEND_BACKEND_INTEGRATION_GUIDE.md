# Frontend-Backend Integration Guide

## 🎯 Overview
This guide provides a complete solution for integrating the frontend and backend of your SOC Security Platform, addressing common compatibility issues and ensuring smooth communication between services.

## 🔴 Critical Issues Found

### 1. **Database ORM Mismatch (CRITICAL)**
- **Problem**: Backend uses SQLAlchemy models but endpoints have MongoDB-style queries
- **Impact**: All user and auth endpoints fail with AttributeError
- **Files Affected**:
  - `backend/app/api/endpoints/users.py`
  - `backend/app/api/endpoints/auth.py`

### 2. **Missing WebSocket Authentication (HIGH)**
- **Problem**: WebSocket endpoint has TODO comment, no actual authentication
- **Impact**: Unauthorized access to real-time data
- **File**: `backend/app/api/endpoints/websocket_endpoint.py:28`

### 3. **Response Format Inconsistency (MEDIUM)**
- **Problem**: Some endpoints return arrays, others return paginated objects
- **Impact**: Frontend has to handle multiple response formats
- **Affected**: Asset, User, Task endpoints

## 📋 Integration Checklist

### Backend Configuration
- [ ] Fix SQLAlchemy queries in user/auth endpoints
- [ ] Implement WebSocket authentication
- [ ] Standardize response formats
- [ ] Ensure CORS allows frontend origin
- [ ] Use environment variables for secrets

### Frontend Configuration
- [ ] API base URL set to `/api/v1`
- [ ] Proxy configured in `vite.config.ts`
- [ ] Token management in axios interceptors
- [ ] Error handling for all status codes
- [ ] WebSocket reconnection logic

## 🛠️ Quick Fix Commands

### 1. Fix Database Queries
```bash
# Apply the integration fixes
python fix_integration_issues.py

# This will:
# - Fix SQLAlchemy queries
# - Add WebSocket authentication
# - Standardize responses
# - Update CORS configuration
```

### 2. Start Services
```bash
# Terminal 1: Start Backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd frontend
npm run dev

# Terminal 3: Run Tests
python test_frontend_backend_integration.py
```

## 🔧 Manual Fixes Required

### Fix 1: Update User Endpoints (backend/app/api/endpoints/users.py)
Replace MongoDB-style queries with SQLAlchemy:

```python
# OLD (MongoDB style)
users = await User.find().skip(skip).limit(limit).to_list()

# NEW (SQLAlchemy style)
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session

async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
```

### Fix 2: Implement WebSocket Auth (backend/app/api/endpoints/websocket_endpoint.py)
```python
# Replace TODO with:
from app.core.security import security

if not token:
    await websocket.close(code=1008, reason="Missing token")
    return

payload = security.verify_token(token)
if not payload:
    await websocket.close(code=1008, reason="Invalid token")
    return
```

### Fix 3: Frontend API Configuration (frontend/vite.config.ts)
```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  // ... rest of config
})
```

## 📊 API Endpoint Mapping

| Frontend Call | Backend Endpoint | Status | Notes |
|--------------|------------------|--------|-------|
| POST /api/v1/auth/login | ✅ Exists | ❌ Broken | Fix SQLAlchemy queries |
| GET /api/v1/auth/me | ✅ Exists | ❌ Broken | Fix SQLAlchemy queries |
| GET /api/v1/assets/ | ✅ Exists | ⚠️ Works | Returns array in demo mode |
| POST /api/v1/assets/ | ✅ Exists | ⚠️ Works | Demo mode only |
| GET /api/v1/users/ | ✅ Exists | ❌ Broken | Fix SQLAlchemy queries |
| WS /api/v1/ws/{id} | ✅ Exists | ❌ No Auth | Add authentication |

## 🔄 Response Format Standards

### Paginated Lists
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

### Single Entity
```json
{
  "id": "123",
  "field1": "value1",
  "field2": "value2"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status": 400,
  "errors": ["field1: required", "field2: invalid"]
}
```

## 🧪 Testing Integration

### Run Automated Tests
```bash
# Full integration test suite
python test_frontend_backend_integration.py

# Quick health check
curl http://localhost:8000/health

# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

### Expected Test Results
- ✅ Authentication endpoint accessible
- ✅ CORS headers present
- ✅ Response formats consistent
- ✅ WebSocket connects with token
- ✅ Data models compatible

## 🚀 Performance Optimizations

### Backend
1. **Connection Pooling**: Already configured in SQLAlchemy
2. **Response Caching**: Redis cache available
3. **Async Operations**: Using FastAPI async endpoints
4. **GZIP Compression**: Enabled in middleware

### Frontend
1. **API Request Batching**: Combine multiple requests
2. **Response Caching**: Use Pinia store caching
3. **Lazy Loading**: Load data on demand
4. **WebSocket for Real-time**: Reduce polling

## 📝 Development Workflow

1. **Make Backend Changes**
   ```bash
   cd backend
   # Edit files
   python -m pytest  # Run tests
   ```

2. **Update Frontend Types**
   ```bash
   cd frontend
   npm run type-check  # Verify types
   ```

3. **Test Integration**
   ```bash
   python test_frontend_backend_integration.py
   ```

4. **Deploy**
   ```bash
   docker-compose up -d  # Production deployment
   ```

## 🔍 Debugging Tips

### Check Backend Logs
```bash
tail -f backend/logs/backend.log
```

### Monitor Network Requests
- Open browser DevTools
- Go to Network tab
- Filter by XHR/Fetch
- Check request/response details

### Test Individual Endpoints
```bash
# Use httpie or curl
http GET localhost:8000/api/v1/assets/ "Authorization: Bearer {token}"
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [Vue 3 + TypeScript Guide](https://vuejs.org/guide/typescript/overview.html)
- [Axios Interceptors](https://axios-http.com/docs/interceptors)

## ✅ Success Criteria

Your integration is working correctly when:
1. Frontend can login and receive JWT token
2. All API calls include Authorization header
3. WebSocket connects with authentication
4. Response formats are predictable
5. Error messages are user-friendly
6. No CORS errors in browser console
7. Data updates reflect in real-time

## 🆘 Troubleshooting

### "Backend not running"
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### "CORS error"
- Check `BACKEND_CORS_ORIGINS` in `backend/app/core/config.py`
- Ensure frontend URL is included

### "AttributeError: _inheritance_inited"
- This is the SQLAlchemy/MongoDB mismatch
- Run `python fix_integration_issues.py`

### "WebSocket connection failed"
- Check token is being sent: `?token={jwt_token}`
- Verify WebSocket authentication is implemented

## 🎯 Next Steps

1. **Immediate**: Fix SQLAlchemy queries in user endpoints
2. **High Priority**: Implement WebSocket authentication
3. **Medium Priority**: Standardize all response formats
4. **Low Priority**: Add OpenAPI documentation generation
5. **Future**: Implement GraphQL endpoint for flexible queries

---

**Need Help?**
- Check `integration_test_report.json` for detailed test results
- Review `fix_summary.json` for applied fixes
- Run `python test_frontend_backend_integration.py` for current status