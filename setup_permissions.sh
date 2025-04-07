#!/bin/bash

# Ethical Scraper Permission Setup Script
# Sets secure permissions (644 for files, 755 for dirs) with verification

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validate we're in project root
check_project_root() {
    if [[ ! -f "main.py" || ! -d "core" ]]; then
        echo -e "${RED}Error: Must run from project root directory${NC}"
        exit 1
    fi
}

set_permissions() {
    echo -e "${YELLOW}Setting directory permissions to 755...${NC}"
    find . -type d -exec chmod 755 {} \;
    
    echo -e "${YELLOW}Setting file permissions to 644...${NC}"
    find . -type f -exec chmod 644 {} \;
    
    echo -e "${YELLOW}Making main.py executable...${NC}"
    chmod +x main.py
}

verify_permissions() {
    local errors=0
    
    echo -e "\n${YELLOW}Verifying permissions...${NC}"
    
    # Check directories
    while IFS= read -r dir; do
        perms=$(stat -c "%a" "$dir")
        if [[ "$perms" != "755" ]]; then
            echo -e "${RED}Bad permissions (${perms}): ${dir}${NC}"
            ((errors++))
        fi
    done < <(find . -type d)
    
    # Check files
    while IFS= read -r file; do
        perms=$(stat -c "%a" "$file")
        if [[ "$file" == "./main.py" ]]; then
            if [[ "$perms" != "755" ]]; then
                echo -e "${RED}main.py should be executable (755)${NC}"
                ((errors++))
            fi
        elif [[ "$perms" != "644" ]]; then
            echo -e "${RED}Bad permissions (${perms}): ${file}${NC}"
            ((errors++))
        fi
    done < <(find . -type f)
    
    if [[ $errors -eq 0 ]]; then
        echo -e "${GREEN}All permissions verified successfully${NC}"
    else
        echo -e "${RED}Found ${errors} permission issues${NC}"
        exit 1
    fi
}

main() {
    check_project_root
    set_permissions
    verify_permissions
    echo -e "${GREEN}Permission setup complete${NC}"
}

main