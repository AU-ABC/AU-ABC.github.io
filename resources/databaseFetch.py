import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Load the Excel file into a pandas dataframe
excel_file = 'downloaded_file.xlsx'
csv_file = 'converted_file.csv'
df = pd.read_excel(excel_file)

# Function to check if a link works
def test_link(link):
    try:
        # Parse the link from the HTML
        soup = BeautifulSoup(link, 'html.parser')
        url = soup.find('a')['href']

        # Test the link
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code == 200:
            return 'Working', datetime.now().strftime('%Y-%m-%d')
        else:
            return 'Not Working', datetime.now().strftime('%Y-%m-%d')
    except Exception:
        return 'Not Working', datetime.now().strftime('%Y-%m-%d')

# Add a new column 'TESTED' with results
df['Tested'], df['Date_tested'] = zip(*df['Link'].apply(test_link))

# Save the updated dataframe to a CSV file
df.to_csv(csv_file, index=False)