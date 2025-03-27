import requests
import uuid
from django.conf import settings
import logging
import json
import time

logger = logging.getLogger(__name__)

class VTPassService:
    """
    Service class to interact with the VTPass API.
    Uses the sandbox environment for testing.
    """
    def __init__(self):
        self.base_url = settings.VTPASS_BASE_URL
        self.api_key = settings.VTPASS_API_KEY
        self.public_key = settings.VTPASS_PUBLIC_KEY
        self.secret_key = settings.VTPASS_SECRET_KEY
    
    def _get_headers(self, is_post=True):
        """Return the appropriate headers for VTPass API requests"""
        headers = {
            'api-key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # For GET requests, use the public key
        # For POST requests, use the secret key
        if is_post:
            headers['secret-key'] = self.secret_key
        else:
            headers['public-key'] = self.public_key
            
        # Add additional logging to debug header issues
        logger.info(f"API Key: {self.api_key[:5]}...{self.api_key[-5:]}")
        if is_post:
            logger.info(f"Secret Key: {self.secret_key[:5]}...{self.secret_key[-5:]}")
        else:
            logger.info(f"Public Key: {self.public_key[:5]}...{self.public_key[-5:]}")
            
        return headers
    
    def _make_get_request(self, endpoint, params=None):
        """Make a GET request to the VTPass API"""
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers(is_post=False)
        
        try:
            logger.info(f"Making GET request to VTPass API: {url}")
            logger.info(f"Headers: {json.dumps(headers)}")
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"VTPass API response status: {response.status_code}")
            logger.info(f"VTPass API response: {response.text}")
            
            # Handle potential API errors
            if response.status_code == 401:
                return {
                    "code": "error",
                    "response_description": "Invalid VTPass API credentials. Please check your API keys.",
                    "data": {}
                }
            elif response.status_code != 200:
                return {
                    "code": "error", 
                    "response_description": f"VTPass API error: {response.status_code}", 
                    "data": {}
                }
                
            return response.json()
        except Exception as e:
            logger.error(f"Error making GET request to VTPass API: {str(e)}")
            return {"code": "error", "response_description": str(e), "data": {}}
    
    def _make_post_request(self, endpoint, data, max_retries=0, current_retry=0):
        """
        Make a POST request to the VTPass API
        
        Args:
            endpoint: API endpoint to call
            data: Request data
            max_retries: Maximum number of retries for error code 016 (default 0)
            current_retry: Current retry attempt (used internally)
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers(is_post=True)
        
        try:
            # Very detailed debug logging
            print("=== VTPASS API REQUEST ===")
            print(f"URL: {url}")
            print(f"Headers: {headers}")
            print(f"Data: {data}")
            
            # Check specifically for billersCode
            if 'billersCode' in data:
                print(f"billersCode is included: {data['billersCode']}")
            else:
                print("billersCode is NOT in the request data!")
                
            # Check for other formats
            if 'billerscode' in data:
                print(f"billerscode (lowercase) is included: {data['billerscode']}")
            if 'billers_code' in data:
                print(f"billers_code (snake_case) is included: {data['billers_code']}")
                
            logger.info(f"Making POST request to VTPass API: {url}")
            logger.info(f"Headers: {json.dumps(headers)}")
            logger.info(f"Data: {json.dumps(data)}")
            response = requests.post(url, headers=headers, json=data)
            logger.info(f"VTPass API response status: {response.status_code}")
            logger.info(f"VTPass API response: {response.text}")
            
            # Handle potential API errors
            if response.status_code == 401:
                return {
                    "code": "error",
                    "response_description": "Invalid VTPass API credentials. Please check your API keys.",
                    "data": {}
                }
            elif response.status_code != 200:
                return {
                    "code": "error", 
                    "response_description": f"VTPass API error: {response.status_code}", 
                    "data": {}
                }
                
            # Try to parse the JSON response
            response_data = response.json()
            
            # Enhanced handling for specific VTPass error codes
            if response_data.get('code') == '016':
                logger.warning(f"VTPass transaction failed with code 016: {response_data}")
                # Code 016 is a transaction failure which can happen for various reasons:
                # - Network connectivity issues with the telco
                # - Invalid recipient number
                # - Service temporarily unavailable
                # - Transaction limits reached
                
                # If automatic retry is enabled and we haven't exceeded max retries
                if max_retries > 0 and current_retry < max_retries:
                    logger.info(f"Automatic retry attempt {current_retry + 1} of {max_retries} for error code 016")
                    
                    # Generate a new request_id to avoid duplicate transaction errors
                    if 'request_id' in data:
                        data['request_id'] = f"{data['request_id']}-retry-{current_retry + 1}"
                    
                    # Wait a short time before retrying (exponential backoff)
                    time.sleep(2 ** current_retry)  # 1s, 2s, 4s, 8s for retries 0-3
                    
                    # Retry the request
                    return self._make_post_request(endpoint, data, max_retries, current_retry + 1)
                
                # Add more context to the error for frontend handling
                response_data['vtpass_error_code'] = '016'
                response_data['error_type'] = 'TRANSACTION_FAILED'
                response_data['possible_causes'] = [
                    'Network connectivity issues with the mobile operator',
                    'Invalid recipient number',
                    'Service temporarily unavailable',
                    'Transaction limits reached'
                ]
                response_data['retry_recommended'] = True
            elif response_data.get('code') == '014':
                logger.warning(f"VTPass API returned insufficient funds error: {response_data}")
                # Code 014 is often used for insufficient funds
                response_data['vtpass_error_code'] = '014'
                response_data['error_type'] = 'INSUFFICIENT_FUNDS'
                response_data['retry_recommended'] = False
            elif response_data.get('code') == '009':
                logger.warning(f"VTPass API returned duplicate request error: {response_data}")
                # Code 009 is often used for duplicate requests
                response_data['vtpass_error_code'] = '009'
                response_data['error_type'] = 'DUPLICATE_REQUEST'
                response_data['retry_recommended'] = True  # Can retry with a new request_id
            
            return response_data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response from VTPass API: {str(e)}, Response: {response.text}")
            return {
                "code": "error", 
                "response_description": "Invalid JSON response from VTPass API", 
                "raw_response": response.text
            }
        except Exception as e:
            logger.error(f"Error making POST request to VTPass API: {str(e)}")
            return {"code": "error", "response_description": str(e), "data": {}}
    
    def get_user_balance(self):
        """Get the current balance for the VTPass account"""
        try:
            # First try the real API
            response = self._make_get_request('balance')
            if response.get("code") == "error":
                # If real API fails, return a mock balance for testing
                return {
                    "code": "success",
                    "response_description": "Mock balance retrieved successfully",
                    "data": {
                        "balance": "1000.00"
                    }
                }
            return response
        except Exception as e:
            logger.error(f"Error getting VTPass balance: {str(e)}")
            # Return a mock balance for testing
            return {
                "code": "success",
                "response_description": "Mock balance retrieved successfully",
                "data": {
                    "balance": "1000.00"
                }
            }
    
    def verify_service_available(self, service_id):
        """Verify if a particular service is available"""
        return self._make_get_request('service-variations', params={'serviceID': service_id})
    
    def purchase_service(self, service_id, variation_code, amount, phone, email, request_id=None, auto_retry=False, **additional_params):
        """
        Purchase a service through VTPass API
        
        Args:
            service_id: The service ID (e.g., 'mtn', 'airtel', etc.)
            variation_code: The variation code for the service
            amount: The amount to purchase
            phone: The recipient's phone number
            email: The email address to receive receipt
            request_id: A unique request ID (generated if not provided)
            auto_retry: Whether to automatically retry on error code 016 (default False)
            **additional_params: Additional parameters like billersCode for specific services
        
        Returns:
            API response from VTPass
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
            
        data = {
            'serviceID': service_id,
            'amount': amount,
            'phone': phone,
            'email': email,
            'request_id': request_id
        }
        
        if variation_code:
            data['variation_code'] = variation_code
        
        # Direct handling for JAMB service
        if service_id.lower() == 'jamb':
            # Get billersCode from various possible formats
            billers_code = (
                additional_params.get('billersCode') or 
                additional_params.get('billerscode') or 
                additional_params.get('billers_code')
            )
            
            if billers_code:
                # Set it in all formats to maximize chance of success
                data['billersCode'] = billers_code  # Exact format from docs
                
                # Log special handling for JAMB
                print(f"Special handling for JAMB: Added billersCode={billers_code}")
        
        # Add any additional parameters needed for specific services (like billersCode for JAMB)
        for key, value in additional_params.items():
            if value:  # Only add non-empty values
                data[key] = value
                
        # Log all parameters being sent to VTPass
        logger.info(f"Sending to VTPass: {json.dumps(data)}")
            
        # Number of automatic retries to perform for error code 016
        max_retries = 2 if auto_retry else 0
            
        return self._make_post_request('pay', data, max_retries=max_retries)
    
    def verify_transaction(self, request_id):
        """Verify the status of a transaction using its request ID"""
        return self._make_get_request('requery', params={'request_id': request_id})
    
    def get_services(self, service_type):
        """
        Get all available services by type
        
        Args:
            service_type: The type of service (e.g., 'airtime', 'data', 'electricity', etc.)
        
        Returns:
            List of available services
        """
        try:
            # First try the real API
            response = self._make_get_request(service_type)
            if response.get("code") == "error":
                # If real API fails, return mock services for testing
                return {
                    "code": "success",
                    "response_description": f"Mock {service_type} services retrieved successfully",
                    "content": self._get_mock_services(service_type)
                }
            return response
        except Exception as e:
            logger.error(f"Error getting {service_type} services: {str(e)}")
            # Return mock services for testing
            return {
                "code": "success",
                "response_description": f"Mock {service_type} services retrieved successfully",
                "content": self._get_mock_services(service_type)
            }
    
    def _get_mock_services(self, service_type):
        """Return mock services for testing"""
        if service_type == "airtime":
            return [
                {"id": "mtn", "name": "MTN", "description": "MTN Airtime"},
                {"id": "airtel", "name": "Airtel", "description": "Airtel Airtime"},
                {"id": "glo", "name": "Glo", "description": "Glo Airtime"},
                {"id": "9mobile", "name": "9mobile", "description": "9mobile Airtime"}
            ]
        elif service_type == "data":
            return [
                {"id": "mtn-data", "name": "MTN Data", "description": "MTN Data Bundle", "variations": [
                    {"variation_code": "mtn-1gb", "name": "1GB", "amount": "1000.00"},
                    {"variation_code": "mtn-2gb", "name": "2GB", "amount": "2000.00"}
                ]},
                {"id": "airtel-data", "name": "Airtel Data", "description": "Airtel Data Bundle", "variations": [
                    {"variation_code": "airtel-1gb", "name": "1GB", "amount": "1000.00"},
                    {"variation_code": "airtel-2gb", "name": "2GB", "amount": "2000.00"}
                ]}
            ]
        elif service_type == "electricity":
            return [
                {"id": "ikeja-electric", "name": "Ikeja Electric", "description": "Ikeja Electric Postpaid"},
                {"id": "eko-electric", "name": "Eko Electric", "description": "Eko Electric Prepaid"}
            ]
        else:
            return []
        
    def create_vtpass_account(self, user):
        """
        Create a VTPass test account for a user
        Note: This is a mock method since the actual API doesn't have this functionality
        In a real implementation, we might create an account on VTPass through their API
        
        Args:
            user: The User instance to create a VTPass account for
            
        Returns:
            Mock response with account ID and initial balance
        """
        # Generate a mock VTPass account ID
        vtpass_account_id = f"VT-{str(uuid.uuid4())[:8]}"
        
        # Update the user with the mock VTPass account details
        user.vtpass_account_id = vtpass_account_id
        user.vtpass_balance = 1000.00  # Start with initial balance
        user.save()
        
        return {
            "code": "success",
            "response_description": "VTPass test account created successfully",
            "data": {
                "account_id": vtpass_account_id,
                "balance": "1000.00"
            }
        }
