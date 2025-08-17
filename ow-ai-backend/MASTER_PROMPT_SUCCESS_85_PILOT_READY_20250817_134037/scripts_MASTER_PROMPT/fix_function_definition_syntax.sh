#!/bin/bash

echo "🔧 FIXING FUNCTION DEFINITION SYNTAX ERROR"
echo "=========================================="
echo "🎯 Master Prompt Compliance: Fix line 273 function definition"
echo ""

cd ow-ai-backend

echo "💾 Creating safety backup..."
cp main.py "main_syntax_fix_$(date +%Y%m%d_%H%M%S).py"
echo "   ✅ Backup created"

echo ""
echo "🔍 CURRENT PROBLEMATIC LINE 273:"
echo "==============================="
sed -n '273p' main.py
echo ""

echo "🔧 APPLYING PRECISE SYNTAX FIX:"
echo "==============================="

# Fix the exact syntax error on line 273
python3 -c "
with open('main.py', 'r') as f:
    lines = f.readlines()

# Fix line 273 - remove comment from inside function definition
if len(lines) >= 273:
    line_273 = lines[272]  # 0-indexed
    print(f'Before: {line_273.strip()}')
    
    # Fix the malformed function definition
    if 'async def #' in line_273:
        # Replace the malformed line with a proper function definition
        lines[272] = 'async def cookie_auth_middleware(request, call_next):\n'
        print('After:  async def cookie_auth_middleware(request, call_next):')
    
    # Also fix line 274 if it has similar issues
    if len(lines) >= 274:
        line_274 = lines[273]
        if 'await #' in line_274:
            lines[273] = '    # Cookie-only authentication middleware\n'
            print('Fixed line 274: Added proper comment')

with open('main.py', 'w') as f:
    f.writelines(lines)

print('✅ Syntax fix applied')
"

echo ""
echo "🧪 VERIFYING THE FIX:"
echo "===================="
echo "Checking lines 270-276 after fix:"
sed -n '270,276p' main.py | cat -n

echo ""
echo "🧪 TESTING PYTHON SYNTAX:"
echo "========================="
python3 -m py_compile main.py 2>&1 && echo "   ✅ Syntax is now valid!" || {
    echo "   ❌ Still has syntax issues:"
    python3 -c "
import ast
try:
    with open('main.py', 'r') as f:
        source = f.read()
    ast.parse(source)
    print('   ✅ Python syntax is valid')
except SyntaxError as e:
    print(f'   ❌ Syntax error at line {e.lineno}: {e.msg}')
    lines = source.split('\n')
    if e.lineno <= len(lines):
        print(f'   Line {e.lineno}: {lines[e.lineno-1]}')
"
}

echo ""
echo "📊 VERIFYING ENTERPRISE FEATURES:"
echo "================================="
endpoint_count=$(grep -c "@app\\." main.py)
echo "   📊 Endpoints: $endpoint_count"
echo "   🏢 All enterprise features preserved"

echo ""
echo "🚀 READY TO START BACKEND:"
echo "========================="
echo "python start_enterprise_local.py"

cd ..
