import requests
from flask import current_app
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class CurrencyService:
    @staticmethod
    def get_countries_with_currencies():
        """Fetch all countries with their currencies from REST Countries API"""
        try:
            response = requests.get(
                'https://restcountries.com/v3.1/all?fields=name,currencies',
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch countries data: {str(e)}")
            return None
    
    @staticmethod
    def get_exchange_rate(from_currency, to_currency):
        """Get exchange rate from one currency to another"""
        try:
            if from_currency == to_currency:
                return Decimal('1.0')
            
            # Use ExchangeRate-API
            response = requests.get(
                f'https://api.exchangerate-api.com/v4/latest/{from_currency}',
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('rates', {})
            
            if to_currency not in rates:
                logger.error(f"Exchange rate not found for {from_currency} to {to_currency}")
                return None
            
            return Decimal(str(rates[to_currency]))
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch exchange rate: {str(e)}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing exchange rate data: {str(e)}")
            return None
    
    @staticmethod
    def convert_amount(amount, from_currency, to_currency):
        """Convert amount from one currency to another"""
        try:
            if from_currency == to_currency:
                return amount, Decimal('1.0')
            
            exchange_rate = CurrencyService.get_exchange_rate(from_currency, to_currency)
            if exchange_rate is None:
                return None, None
            
            converted_amount = Decimal(str(amount)) * exchange_rate
            return converted_amount.quantize(Decimal('0.01')), exchange_rate
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting amount: {str(e)}")
            return None, None

class ExternalAPIService:
    @staticmethod
    def get_supported_countries():
        """Get list of supported countries with their currencies"""
        countries_data = CurrencyService.get_countries_with_currencies()
        if not countries_data:
            return []
        
        countries = []
        for country_data in countries_data:
            try:
                country_name = country_data['name']['common']
                currencies = country_data.get('currencies', {})
                
                if currencies:
                    currency_code = list(currencies.keys())[0]
                    currency_name = currencies[currency_code].get('name', currency_code)
                    
                    countries.append({
                        'name': country_name,
                        'currency_code': currency_code,
                        'currency_name': currency_name
                    })
            except (KeyError, IndexError):
                continue
        
        # Sort by country name
        return sorted(countries, key=lambda x: x['name'])
    
    @staticmethod
    def validate_currency(currency_code):
        """Validate if a currency code is supported"""
        try:
            # Test if we can get exchange rates for this currency
            response = requests.get(
                f'https://api.exchangerate-api.com/v4/latest/{currency_code}',
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False