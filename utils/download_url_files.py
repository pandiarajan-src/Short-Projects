"""
This module provides functionality to download files and subfolders recursively from a given URL.
"""

import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

def download_files(url, save_dir):
    """
    Downloads files and subfolders recursively from a given URL.

    Args:
        url (str): The URL to download files from.
        save_dir (str): The directory where the downloaded files will be saved.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP request.

    Example:
        download_files("http://example.com/files", "/path/to/save_dir")
    """
    print(f"Starting download from {url} to {save_dir}")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, "html.parser")

        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        print(f"Created directory {save_dir}")

        # Download files
        for link in soup.find_all("a"):
            href = link.get("href")
            if href:
                if href.startswith("/"):
                    # Handle relative links
                    full_url = urllib.parse.urljoin(url, href)
                elif href.startswith("http"):
                    full_url = href
                else:
                    # Handle relative paths that do not start with a /
                    full_url = urllib.parse.urljoin(url, "/" + href)

                if full_url.startswith(url):  # Only download items from the base URL.
                    if full_url != url + "/":  # Prevent infinite loops.
                        if not full_url.endswith("/"):  # If a file, download it.
                            try:
                                print(f"Downloading file from {full_url}")
                                file_response = requests.get(full_url, stream=True)
                                file_response.raise_for_status()
                                filename = os.path.join(save_dir, full_url.split("/")[-1])
                                with open(filename, "wb") as f:
                                    for chunk in file_response.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                print(f"Downloaded: {full_url}")
                            except requests.exceptions.RequestException as e:
                                print(f"Error downloading {full_url}: {e}")
                        else:  # If a folder, recurse.
                            sub_dir = os.path.join(save_dir, full_url[len(url):].strip("/"))
                            print(f"Recursing into directory {sub_dir}")
                            download_files(full_url, sub_dir)

    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")

# Example Usage:
def is_valid_url(url):
    """Check if the URL is valid using a regex pattern."""
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def is_valid_directory(directory):
    """Check if the directory is a valid path."""
    return os.path.isdir(directory) or not os.path.exists(directory)

BASE_URL = input("Enter the URL to download files from: ")
while not is_valid_url(BASE_URL):
    print("Invalid URL. Please enter a valid URL.")
    BASE_URL = input("Enter the URL to download files from: ")

SAVE_DIRECTORY = input("Enter the directory to save the downloaded files: ")
while not is_valid_directory(SAVE_DIRECTORY):
    print("Invalid directory. Please enter a valid directory path.")
    SAVE_DIRECTORY = input("Enter the directory to save the downloaded files: ")

# Create save directory if it doesn't exist
os.makedirs(SAVE_DIRECTORY, exist_ok=True)
print(f"Save directory {SAVE_DIRECTORY} created")

download_files(BASE_URL, SAVE_DIRECTORY)
