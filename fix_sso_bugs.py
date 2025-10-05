"""Fix SSO SQL bugs in routes/sso_routes.py"""

with open('routes/sso_routes.py', 'r') as f:
    content = f.read()

# Bug 1: Remove duplicate password parameter in UPDATE (line 342)
content = content.replace(
    '''UPDATE users SET 
                    first_name = :first_name,
                    last_name = :last_name,
                    access_level = :access_level,
                    department = :department,
                    mfa_enabled = :mfa_enabled,
                    status = :status,
                    last_login = :last_login
                WHERE email = :email
            """), {
                "password": hashed_password,

                "email": email,''',
    '''UPDATE users SET 
                    first_name = :first_name,
                    last_name = :last_name,
                    access_level = :access_level,
                    department = :department,
                    mfa_enabled = :mfa_enabled,
                    status = :status,
                    last_login = :last_login
                WHERE email = :email
            """), {
                "email": email,'''
)

# Bug 2: Fix INSERT statement - remove duplicate columns and fix parameters
content = content.replace(
    '''result = db.execute(text("""
                INSERT INTO users (
                    email, password, first_name, last_name, access_level, department,
                    mfa_enabled, status, role, last_login, created_at
                ) VALUES (
                    :email, :password, :first_name, :last_name, :access_level, :department,
                    :mfa_enabled, :status, :role, :last_login, :created_at
                    :email, :first_name, :last_name, :access_level, :department,
                    :mfa_enabled, :status, :role, :last_login, :created_at
                ) RETURNING user_id
            """), {
                "password": hashed_password,

                "email": email,''',
    '''result = db.execute(text("""
                INSERT INTO users (
                    email, password, first_name, last_name, access_level, department,
                    mfa_enabled, status, role, last_login, created_at
                ) VALUES (
                    :email, :password, :first_name, :last_name, :access_level, :department,
                    :mfa_enabled, :status, :role, :last_login, :created_at
                ) RETURNING user_id
            """), {
                "email": email,
                "password": hashed_password,'''
)

# Bug 3: Fix audit log INSERT - remove wrong password parameter
content = content.replace(
    '''INSERT INTO user_audit_logs (
                user_email, action, target, details, ip_address, timestamp
            ) VALUES (:password, 
                :user_email, :action, :target, :details, :ip_address, :timestamp
            )''',
    '''INSERT INTO user_audit_logs (
                user_email, action, target, details, ip_address, timestamp
            ) VALUES (
                :user_email, :action, :target, :details, :ip_address, :timestamp
            )'''
)

# Bug 4: Fix duplicate return statement in create_or_update_sso_user
content = content.replace(
    '''return {
            "user_id": user_id,
                "password": hashed_password,

            "email": email,''',
    '''return {
            "user_id": user_id,
            "email": email,'''
)

with open('routes/sso_routes.py', 'w') as f:
    f.write(content)

print("✅ Fixed SSO SQL bugs")
