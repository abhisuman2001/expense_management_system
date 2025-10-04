import pytesseract
from PIL import Image
import re
from datetime import datetime
from decimal import Decimal
import os
import logging

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        # Set tesseract command path if configured
        tesseract_path = os.environ.get('TESSERACT_CMD_PATH')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_text_from_image(self, image_path):
        """Extract text from image using OCR"""
        try:
            # Open and process image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(image, config='--psm 6')
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return None
    
    def parse_receipt_data(self, text):
        """Parse extracted text to identify expense details"""
        if not text:
            return {}
        
        result = {}
        
        # Extract amount using various patterns
        amount = self._extract_amount(text)
        if amount:
            result['amount'] = amount
        
        # Extract date
        date = self._extract_date(text)
        if date:
            result['date'] = date
        
        # Extract merchant name
        merchant = self._extract_merchant_name(text)
        if merchant:
            result['merchant_name'] = merchant
        
        # Extract possible category keywords
        category = self._extract_category(text)
        if category:
            result['category'] = category
        
        return result
    
    def _extract_amount(self, text):
        """Extract monetary amounts from text"""
        # Common patterns for amounts
        patterns = [
            r'\$\s*(\d+(?:\.\d{2})?)',  # $123.45
            r'(\d+\.\d{2})\s*\$',       # 123.45$
            r'USD\s*(\d+(?:\.\d{2})?)',  # USD 123.45
            r'(\d+(?:\.\d{2})?)\s*USD',  # 123.45 USD
            r'TOTAL\s*[:\-]?\s*\$?\s*(\d+\.\d{2})',  # TOTAL: $123.45
            r'Amount\s*[:\-]?\s*\$?\s*(\d+\.\d{2})',  # Amount: $123.45
            r'(\d+\.\d{2})',  # Just decimal numbers
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = Decimal(match)
                    if 0.01 <= amount <= 999999.99:  # Reasonable range
                        amounts.append(amount)
                except (ValueError, TypeError):
                    continue
        
        # Return the largest amount found (likely the total)
        return max(amounts) if amounts else None
    
    def _extract_date(self, text):
        """Extract dates from text"""
        # Common date patterns
        patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',    # YYYY/MM/DD
            r'(\w{3}\s+\d{1,2},?\s+\d{4})',      # Jan 15, 2023
            r'(\d{1,2}\s+\w{3}\s+\d{4})',        # 15 Jan 2023
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Try to parse the date
                    for date_format in ['%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', 
                                      '%m-%d-%Y', '%d-%m-%Y', '%Y-%m-%d',
                                      '%b %d, %Y', '%d %b %Y']:
                        try:
                            parsed_date = datetime.strptime(match, date_format).date()
                            # Check if date is reasonable (not too far in future/past)
                            if (datetime.now().date() - parsed_date).days <= 365:
                                return parsed_date
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    def _extract_merchant_name(self, text):
        """Extract merchant/restaurant name from text"""
        lines = text.split('\n')
        
        # Usually the merchant name is one of the first few lines
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if line and len(line) > 2:
                # Skip obvious non-merchant lines
                skip_patterns = [
                    r'^\d+$',  # Just numbers
                    r'^[\d\s\-\(\)]+$',  # Phone numbers
                    r'receipt', r'thank you', r'welcome',
                    r'date', r'time', r'total', r'amount'
                ]
                
                should_skip = False
                for pattern in skip_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        should_skip = True
                        break
                
                if not should_skip and len(line) <= 50:
                    return line.title()
        
        return None
    
    def _extract_category(self, text):
        """Determine expense category based on text content"""
        text_lower = text.lower()
        
        category_keywords = {
            'Meals': ['restaurant', 'cafe', 'food', 'dining', 'lunch', 'dinner', 'breakfast', 'meal'],
            'Travel': ['hotel', 'motel', 'flight', 'airline', 'taxi', 'uber', 'lyft', 'train', 'bus'],
            'Internet/Phone': ['telecom', 'mobile', 'internet', 'wifi', 'phone', 'cellular'],
            'Office Supplies': ['office', 'supplies', 'paper', 'printer', 'computer', 'electronics'],
            'Training': ['training', 'education', 'course', 'seminar', 'workshop', 'conference']
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return 'Other'
    
    def process_receipt(self, image_path):
        """Complete receipt processing pipeline"""
        try:
            # Extract text from image
            text = self.extract_text_from_image(image_path)
            if not text:
                return None
            
            # Parse receipt data
            parsed_data = self.parse_receipt_data(text)
            
            # Add extracted text for reference
            parsed_data['extracted_text'] = text
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Receipt processing failed: {str(e)}")
            return None