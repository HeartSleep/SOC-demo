# Frontend Issues and Fixes

## Current Status

**Frontend Server**: ✅ Running on http://localhost:5173
**Backend Server**: ✅ Running on http://localhost:8000
**API Proxy**: ✅ Configured in vite.config.ts

---

## Issues Identified

### 1. SASS Deprecation Warnings ⚠️

**Severity**: LOW (Non-blocking)
**Impact**: Future compatibility

**Issues**:
- Using deprecated `@import` syntax (will be removed in Dart Sass 3.0.0)
- Using deprecated `lighten()` function (should use `color.scale()` or `color.adjust()`)
- Legacy JS API warnings

**Location**:
- `src/styles/index.scss`
- `src/styles/theme.scss`
- `vite.config.ts` (SCSS preprocessor options)

**Fix Required**:
```scss
// Before (Deprecated):
@import './variables.scss';
--el-color-primary-light-3: #{lighten($primary-color, 30%)};

// After (Modern):
@use './variables.scss' as vars;
@use 'sass:color';
--el-color-primary-light-3: #{color.adjust(vars.$primary-color, $lightness: 30%)};
```

**Status**: 📋 TODO - Not urgent, can be fixed later

---

### 2. Duplicate SCSS Import in vite.config.ts 🐛

**Severity**: MEDIUM
**Impact**: Redundant processing, potential style conflicts

**Issue**:
In `vite.config.ts`, the SCSS preprocessor options add an automatic import:
```typescript
scss: {
  additionalData: `@import "@/styles/variables.scss";`
}
```

But `src/styles/index.scss` already imports variables:
```scss
@import "@/styles/variables.scss";
@import './variables.scss';  // Duplicate!
```

**This causes**:
- Variables imported twice
- SASS deprecation warnings about duplicate imports
- Slightly slower compilation

**Fix**:
Remove the duplicate import from either location.

**Status**: 📋 TODO - Should be fixed

---

### 3. API Response Type Mismatch (Potential) ⚠️

**Severity**: MEDIUM
**Impact**: Runtime errors on API calls

**Potential Issue**:
The `request.ts` returns `response.data` directly:
```typescript
return response.data  // Line 94
```

But FastAPI endpoints might return different structures:
- Some return data directly
- Some return `{items: [], total: 123}` (paginated)
- Backend now uses `ORJSONResponse` which might serialize differently

**Needs Testing**:
- Login flow
- Asset listing
- Pagination responses

**Status**: 🔍 NEEDS VERIFICATION

---

### 4. Missing CSRF Token Integration ⚠️

**Severity**: MEDIUM
**Impact**: CSRF-protected endpoints will fail

**Issue**:
Backend has CSRF protection enabled, but frontend doesn't send CSRF tokens.

**Backend expects** (from `backend/app/core/csrf.py`):
```python
csrf_token = request.headers.get("X-CSRF-Token")
```

**Frontend doesn't send it** (in `src/utils/request.ts`):
```typescript
// Missing:
config.headers['X-CSRF-Token'] = getCsrfToken()
```

**Fix Required**:
1. Add CSRF token management in `src/utils/auth.ts`
2. Update `src/utils/request.ts` to include token in headers
3. Fetch CSRF token on app initialization

**Status**: 🚨 CRITICAL - Will cause POST/PUT/DELETE to fail

---

### 5. Authentication Header Format Issue (Potential) ⚠️

**Severity**: HIGH
**Impact**: All authenticated requests will fail

**Issue**:
Backend expects OAuth2 form data for login (from backend code):
```python
# backend/app/api/endpoints/auth.py
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    ...
```

But frontend sends JSON:
```typescript
// frontend/src/api/auth.ts
export function login(data: LoginParams) {
  return request({
    url: '/auth/login',
    method: 'post',
    data  // Sends as JSON
  })
}
```

OAuth2PasswordRequestForm expects `application/x-www-form-urlencoded`:
- `username=xxx&password=yyy`

Not JSON:
- `{"username": "xxx", "password": "yyy"}`

**Fix Required**:
Update login function to send form data:
```typescript
export function login(data: LoginParams) {
  const formData = new URLSearchParams()
  formData.append('username', data.username)
  formData.append('password', data.password)

  return request({
    url: '/auth/login',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
}
```

**Status**: 🚨 CRITICAL - Login will not work

---

### 6. Missing Error Handling for Demo Mode 📝

**Severity**: LOW
**Impact**: Better UX

**Issue**:
Backend is running in demo mode (no DB/Redis), but frontend doesn't have special handling for demo responses.

**Enhancement**:
Add demo mode detection and appropriate messaging.

**Status**: 📋 ENHANCEMENT

---

## Priority Fixes

### 🚨 Critical (Fix Immediately):

1. **Fix Login Request Format** - Login won't work without this
   - File: `src/api/auth.ts`
   - Change: Send form data instead of JSON

2. **Add CSRF Token Support** - POST/PUT/DELETE requests will fail
   - Files: `src/utils/auth.ts`, `src/utils/request.ts`
   - Change: Fetch and include CSRF token in headers

### ⚠️ High Priority:

3. **Remove Duplicate SCSS Imports** - Causing warnings
   - File: `src/styles/index.scss` or `vite.config.ts`
   - Change: Remove one of the duplicate imports

### 📋 Medium Priority:

4. **Update SASS Syntax** - Future compatibility
   - Files: All SCSS files
   - Change: Migrate to modern SASS syntax

5. **Add Demo Mode Handling** - Better UX
   - Files: Various views
   - Change: Detect and display demo mode appropriately

---

## Testing Checklist

### Before Fixes:
- [ ] Test login (expected: will fail)
- [ ] Test asset list (expected: might work if no auth)
- [ ] Test asset create (expected: will fail - CSRF)
- [ ] Check browser console for errors
- [ ] Check network tab for API calls

### After Fixes:
- [ ] Test login with test credentials
- [ ] Test all CRUD operations
- [ ] Verify CSRF token in request headers
- [ ] Check for console errors
- [ ] Verify API responses are handled correctly

---

## Next Steps

1. Fix critical issues first (login format, CSRF)
2. Test the login flow
3. Verify API connectivity
4. Check all pages for exceptions
5. Document any additional issues found
6. Create fix scripts/patches

---

**Created**: 2025-09-30
**Status**: ANALYSIS COMPLETE - FIXES NEEDED