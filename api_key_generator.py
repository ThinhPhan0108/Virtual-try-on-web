import requests
from bs4 import BeautifulSoup
import random
import string
import os
import time

# Function to generate a random email address using 1secmail
def generate_email():
    # Get a random domain from 1secmail
    domain_req = requests.get("https://www.1secmail.com/api/v1/?action=getDomain")
    domain = domain_req.json()[0]

    # Generate a random username
    username = ''.join(random.choice(string.ascii_lowercase) for i in range(10))

    email = f"{username}@{domain}"
    return email

# Function to check inbox for a specific email
def check_inbox(email):
    username, domain = email.split("@")
    url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}"
    messages = requests.get(url).json()
    return messages

# Function to register with Pixelcut
def register_pixelcut(email, password):
    # Use requests to submit the registration form
    url = "https://www.pixelcut.ai/register" # Replace with the actual registration URL
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(url, data=data)
    return response

# Function to retrieve the API key (This part needs to be adapted to Pixelcut's actual process)
def retrieve_api_key(email, password):
    # This is a placeholder - you'll need to inspect Pixelcut's site to see how the API key is actually retrieved
    # It might involve logging in and scraping the dashboard, or checking for a confirmation email
    print("Placeholder: Implement API key retrieval from Pixelcut")
    return "YOUR_API_KEY"

# Function to update the app.py file with the new API key
def update_api_key(api_key):
    # Read the app.py file
    with open("app.py", "r") as f:
        content = f.read()

    # Replace the old API key with the new one
    new_content = content.replace(os.getenv("PIXELCUT_API_KEY"), api_key)

    # Write the updated content to the app.py file
    with open("app.py", "w") as f:
        f.write(new_content)

# Main workflow
def main():
    email = generate_email()
    password = ''.join(random.choice(string.ascii_lowercase) for i in range(12))
    print(f"Generated email: {email}, password: {password}")

    # Register with Pixelcut
    response = register_pixelcut(email, password)

    if response.status_code == 200:
        print("Registration successful (potentially - depends on Pixelcut's response)")

        # Wait for a confirmation email (if needed)
        time.sleep(10)  # Adjust as needed

        # Retrieve the API key
        api_key = retrieve_api_key(email, password)

        # Update the app.py file with the new API key
        update_api_key(api_key)
        print("API key retrieval and app.py update complete")
    else:
        print(f"Registration failed with status code: {response.status_code}")

if __name__ == "__main__":
    main()
