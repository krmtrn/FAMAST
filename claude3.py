import requests
import pandas as pd
import numpy as np
from PIL import Image
from io import BytesIO
import time
import os
from urllib.parse import urlparse
from datetime import datetime
import random
from SPARQLWrapper import SPARQLWrapper, JSON

# Create directories for saving data
os.makedirs('images', exist_ok=True)
os.makedirs('data', exist_ok=True)

def run_wikidata_query(start_year, end_year, limit=100):
    """Run a SPARQL query on WikiData to get European painting data with geospatial information"""
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    
    query = f"""
    SELECT DISTINCT ?artwork ?image ?date ?creationLocationLabel ?coords ?countryLabel
    WHERE {{
      # Only paintings
      ?artwork wdt:P31 wd:Q3305213.  # Q3305213: painting
      
      # Created in a European country
      ?artwork wdt:P495 ?country.  # P495: country of origin
      ?country wdt:P30 wd:Q46.  # Q46: Europe
      
      # Must have an image
      ?artwork wdt:P18 ?image.
      
      # Creation date between specified years
      ?artwork wdt:P571 ?date.
      FILTER(YEAR(?date) >= {start_year} && YEAR(?date) <= {end_year})
      
      # Creation location with coordinates
      ?artwork wdt:P1071 ?creationLocation.  # P1071: location of creation
      ?creationLocation wdt:P625 ?coords.  # P625: coordinate location
      
      # Language services
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,tr". }}
    }}
    ORDER BY ?date
    LIMIT {limit}
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return results["results"]["bindings"]
    except Exception as e:
        print(f"Error running query for {start_year}-{end_year}: {e}")
        return []

def extract_coordinates(coords_str):
    """Extract latitude and longitude from WikiData coordinate format"""
    # WikiData typically returns: Point(longitude latitude)
    try:
        # Remove 'Point(' and ')'
        coords_clean = coords_str.replace('Point(', '').replace(')', '')
        
        # Split into longitude and latitude
        lon, lat = coords_clean.split()
        return float(lat), float(lon)
    except Exception as e:
        print(f"Error extracting coordinates from {coords_str}: {e}")
        return None, None

def download_image(url, timeout=30, max_retries=3):
    """Download image from URL with enhanced headers to bypass restrictions"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://commons.wikimedia.org/',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="91"',
        'sec-ch-ua-mobile': '?0',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }
    
    retries = 0
    while retries < max_retries:
        try:
            # Try to download with enhanced headers
            response = requests.get(url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
            else:
                print(f"Failed to download image: HTTP {response.status_code}")
                
                # For Wikimedia Commons URLs, try to modify the URL to access a thumbnail
                if 'wikimedia.org' in url or 'wikipedia.org' in url:
                    try:
                        # Extract the filename
                        filename = url.split('/')[-1]
                        # Create thumbnail URL
                        thumbnail_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=800"
                        print(f"Trying alternative thumbnail URL: {thumbnail_url}")
                        
                        response = requests.get(thumbnail_url, headers=headers, timeout=timeout)
                        if response.status_code == 200:
                            return Image.open(BytesIO(response.content))
                        else:
                            print(f"Failed to download thumbnail: HTTP {response.status_code}")
                    except Exception as e:
                        print(f"Error getting thumbnail: {e}")
            
            retries += 1
            if retries < max_retries:
                wait_time = 2 ** retries  # Exponential backoff
                print(f"Retrying in {wait_time} seconds... (attempt {retries+1}/{max_retries})")
                time.sleep(wait_time)
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            retries += 1
            if retries < max_retries:
                wait_time = 2 ** retries
                print(f"Retrying in {wait_time} seconds... (attempt {retries+1}/{max_retries})")
                time.sleep(wait_time)
    
    print(f"Failed to download image after {max_retries} attempts")
    return None

def analyze_image_colors(image):
    """Analyze the RGB color distribution in an image"""
    try:
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize for faster processing if image is large
        if max(image.size) > 1000:
            ratio = 1000 / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)
        
        # Get pixel data as numpy array
        pixels = np.array(image)
        
        # Calculate color percentages
        total_pixels = pixels.shape[0] * pixels.shape[1]
        red_sum = pixels[:,:,0].sum()
        green_sum = pixels[:,:,1].sum()
        blue_sum = pixels[:,:,2].sum()
        
        total_color = red_sum + green_sum + blue_sum
        
        # Calculate color percentages (normalized)
        if total_color > 0:
            red_pct = red_sum / total_color
            green_pct = green_sum / total_color
            blue_pct = blue_sum / total_color
        else:
            red_pct = green_pct = blue_pct = 0.33
            
        return {
            'red_pct': red_pct,
            'green_pct': green_pct,
            'blue_pct': blue_pct
        }
    except Exception as e:
        print(f"Error analyzing image colors: {e}")
        return None

