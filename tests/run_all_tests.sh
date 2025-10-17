#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}OW-KAI ENTERPRISE TEST SUITE${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Test 1: Cleanup
echo -e "\n${BLUE}[1/3] Running Data Cleanup...${NC}"
python3 cleanup_data.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cleanup failed${NC}"
    exit 1
fi

# Test 2: Authentication
echo -e "\n${BLUE}[2/3] Running Authentication Tests...${NC}"
python3 test_authentication.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Authentication tests failed${NC}"
    exit 1
fi

# Test 3: Check backend health
echo -e "\n${BLUE}[3/3] Checking Backend Health...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" $API_BASE_URL/health)
if [ $response -eq 200 ]; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend returned status $response${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ ALL TESTS COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}\n"
