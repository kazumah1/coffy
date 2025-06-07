# Authentication Persistence Testing Guide

## Overview
This guide helps you verify that users stay logged in after reloading your iOS app, especially when profiles are saved to the server (not locally).

## Issue Fixed: Server-Side vs Local Profile Storage

### The Problem
- **Simulator**: Profiles saved locally → login persistence worked
- **iPhone**: Profiles saved to server only → login persistence failed
- **Root Cause**: Authentication logic was incorrectly coupled with profile completion checks

### The Solution
- **Separated authentication from profile completion** - users stay logged in regardless of profile status
- **Made profile completion checks non-blocking** - if they fail, user remains authenticated  
- **Improved error handling** - server errors don't log users out
- **Enhanced logging** - easier to debug server vs local profile issues

## Key Changes Made

### 1. Authentication-First Loading
- **Before**: Profile completion check could prevent user from loading
- **After**: User is ALWAYS loaded first, profile check is secondary and optional

### 2. Server-Side Profile Support  
- **Before**: Defaulted to local profile checking
- **After**: Prioritizes server-side profile data with local fallback

### 3. Error Resilience
- **Before**: Any profile check error would disrupt authentication
- **After**: Profile errors are logged but don't affect login state

### 4. Improved Logging
- Added detailed logs to distinguish between server and local profile scenarios
- Easy to debug what's happening on iPhone vs simulator

## Testing Steps

### Test 1: iPhone with Server-Side Profiles
1. **Fresh Install**: Delete and reinstall the app on your actual iPhone
2. **Login**: Complete Google OAuth login  
3. **Check Console**: Should see "User data saved to storage" 
4. **Profile Setup**: Complete profile setup (saves to server)
5. **Check Console**: Should see "Backend available, checking server-side profile completion"
6. **Force Close**: Completely close the app 
7. **Reopen**: Open the app again
8. **Expected**: User should still be logged in, go directly to main app
9. **Check Console**: Should see "Loaded user from storage" and "Server profile check result"

### Test 2: Simulator with Local Profiles  
1. **Fresh Install**: Reset simulator 
2. **Login**: Complete Google OAuth login
3. **Profile Setup**: Complete profile setup (saves locally)
4. **Check Console**: Should see "Backend not available, checking local profile completion"
5. **Force Close**: Close simulator
6. **Reopen**: Open simulator again  
7. **Expected**: User should still be logged in
8. **Check Console**: Should see "Local profile check result"

### Test 3: Network Error Resilience (iPhone)
1. **Login**: Complete login and profile setup on iPhone
2. **Turn off WiFi/Cellular**: Disconnect from internet
3. **Force Close**: Close the app
4. **Reopen**: Open the app again  
5. **Expected**: User should still be logged in (authentication not dependent on profile check)
6. **Check Console**: Should see "Profile completion check failed, user remains logged in"

### Test 4: Server Error Resilience (iPhone)
1. **Login**: Complete login and profile setup
2. **Backend Issue**: If backend returns errors for profile endpoint
3. **Force Close**: Close and reopen app
4. **Expected**: User should still be logged in
5. **Check Console**: Should see "Profile completion check failed with status: [error]"

## Console Logs to Watch For

### iPhone with Server-Side Profiles (Success):
```
=== DEBUG STORED DATA ===
Stored user: {id: "...", email: "...", needsProfileSetup: false}
========================
Loaded user from storage: {id: "...", email: "..."}
Checking profile completion for user: [user_id]
Backend available, checking server-side profile completion
Server profile check result: {hasProfile: true, hasContacts: true, needsSetup: false}
```

### Simulator with Local Profiles (Success):
```
=== DEBUG STORED DATA ===
Stored user: {id: "...", email: "...", needsProfileSetup: false}
Stored profile: {name: "...", phone_number: "..."}
========================
Loaded user from storage: {id: "...", email: "..."}
Backend not available, checking local profile completion
Local profile check result: false
```

### Network Error (Resilient):
```
Loaded user from storage: {id: "...", email: "..."}
Profile completion check failed, user remains logged in: [error details]
```

### Server Error (Resilient):
```
Loaded user from storage: {id: "...", email: "..."}
Profile completion check failed with status: 500
```

## Troubleshooting iPhone-Specific Issues

### Issue: Still logged out on iPhone after server profile setup
**Check:**
- Are you seeing "Server profile check result" in console?
- Is the server returning the correct profile data?
- Are there any network errors affecting the profile endpoint?

**Solution**: Profile check errors should not affect login - user should stay authenticated

### Issue: Profile setup status incorrect on iPhone
**Check:**
- Server endpoint `/auth/user/{user_id}` is working correctly
- Profile data includes `name`, `phone_number`, and `contacts_loaded` fields
- Server is returning proper HTTP status codes

### Issue: Authentication works on simulator but not iPhone  
**Check:**
- Console logs should show "Backend available" on iPhone vs "Backend not available" on simulator
- Server-side profile data should match what's expected
- Network connectivity on iPhone

## Manual Debug Function

Add this to any component to manually test profile completion:

```javascript
const debugProfileCompletion = async () => {
    const { user, checkProfileCompletion } = useAuth();
    if (user?.id) {
        try {
            const needsSetup = await checkProfileCompletion(user.id);
            console.log('Manual profile check result:', needsSetup);
            Alert.alert('Debug', `Profile setup needed: ${needsSetup}`);
        } catch (error) {
            console.error('Manual profile check error:', error);
            Alert.alert('Debug Error', error.message);
        }
    }
};
```

## Expected iPhone Behavior After Fixes

1. **First Install**: User sees login screen
2. **After Login**: User data saved, profile completion checked from server
3. **Profile Setup**: Data saved to server, completion status updated  
4. **App Reload**: User loaded from storage FIRST, then profile status updated from server
5. **Network Errors**: User remains logged in, profile errors are logged but non-blocking
6. **Server Errors**: User remains logged in, graceful error handling

The key improvement is that authentication is now completely separate from profile completion, ensuring users stay logged in on iPhone even when profiles are server-only. 