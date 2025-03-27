#!/usr/bin/env python
"""
Script to automatically create test users for the PayLink application.
This script registers 5 different users through the API.
"""
import os
import json
import random
import requests
from datetime import datetime, timedelta
from faker import Faker

# Initialize faker to generate realistic test data
fake = Faker()

# API Configuration
API_BASE_URL = "http://localhost:8000/api"
REGISTER_ENDPOINT = f"{API_BASE_URL}/users/register/"

# Nigerian bank options for realistic data
BANKS = [
    "Access Bank",
    "First Bank",
    "GTBank",
    "UBA",
    "Zenith Bank",
    "Fidelity Bank",
    "Wema Bank",
    "Sterling Bank",
]

# Nigerian states
STATES = [
    "Lagos", "Abuja", "Rivers", "Kano", "Oyo", "Kaduna", "Anambra", 
    "Enugu", "Delta", "Edo", "Ogun", "Ondo", "Plateau", "Borno"
]

# Nigerian telecom networks
NETWORKS = ["MTN", "Airtel", "Glo", "9mobile"]

def generate_phone_number():
    """Generate a random Nigerian phone number"""
    prefix = random.choice(["0803", "0805", "0806", "0807", "0809", "0810", "0813", "0814", "0816", "0703", "0706", "0903"])
    suffix = ''.join(random.choices('0123456789', k=7))
    return f"{prefix}{suffix}"

def generate_account_number():
    """Generate a random 10-digit bank account number"""
    return ''.join(random.choices('0123456789', k=10))

def generate_random_user():
    """Generate random user data for registration"""
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = fake.email()
    
    # Generate a random date of birth for an adult (18-60 years old)
    today = datetime.now()
    days_to_subtract = random.randint(18 * 365, 60 * 365)
    dob = today - timedelta(days=days_to_subtract)
    
    return {
        "email": email,
        "username": f"{first_name.lower()}{random.randint(1, 999)}",
        "password": "TestPassword123!",  # Using a fixed password for all test users
        "password_confirm": "TestPassword123!",
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": generate_phone_number(),
        "date_of_birth": dob.strftime("%Y-%m-%d"),
        "address": fake.address().replace("\n", ", "),
        "state": random.choice(STATES),
        "bank_name": random.choice(BANKS),
        "account_number": generate_account_number(),
        "account_name": f"{first_name} {last_name}",
        "bvn": ''.join(random.choices('0123456789', k=11)),  # Random 11-digit BVN
        "preferred_network": random.choice(NETWORKS)
    }

def create_user(user_data):
    """Create a user through the API"""
    try:
        response = requests.post(REGISTER_ENDPOINT, json=user_data)
        if response.status_code == 201:
            print(f"✅ Successfully created user: {user_data['username']} ({user_data['email']})")
            print(f"   First Name: {user_data['first_name']}")
            print(f"   Last Name: {user_data['last_name']}")
            print(f"   Phone: {user_data['phone_number']}")
            print("   Password: TestPassword123!")
            print("-" * 50)
            return response.json()
        else:
            print(f"❌ Failed to create user: {user_data['username']}")
            print(f"   Status code: {response.status_code}")
            try:
                print(f"   Error: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"   Error: {response.text}")
            print("-" * 50)
            return None
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return None

def main():
    """Main function to create test users"""
    print("=" * 50)
    print("Creating 5 test users for PayLink")
    print("=" * 50)
    
    # Make sure the server is running
    try:
        requests.get(API_BASE_URL)
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server.")
        print(f"   Please make sure the server is running at {API_BASE_URL}")
        print("   You can start it with: python manage.py runserver")
        return
    
    # Create users
    successful_users = []
    print("\nCreating users...\n")
    
    for i in range(5):
        user_data = generate_random_user()
        result = create_user(user_data)
        if result:
            successful_users.append({
                "email": user_data["email"],
                "username": user_data["username"],
                "password": "TestPassword123!"
            })
    
    # Summary
    print("\nSummary:")
    print(f"Successfully created {len(successful_users)} out of 5 users.")
    
    if successful_users:
        print("\nUser credentials for login:")
        for i, user in enumerate(successful_users, 1):
            print(f"{i}. {user['email']} / TestPassword123!")

if __name__ == "__main__":
    main()
