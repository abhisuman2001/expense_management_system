def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Password must be at least 8 characters long and contain at least:
    - One uppercase letter
    - One lowercase letter  
    - One digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    return True, "Valid password"

def sanitize_string(text, max_length=None):
    """Remove potentially harmful characters and limit length"""
    if not text:
        return ""
    
    # Remove HTML tags and script tags
    import re
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Limit length
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()