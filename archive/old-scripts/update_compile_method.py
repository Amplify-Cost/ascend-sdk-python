with open('services/cedar_enforcement_service.py', 'r') as f:
    content = f.read()

# Find and replace the compile method to add validation
old_compile_start = '''    @staticmethod
    def compile(natural_language: str, risk_level: str = "medium") -> Dict[str, Any]:
        """Convert natural language policy to structured Cedar-style policy"""
        
        text_lower = natural_language.lower()'''

new_compile_start = '''    @staticmethod
    def compile(natural_language: str, risk_level: str = "medium") -> Dict[str, Any]:
        """
        Convert natural language policy to structured Cedar-style policy
        
        Args:
            natural_language: Policy description in plain English
            risk_level: "low", "medium", or "high"
            
        Raises:
            PolicyValidationError: If input is invalid
        """
        # Validate input
        is_valid, errors = PolicyValidator.validate_natural_language(natural_language)
        if not is_valid:
            raise PolicyValidationError(f"Invalid policy: {'; '.join(errors)}")
        
        text_lower = natural_language.lower()'''

content = content.replace(old_compile_start, new_compile_start)

with open('services/cedar_enforcement_service.py', 'w') as f:
    f.write(content)

print("Updated compile() method with validation")
