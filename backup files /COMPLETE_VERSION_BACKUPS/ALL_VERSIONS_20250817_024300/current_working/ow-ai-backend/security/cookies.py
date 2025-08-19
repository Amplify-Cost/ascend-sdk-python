# security/cookies.py
SESSION_COOKIE_NAME = "owai_session"
CSRF_COOKIE_NAME = "owai_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

# If your dashboard runs on a different domain, keep "None".
COOKIE_SAMESITE = "None"   # use "Lax" if strictly same-site
COOKIE_SECURE = True       # must be True in HTTPS/prod
COOKIE_HTTPONLY = True

# Allow bearer tokens temporarily during migration. Turn this OFF after you test.
ALLOW_BEARER_FOR_MIGRATION = True
