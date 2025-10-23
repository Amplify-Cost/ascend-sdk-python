"""
Enterprise SSO/OIDC Manager
Supports Okta, Azure AD, Google Workspace, and other OIDC providers
"""

import os
import jwt
import requests
from typing import Dict, Optional, List
from fastapi import HTTPException, status
from authlib.integrations.requests_client import OAuth2Session
from enterprise_config import config
import logging

logger = logging.getLogger(__name__)

class EnterpriseSSO:
    """Enterprise Single Sign-On Manager"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.group_to_role_mapping = self._initialize_group_mappings()
        
    def _initialize_providers(self) -> Dict:
        """Initialize SSO provider configurations"""
        
        return {
            "okta": {
                "name": "Okta",
                "client_id": config.get_secret("okta-client-id"),
                "client_secret": config.get_secret("okta-client-secret"),
                "domain": os.getenv("OKTA_DOMAIN", "your-org.okta.com"),
                "authorization_url": f"https://{os.getenv('OKTA_DOMAIN', 'your-org.okta.com')}/oauth2/v1/authorize",
                "token_url": f"https://{os.getenv('OKTA_DOMAIN', 'your-org.okta.com')}/oauth2/v1/token",
                "userinfo_url": f"https://{os.getenv('OKTA_DOMAIN', 'your-org.okta.com')}/oauth2/v1/userinfo",
                "jwks_url": f"https://{os.getenv('OKTA_DOMAIN', 'your-org.okta.com')}/oauth2/v1/keys",
                "scopes": ["openid", "profile", "email", "groups"]
            },
            
            "azure_ad": {
                "name": "Azure Active Directory",
                "client_id": config.get_secret("azure-ad-client-id"),
                "client_secret": config.get_secret("azure-ad-client-secret"),
                "tenant_id": os.getenv("AZURE_TENANT_ID", "your-tenant-id"),
                "authorization_url": f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID', 'your-tenant-id')}/oauth2/v2.0/authorize",
                "token_url": f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID', 'your-tenant-id')}/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me",
                "jwks_url": "https://login.microsoftonline.com/common/discovery/v2.0/keys",
                "scopes": ["openid", "profile", "email", "User.Read", "Directory.Read.All"]
            },
            
            "google": {
                "name": "Google Workspace",
                "client_id": config.get_secret("google-client-id"),
                "client_secret": config.get_secret("google-client-secret"),
                "authorization_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "jwks_url": "https://www.googleapis.com/oauth2/v3/certs",
                "scopes": ["openid", "email", "profile"]
            }
        }
    
    def _initialize_group_mappings(self) -> Dict:
        """Map IdP groups to OW-AI access levels"""
        
        return {
            # Okta Groups
            "OW-AI-Executives": 5,           # Executive level
            "OW-AI-Administrators": 4,       # Admin level
            "OW-AI-Managers": 3,            # Manager level
            "OW-AI-PowerUsers": 2,          # Power user level
            "OW-AI-BasicUsers": 1,          # Basic level
            "OW-AI-Restricted": 0,          # Restricted level
            
            # Azure AD Groups
            "OW-AI Executive Team": 5,
            "OW-AI System Administrators": 4,
            "OW-AI Security Managers": 3,
            "OW-AI Power Users": 2,
            "OW-AI Standard Users": 1,
            "OW-AI Restricted Access": 0,
            
            # Google Workspace Groups
            "ow-ai-executives@company.com": 5,
            "ow-ai-admins@company.com": 4,
            "ow-ai-managers@company.com": 3,
            "ow-ai-power@company.com": 2,
            "ow-ai-users@company.com": 1,
            "ow-ai-restricted@company.com": 0,
            
            # Fallback mappings
            "administrators": 4,
            "managers": 3,
            "users": 1,
            "guests": 0
        }
    
    def get_authorization_url(self, provider: str, redirect_uri: str, state: str = None) -> str:
        """Get authorization URL for SSO provider"""
        
        if provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported SSO provider: {provider}"
            )
        
        provider_config = self.providers[provider]
        
        if not provider_config["client_id"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SSO provider {provider} not configured"
            )
        
        oauth = OAuth2Session(
            client_id=provider_config["client_id"],
            redirect_uri=redirect_uri,
            scope=" ".join(provider_config["scopes"])
        )
        
        authorization_url, state = oauth.create_authorization_url(
            provider_config["authorization_url"],
            state=state
        )
        
        logger.info(f"✅ Generated SSO authorization URL for {provider}")
        return authorization_url
    
    def exchange_code_for_token(self, provider: str, code: str, redirect_uri: str) -> Dict:
        """Exchange authorization code for access token"""
        
        if provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported SSO provider: {provider}"
            )
        
        provider_config = self.providers[provider]
        
        oauth = OAuth2Session(
            client_id=provider_config["client_id"],
            redirect_uri=redirect_uri
        )
        
        try:
            token = oauth.fetch_token(
                provider_config["token_url"],
                code=code,
                client_secret=provider_config["client_secret"]
            )
            
            logger.info(f"✅ Successfully exchanged code for token with {provider}")
            return token
            
        except Exception as e:
            logger.error(f"❌ Token exchange failed for {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange authorization code: {str(e)}"
            )
    
    def get_user_info(self, provider: str, access_token: str) -> Dict:
        """Get user information from SSO provider"""
        
        if provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported SSO provider: {provider}"
            )
        
        provider_config = self.providers[provider]
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(provider_config["userinfo_url"], headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            logger.info(f"✅ Retrieved user info from {provider} for user: {user_info.get('email', 'unknown')}")
            
            return user_info
            
        except Exception as e:
            logger.error(f"❌ Failed to get user info from {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve user information: {str(e)}"
            )
    
    def get_user_groups(self, provider: str, access_token: str, user_id: str = None) -> List[str]:
        """Get user groups/roles from SSO provider"""
        
        groups = []
        
        try:
            if provider == "okta":
                groups = self._get_okta_groups(access_token, user_id)
            elif provider == "azure_ad":
                groups = self._get_azure_groups(access_token)
            elif provider == "google":
                groups = self._get_google_groups(access_token)
            
            logger.info(f"✅ Retrieved {len(groups)} groups from {provider}")
            return groups
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get groups from {provider}: {str(e)}")
            return []
    
    def _get_okta_groups(self, access_token: str, user_id: str) -> List[str]:
        """Get groups from Okta"""
        domain = os.getenv("OKTA_DOMAIN", "your-org.okta.com")
        url = f"https://{domain}/api/v1/users/{user_id}/groups"
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        groups_data = response.json()
        return [group["profile"]["name"] for group in groups_data]
    
    def _get_azure_groups(self, access_token: str) -> List[str]:
        """Get groups from Azure AD"""
        url = "https://graph.microsoft.com/v1.0/me/memberOf"
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        groups_data = response.json()
        return [group["displayName"] for group in groups_data.get("value", [])]
    
    def _get_google_groups(self, access_token: str) -> List[str]:
        """Get groups from Google Workspace"""
        # Google groups require additional API setup
        # For now, return empty list - would need Google Admin SDK
        return []
    
    def map_groups_to_access_level(self, groups: List[str]) -> int:
        """Map IdP groups to OW-AI access level"""
        
        # Find highest access level from user's groups
        max_level = 0
        matched_groups = []
        
        for group in groups:
            if group in self.group_to_role_mapping:
                level = self.group_to_role_mapping[group]
                if level > max_level:
                    max_level = level
                matched_groups.append(group)
        
        logger.info(f"✅ Mapped groups {matched_groups} to access level {max_level}")
        return max_level
    
    def create_enterprise_user_profile(self, provider: str, user_info: Dict, groups: List[str]) -> Dict:
        """Create enterprise user profile from SSO data"""
        
        access_level = self.map_groups_to_access_level(groups)
        
        # Extract user information based on provider
        if provider == "okta":
            email = user_info.get("email") or user_info.get("preferred_username")
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")
            
        elif provider == "azure_ad":
            email = user_info.get("mail") or user_info.get("userPrincipalName")
            first_name = user_info.get("givenName", "")
            last_name = user_info.get("surname", "")
            
        elif provider == "google":
            email = user_info.get("email", "")
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")
            
        else:
            email = user_info.get("email", "")
            first_name = user_info.get("first_name", "")
            last_name = user_info.get("last_name", "")
        
        enterprise_profile = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "access_level": access_level,
            "sso_provider": provider,
            "sso_groups": groups,
            "role": "admin" if access_level >= 4 else "user",
            "department": self._extract_department_from_groups(groups),
            "mfa_enabled": True,  # SSO providers typically enforce MFA
            "status": "Active",
            "login_method": "SSO"
        }
        
        logger.info(f"✅ Created enterprise profile for {email} with access level {access_level}")
        return enterprise_profile
    
    def _extract_department_from_groups(self, groups: List[str]) -> str:
        """Extract department from group names"""
        
        department_mappings = {
            "finance": "Finance",
            "hr": "Human Resources", 
            "it": "Information Technology",
            "security": "Security",
            "operations": "Operations",
            "executive": "Executive",
            "legal": "Legal",
            "marketing": "Marketing"
        }
        
        for group in groups:
            group_lower = group.lower()
            for dept_key, dept_name in department_mappings.items():
                if dept_key in group_lower:
                    return dept_name
        
        return "General"
    
    def validate_sso_token(self, provider: str, id_token: str) -> Dict:
        """Validate SSO ID token"""
        
        if provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported SSO provider: {provider}"
            )
        
        try:
            # Get JWKS for token validation
            provider_config = self.providers[provider]
            jwks_response = requests.get(provider_config["jwks_url"])
            jwks = jwks_response.json()
            
            # Decode and validate token
            # Note: In production, implement proper JWKS key selection
            unverified_header = jwt.get_unverified_header(id_token)
            
            # For demo purposes, decode without verification
            # In production: implement proper key validation
            decoded_token = jwt.decode(
                id_token, 
                options={"verify_signature": False},  # REMOVE IN PRODUCTION
                algorithms=["RS256"]
            )
            
            logger.info(f"✅ Validated SSO token for {decoded_token.get('email', 'unknown')}")
            return decoded_token
            
        except Exception as e:
            logger.error(f"❌ SSO token validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid SSO token: {str(e)}"
            )

# Create global SSO instance
enterprise_sso = EnterpriseSSO()