/**
 * 🏢 Enterprise Authentication Utilities - Master Prompt Compliant
 * Cookie-only authentication with proper API request handling
 */

const API_BASE_URL = '';

/**
 * 🍪 Master Prompt Compliance: Cookie-only authentication
 */
export const loginUser = async (email, password) => {
    console.log('🏢 Enterprise login attempt for:', email);
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'include', // 🍪 Include cookies
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        console.log('🏢 Enterprise login response:', {
            status: response.status,
            headers: Object.fromEntries(response.headers.entries())
        });

        if (!response.ok) {
            // Fallback to URLSearchParams if JSON fails
            const formResponse = await fetch(`${API_BASE_URL}/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                credentials: 'include',
                body: new URLSearchParams({
                    username: email,
                    password: password
                })
            });

            if (!formResponse.ok) {
                const errorText = await formResponse.text();
                throw new Error(`Authentication failed: ${formResponse.status} - ${errorText}`);
            }

            const result = await formResponse.json();
            console.log('✅ Enterprise login successful');
            return result;
        }

        const result = await response.json();
        console.log('✅ Enterprise login successful');
        return result;

    } catch (error) {
        console.error('❌ Enterprise login error:', error);
        throw error;
    }
};

/**
 * 🍪 Get current user via cookie authentication
 */
export const getCurrentUser = async () => {
    console.log('🔍 Checking enterprise authentication status...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            },
            credentials: 'include' // 🍪 Send cookies
        });

        if (!response.ok) {
            console.log('ℹ️ No authentication found, showing login');
            return null;
        }

        const user = await response.json();
        console.log('✅ Enterprise authentication validated');
        return user;

    } catch (error) {
        console.error('❌ Enterprise auth check error:', error);
        return null;
    }
};

/**
 * 🍪 Logout user (clear server-side session)
 */
export const logoutUser = async () => {
    console.log('🔍 Enterprise logout attempt...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });

        console.log('✅ Enterprise logout completed');
        return true;

    } catch (error) {
        console.error('❌ Enterprise logout error:', error);
        return false;
    }
};

/**
 * 🍪 Fetch with authentication (uses cookies) - FIXED FOR API CALLS
 */
export const fetchWithAuth = async (url, options = {}) => {
    console.log('🔍 Making authenticated API request to:', url);
    
    const defaultOptions = {
        credentials: 'include', // 🍪 CRITICAL: Always include cookies
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            ...options.headers
        }
    };

    const finalUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    
    console.log('🔍 API request details:', {
        url: finalUrl,
        method: options.method || 'GET',
        credentials: defaultOptions.credentials
    });

    try {
        const response = await fetch(finalUrl, {
            ...defaultOptions,
            ...options
        });
        
        console.log('📊 API response:', {
            status: response.status,
            url: finalUrl
        });
        
        return response;
    } catch (error) {
        console.error('❌ API request failed:', error);
        throw error;
    }
};

// 🔄 Backward compatibility exports
export const logout = logoutUser;

// Alternative export names for compatibility
export { 
    loginUser as login,
    getCurrentUser as getUser
};

// Default export for comprehensive compatibility
export default {
    loginUser,
    logoutUser,
    getCurrentUser,
    fetchWithAuth,
    // Backward compatibility
    login: loginUser,
    logout: logoutUser,
    getUser: getCurrentUser
};

// 🍪 Master Prompt Compliance: No localStorage usage
// Cookie-only authentication maintained throughout