def process_artwork_data(results, save_images=False):
    """Process artwork data from WikiData results"""
    data = []
    
    for i, result in enumerate(results):
        try:
            # Extract data from result
            image_url = result.get('image', {}).get('value')
            date_str = result.get('date', {}).get('value')
            coords_str = result.get('coords', {}).get('value')
            location = result.get('creationLocationLabel', {}).get('value', 'Unknown')
            country = result.get('countryLabel', {}).get('value', 'Unknown')
            
            # Skip if missing essential data
            if not image_url or not date_str or not coords_str:
                print("Skipping artwork: Missing essential data")
                continue
                
            # Extract year from date
            year = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').year
            
            # Extract coordinates
            latitude, longitude = extract_coordinates(coords_str)
            if latitude is None or longitude is None:
                print("Skipping artwork: Could not extract coordinates")
                continue
            
            print(f"Processing artwork {i+1}/{len(results)} from {year}: {location}, {country}")
            
            # Try to download and analyze the image
            print(f"Downloading image: {image_url}")
            image = download_image(image_url)
            
            if image is None:
                print(f"Skipping artwork: Could not download image")
                continue
                
            # Analyze colors
            colors = analyze_image_colors(image)
            if colors is None:
                print(f"Skipping artwork: Could not analyze colors")
                continue
                
            print(f"Image analyzed successfully")
            
            # Save image if requested
            if save_images:
                # Create a safe filename from the URL
                filename = os.path.basename(urlparse(image_url).path)
                if not filename:
                    filename = f"artwork_{year}_{i}.jpg"
                
                save_path = os.path.join('images', filename)
                try:
                    image.save(save_path)
                    print(f"Image saved to {save_path}")
                except Exception as e:
                    print(f"Error saving image: {e}")
            
            # Add to data
            artwork_data = {
                'year': year,
                'location': location,
                'country': country,
                'latitude': latitude,
                'longitude': longitude,
                'red_pct': colors['red_pct'],
                'green_pct': colors['green_pct'],
                'blue_pct': colors['blue_pct'],
                'image_url': image_url
            }
            
            data.append(artwork_data)
            
            # Be nice to the server
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"Error processing result: {e}")
            continue
    
    return data

def main():
    all_data = []
    save_path = os.path.join('data', 'european_paintings_color_data.csv')
    
    # Process data in 10-year chunks to avoid timeout
    decades = [(decade, decade+9) for decade in range(1900, 2001, 10)]
    
    for start_year, end_year in decades:
        print(f"\n=== Querying data for {start_year}-{end_year} ===")
        results = run_wikidata_query(start_year, end_year, limit=50)
        
        if results:
            print(f"Found {len(results)} results for {start_year}-{end_year}")
            decade_data = process_artwork_data(results, save_images=False)
            
            if decade_data:
                all_data.extend(decade_data)
                
                # Save intermediate results
                df = pd.DataFrame(all_data)
                df.to_csv(save_path, index=False)
                print(f"Saved {len(all_data)} records to {save_path}")
            else:
                print(f"No valid data processed for {start_year}-{end_year}")
        else:
            print(f"No results found for {start_year}-{end_year}")
        
        # Be extra nice to the server between decade queries
        time.sleep(random.uniform(5, 10))
    
    # Final save
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(save_path, index=False)
        print(f"Completed! Total of {len(all_data)} records saved to {save_path}")
    else:
        print("No data was collected.")

if __name__ == "__main__":
    main()