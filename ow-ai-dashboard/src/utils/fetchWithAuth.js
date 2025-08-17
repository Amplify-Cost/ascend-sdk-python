/**
 * 🏢 Enterprise Authentication Utilities - Master Prompt Compliant
 * Cookie-only authentication, no localStorage usage
 */

const API_BASE_URL = '';

/**
 * 🍪 Master Prompt Compliance: Cookie-only authentication
 */
export const loginUser = async (email, password) => {
    console.log('🏢 Enterprise login attempt for:', email);
    
    try {
        // 🎯 Master Prompt: Try JSON format first
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
            // If JSON fails, try URLSearchParams format
            console.log('🔄 JSON format failed, trying URLSearchParams...');
            
            const formResponse = await fetch(`${API_BASE_URL}/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                credentials: 'include',
                body: new URLSearchParams({
                    username: email,  // Note: backend might expect 'username' field
                    password: password
                })
            });

            if (!formResponse.ok) {
                const errorText = await formResponse.text();
                throw new Error(`Authentication failed: ${formResponse.status} - ${errorText}`);
            }

            const result = await formResponse.json();
            console.log('✅ Enterprise login successful with URLSearchParams');
            return result;
        }

        const result = await response.json();
        console.log('✅ Enterprise login successful with JSON');
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
 * 🍪 Fetch with authentication (uses cookies)
 */
export const fetchWithAuth = async (url, options = {}) => {
    const defaultOptions = {
        credentials: 'include', // 🍪 Always include cookies
        headers: {
            'Accept': 'application/json',
            ...options.headers
        }
    };

    return fetch(url.startsWith('http') ? url : `${API_BASE_URL}${url}`, {
        ...defaultOptions,
        ...options
    });
};

// 🍪 Master Prompt Compliance: No localStorage usage
// Cookie-only authentication maintained throughout

// 🔄 Backward compatibility exports for existing imports
export const logout = logoutUser;

// Alternative export names for compatibility
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
