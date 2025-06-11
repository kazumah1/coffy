# Authentication Persistence Testing Guide

## Overview
This guide helps you verify that users stay logged in after reloading your iOS app, especially when profiles are saved to the server (not locally).

## 🆕 NEW: Profile Syncing Issue Fixed

### The Previous Problem
- Users had to redo profile setup (name, phone, contacts) every time they signed back in
- Profile data was saved to server but not properly retrieved on sign-in
- Endpoint mismatch: saving to `/auth/users/update-profile` but checking `/auth/user/{id}`

### The New Solution  
- **Fixed endpoint matching**: Profile completion check now uses correct endpoints
- **Added server profile syncing**: `syncProfileFromServer()` function to retrieve existing data
- **Better error handling**: Multiple fallback strategies for finding profile data
- **Enhanced logging**: Detailed logs to track what's happening with profile data

## Key Changes Made

### 1. Fixed Profile Endpoint Matching
- **Before**: Saved to `/auth/users/update-profile`, checked `/auth/user/{id}` 
- **After**: Checks `/auth/users/profile/{id}` first, then falls back to `/auth/user/{id}`

### 2. Added Server Profile Syncing
- New `syncProfileFromServer()` function retrieves existing profile data
- Automatically called during login for existing users
- Can be manually triggered for debugging

### 3. Improved Profile Completion Logic
- Multiple endpoint attempts before falling back to local storage
- Better error handling doesn't disrupt authentication
- Enhanced logging shows exactly what's being checked

### 4. Debug Tools Added
- `DEBUG_PROFILE_COMPONENT.tsx` for manual testing
- Functions to check profile completion, sync from server, view stored data

## Testing Steps

### Test 1: Existing User Profile Recovery (PRIMARY TEST)
1. **First Login**: Complete full profile setup (name, phone, contacts)
2. **Verify Save**: Check console logs that profile is saved to server
3. **Sign Out**: Use sign out function 
4. **Sign Back In**: Complete Google OAuth again
5. **Expected**: Should skip profile setup and go directly to main app
6. **Console Check**: Should see "✅ Existing user with complete profile - skipping setup"

### Test 2: New User Profile Setup  
1. **Fresh Account**: Use a Google account that hasn't used the app before
2. **Login**: Complete Google OAuth
3. **Expected**: Should go to profile setup screen
4. **Console Check**: Should see "📝 New user or incomplete profile - will show setup"

### Test 3: Profile Data Recovery After Issues
1. **Login**: Complete full setup once
2. **Clear Local Data**: Use sign out or manually clear app data
3. **Sign Back In**: Login with same Google account  
4. **Expected**: Profile should be recovered from server automatically
5. **Console Check**: Should see "📥 Server profile data:" and sync success

### Test 4: Debug Tools Usage
1. **Add Debug Component**: Temporarily add `DebugProfileComponent` to any screen
2. **Test Profile Check**: Use "Check Profile Completion" button
3. **Test Server Sync**: Use "Sync from Server" button
4. **View Stored Data**: Use "Show Stored Data" button
5. **Force Setup**: Use "Force Profile Setup" button to test setup flow

## Console Logs to Watch For

### Successful Profile Recovery:
```
=== GOOGLE LOGIN SUCCESS ===
User ID: [user_id]
Email: [email]
Name: [name]
Checking if user needs profile setup...
Backend available, checking server-side profile completion
Server profile check result: {hasProfile: true, hasContacts: true, needsSetup: false}
✅ Existing user with complete profile - skipping setup
```

### Server Profile Sync:
```
🔄 Syncing profile from server for user: [user_id]
📥 Server profile data: {name: "...", phone_number: "...", contacts_loaded: true}
✅ Profile synced successfully from server
```

### New User Setup:
```
=== GOOGLE LOGIN SUCCESS ===
Checking if user needs profile setup...
Primary endpoint not found, trying alternative...
Alternative endpoint also not available
Backend not available, checking local profile completion
Local profile check result: true
📝 New user or incomplete profile - will show setup
```

## Debugging Profile Issues

### Using the Debug Component

Add this to any screen temporarily:

```javascript
import DebugProfileComponent from './DEBUG_PROFILE_COMPONENT';

// In your component JSX:
<DebugProfileComponent />
```

### Debug Functions Available:
- **Check Profile Completion**: Tests the profile completion logic
- **Sync from Server**: Manually syncs profile data from server  
- **Show Stored Data**: Displays all locally stored user data
- **Force Profile Setup**: Forces the setup flow for testing

### Manual Profile Check Command:

```javascript
const { checkProfileCompletion, syncProfileFromServer } = useAuth();

// Check if profile is complete
const needsSetup = await checkProfileCompletion();
console.log('Needs setup:', needsSetup);

// Sync from server
const success = await syncProfileFromServer();
console.log('Sync success:', success);
```

## Troubleshooting Profile Issues

### Issue: Still shows profile setup for existing users
**Debug Steps:**
1. Add debug component and check "Show Stored Data"
2. Use "Sync from Server" to manually retrieve profile
3. Check console for endpoint responses
4. Verify server has the profile data at correct endpoint

### Issue: Profile data not syncing from server
**Check:**
- Server endpoint `/auth/users/profile/{user_id}` or `/auth/user/{user_id}` exists
- Profile data includes `name`, `phone_number`, `contacts_loaded` fields
- Network connectivity and server availability

### Issue: Contacts not preserved
**Check:**  
- Contacts are saved to server via `/contacts/sync` endpoint
- Server returns `contacts_loaded: true` in profile data
- Local contacts stored as fallback

## Expected Behavior After Fixes

1. **First Time User**: Goes through complete profile setup
2. **Returning User**: Profile automatically recovered from server
3. **Network Issues**: Falls back to local data where possible
4. **Server Errors**: Graceful degradation, user stays logged in
5. **Data Persistence**: Profile and contacts preserved across sign-outs

## Quick Debug Checklist

When testing profile persistence:

- [ ] Console shows "✅ Existing user with complete profile" for returning users
- [ ] Debug component "Sync from Server" returns true for existing users
- [ ] Server endpoints return profile data correctly
- [ ] Local storage has user data as fallback
- [ ] Profile setup only shows for genuinely new users

The key improvement is that the app now properly matches profile save/retrieve endpoints and provides better debugging tools to identify any remaining issues. 