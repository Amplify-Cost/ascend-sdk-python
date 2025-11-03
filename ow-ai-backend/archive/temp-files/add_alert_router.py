import os

print("Adding alert router to main.py...")

# Read main.py
with open("main.py", "r") as f:
    content = f.read()

# Check if alert router already imported
if "from routes.alerts_router import router as alerts_router" not in content:
    # Find the import section
    import_section_end = content.find("app = FastAPI")
    
    # Add the import
    new_import = "from routes.alerts_router import router as alerts_router\n"
    content = content[:import_section_end] + new_import + content[import_section_end:]
    
    # Find where to add the router
    router_section = content.find("# Include routers")
    if router_section == -1:
        router_section = content.find("app.include_router(health_router")
    
    # Add the router registration
    router_registration = "\napp.include_router(alerts_router, prefix='/api')\n"
    
    # Insert after the first router registration
    insert_pos = content.find("\n", router_section) + 1
    content = content[:insert_pos] + router_registration + content[insert_pos:]
    
    # Write back
    with open("main.py", "w") as f:
        f.write(content)
    
    print("✅ Alert router added to main.py")
else:
    print("Alert router already registered")
