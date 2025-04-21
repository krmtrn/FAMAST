import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap, rgb2hex
from datetime import datetime
import matplotlib.dates as mdates
from matplotlib.patches import Patch
import os
from shapely.geometry import Polygon

# Print current directory for debugging
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")

# Load the European countries shapefile
def load_europe_map():
    try:
        # Try to find the shapefile in a few common locations
        potential_paths = [
            'ne_50m_admin_0_countries.shp',  # Current directory
            './ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp',  # In subdirectory
            '../ne_50m_admin_0_countries.shp',  # Parent directory
        ]
        
        # Add your specific path here if known
        # potential_paths.append('C:/path/to/your/shapefile/ne_50m_admin_0_countries.shp')
        
        for path in potential_paths:
            if os.path.exists(path):
                print(f"Found shapefile at: {path}")
                europe = gpd.read_file(path)
                
                # Filter to only European countries
                european_countries = ['Albania', 'Andorra', 'Austria', 'Belarus', 'Belgium', 
                                     'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Czech Republic', 
                                     'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 
                                     'Hungary', 'Iceland', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 
                                     'Luxembourg', 'Malta', 'Moldova', 'Monaco', 'Montenegro',
                                     'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal', 
                                     'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 
                                     'Spain', 'Sweden', 'Switzerland', 'Ukraine', 'United Kingdom', 
                                     'Vatican City']
                europe = europe[europe['NAME'].isin(european_countries)]
                return europe
        
        # Try downloading directly if file not found locally
        try:
            print("Attempting to download shapefile from Natural Earth...")
            url = "https://naturalearth.s3.amazonaws.com/50m_cultural/ne_50m_admin_0_countries.zip"
            europe = gpd.read_file(url)
            
            # Filter to only European countries
            european_countries = ['Albania', 'Andorra', 'Austria', 'Belarus', 'Belgium', 
                                 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Czech Republic', 
                                 'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 
                                 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 
                                 'Luxembourg', 'Malta', 'Moldova', 'Monaco', 'Montenegro',
                                 'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal', 
                                 'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 
                                 'Spain', 'Sweden', 'Switzerland', 'Ukraine', 'United Kingdom', 
                                 'Vatican City']
            europe = europe[europe['NAME'].isin(european_countries)]
            return europe
        except Exception as download_error:
            print(f"Error downloading shapefile: {download_error}")
            print("Falling back to simplified Europe map...")
            return create_simple_europe_map()
        
        # If we get here, we couldn't find the file
        print("Couldn't find shapefile in any of the expected locations")
        return create_simple_europe_map()
    except Exception as e:
        print(f"Error loading Europe map: {e}")
        return create_simple_europe_map()

def create_simple_europe_map():
    # Create a very simplified Europe outline as a fallback
    print("Creating simplified Europe map as fallback...")
    
    # Super simplified Europe outline
    europe_outline = Polygon([
        (-10, 35), (40, 35), (40, 75), (-10, 75), (-10, 35)
    ])
    
    # Create a GeoDataFrame with this simple polygon
    return gpd.GeoDataFrame({'NAME': ['Europe']}, geometry=[europe_outline], crs="EPSG:4326")

# Load the painting color data from CSV
def load_painting_data(csv_path):
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                print(f"Trying to load CSV with encoding: {encoding}")
                data = pd.read_csv(csv_path, encoding=encoding)
                
                # Ensure required columns exist and handle NaN values
                required_columns = ['year', 'latitude', 'longitude', 'red_pct', 'green_pct', 'blue_pct']
                for col in required_columns:
                    if col not in data.columns:
                        print(f"Warning: Column '{col}' not found in CSV. Creating default values.")
                        if col == 'year':
                            data[col] = 2000  # Default year
                        elif col in ['latitude', 'longitude']:
                            data[col] = 0.0  # Default coordinates
                        else:
                            data[col] = 0.33  # Default color percentage
                    else:
                        # Fill NaN values with reasonable defaults
                        if col == 'year':
                            data[col] = data[col].fillna(2000)
                        elif col in ['latitude', 'longitude']:
                            data[col] = data[col].fillna(0.0)
                        else:
                            data[col] = data[col].fillna(0.33)
                
                # Ensure color values are between 0 and 1
                for col in ['red_pct', 'green_pct', 'blue_pct']:
                    # If values are above 1, assume they're 0-255 scale and normalize
                    if data[col].max() > 1.0:
                        print(f"Normalizing {col} values from 0-255 to 0-1 range")
                        data[col] = data[col] / 255.0
                    
                    # Clip to ensure 0-1 range
                    data[col] = data[col].clip(0.0, 1.0)
                
                # Convert year to integer if needed
                data['year'] = data['year'].astype(int)
                
                # Convert lat/long to points
                geometry = gpd.points_from_xy(data.longitude, data.latitude)
                return gpd.GeoDataFrame(data, geometry=geometry, crs="EPSG:4326")
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error with encoding {encoding}: {e}")
                continue
        
        # If none of the encodings worked
        raise Exception("Could not decode the CSV file with any of the attempted encodings")
        
    except Exception as e:
        print(f"Error loading painting data: {e}")
        # Create sample data for demonstration
        print("Generating sample data for demonstration...")
        years = list(range(1900, 2001, 5))
        sample_data = []
        
        # Generate sample data points across Europe
        for year in years:
            # Paris
            sample_data.append({
                'year': year,
                'latitude': 48.8566,
                'longitude': 2.3522,
                'red_pct': np.random.random(),
                'green_pct': np.random.random(),
                'blue_pct': np.random.random()
            })
            # Berlin
            sample_data.append({
                'year': year,
                'latitude': 52.5200,
                'longitude': 13.4050,
                'red_pct': np.random.random(),
                'green_pct': np.random.random(),
                'blue_pct': np.random.random()
            })
            # Rome
            sample_data.append({
                'year': year,
                'latitude': 41.9028,
                'longitude': 12.4964,
                'red_pct': np.random.random(),
                'green_pct': np.random.random(),
                'blue_pct': np.random.random()
            })
            # London
            sample_data.append({
                'year': year,
                'latitude': 51.5074,
                'longitude': -0.1278,
                'red_pct': np.random.random(),
                'green_pct': np.random.random(),
                'blue_pct': np.random.random()
            })
            # Madrid
            sample_data.append({
                'year': year,
                'latitude': 40.4168,
                'longitude': -3.7038,
                'red_pct': np.random.random(),
                'green_pct': np.random.random(),
                'blue_pct': np.random.random()
            })
        
        df = pd.DataFrame(sample_data)
        geometry = gpd.points_from_xy(df.longitude, df.latitude)
        return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# Interpolate color data to countries
def interpolate_colors_to_countries(painting_data, europe_gdf, year):
    # Filter painting data for the given year
    year_data = painting_data[painting_data['year'] == year]
    
    if len(year_data) == 0:
        print(f"No data found for year {year}, using default colors")
        colored_europe = europe_gdf.copy()
        colored_europe['color'] = '#CCCCCC'  # Default gray for no data
        return colored_europe, None
    
    # Create a copy of the Europe GeoDataFrame to store color information
    colored_europe = europe_gdf.copy()
    
    # For each country, find the nearest painting data points and calculate average color
    countries_with_colors = []
    
    for idx, country in colored_europe.iterrows():
        try:
            # Find paintings within or close to this country
            # For simplicity, we'll use the centroid of the country and find the nearest points
            country_centroid = country.geometry.centroid
            
            # Calculate distances from country centroid to each painting
            distances = []
            for _, painting in year_data.iterrows():
                painting_point = painting.geometry
                try:
                    distance = country_centroid.distance(painting_point)
                    distances.append((distance, painting))
                except Exception as e:
                    print(f"Error calculating distance: {e}")
                    continue
            
            # Sort by distance and take the nearest points (or weight by distance)
            distances.sort(key=lambda x: x[0])
            nearest_paintings = distances[:min(5, len(distances))]  # Take up to 5 nearest paintings
            
            if nearest_paintings:
                # Calculate weighted average color based on distance
                total_weight = 0
                r_weighted_sum = 0
                g_weighted_sum = 0
                b_weighted_sum = 0
                
                for distance, painting in nearest_paintings:
                    # Use inverse distance as weight
                    weight = 1 / (distance + 0.001)  # Add small value to avoid division by zero
                    r_weighted_sum += float(painting['red_pct']) * weight
                    g_weighted_sum += float(painting['green_pct']) * weight
                    b_weighted_sum += float(painting['blue_pct']) * weight
                    total_weight += weight
                
                # Calculate weighted average and handle potential NaN values
                r_avg = min(max(r_weighted_sum / total_weight if total_weight > 0 else 0.5, 0.0), 1.0)
                g_avg = min(max(g_weighted_sum / total_weight if total_weight > 0 else 0.5, 0.0), 1.0)
                b_avg = min(max(b_weighted_sum / total_weight if total_weight > 0 else 0.5, 0.0), 1.0)
                
                # Create a hex color (with safety checks)
                try:
                    if (not np.isnan(r_avg) and not np.isnan(g_avg) and not np.isnan(b_avg) and 
                        0 <= r_avg <= 1 and 0 <= g_avg <= 1 and 0 <= b_avg <= 1):
                        avg_color = rgb2hex((r_avg, g_avg, b_avg))
                    else:
                        print(f"Invalid color values: R={r_avg}, G={g_avg}, B={b_avg}, using default")
                        avg_color = '#CCCCCC'  # Default gray for invalid values
                except Exception as e:
                    print(f"Error converting color to hex: {e}, using default")
                    avg_color = '#CCCCCC'  # Default gray for error cases
                
                # Store the color information
                colored_europe.at[idx, 'color'] = avg_color
                countries_with_colors.append(idx)
            else:
                colored_europe.at[idx, 'color'] = '#CCCCCC'  # Default gray for countries with no data
        except Exception as e:
            print(f"Error processing country: {e}")
            colored_europe.at[idx, 'color'] = '#CCCCCC'  # Default gray for error cases
    
    # Handle case where no countries have color data
    if not countries_with_colors:
        return colored_europe, None
    
    try:
        # Calculate dominant color component for the year
        r_avg = year_data['red_pct'].mean()
        g_avg = year_data['green_pct'].mean()
        b_avg = year_data['blue_pct'].mean()
        
        if not np.isnan(r_avg) and not np.isnan(g_avg) and not np.isnan(b_avg):
            max_component = max(r_avg, g_avg, b_avg)
            
            if max_component == r_avg:
                dominant_color = "Red"
            elif max_component == g_avg:
                dominant_color = "Green"
            else:
                dominant_color = "Blue"
        else:
            dominant_color = None
    except Exception as e:
        print(f"Error calculating dominant color: {e}")
        dominant_color = None
    
    return colored_europe, dominant_color

# Create animation function
def animate_color_usage(painting_data, europe_gdf, output_file='color_usage_animation.mp4'):
    # Get unique years from the data
    years = sorted(painting_data['year'].unique())
    
    if not years:
        print("No years found in the data.")
        return
    
    # Set up the figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Create title and year text objects
    title = ax.set_title('Color Usage in European Paintings (1900-2000)', fontsize=16)
    year_text = ax.text(0.02, 0.02, '', transform=ax.transAxes, fontsize=14, 
                       bbox=dict(facecolor='white', alpha=0.7))
    
    # Create a legend for dominant color
    dominant_color_text = ax.text(0.98, 0.02, '', transform=ax.transAxes, fontsize=14,
                                 ha='right', bbox=dict(facecolor='white', alpha=0.7))
    
    # Create a function to update the plot for each year
    def update_map(frame):
        year = years[frame]
        ax.clear()
        
        # Interpolate colors for this year
        colored_europe, dominant_color = interpolate_colors_to_countries(painting_data, europe_gdf, year)
        
        # Plot the colored map
        colored_europe.plot(ax=ax, color=colored_europe['color'], edgecolor='black', linewidth=0.5)
        
        # Set the title and year text
        ax.set_title('Color Usage in European Paintings (1900-2000)', fontsize=16)
        ax.text(0.02, 0.02, f'Year: {year}', transform=ax.transAxes, fontsize=14,
               bbox=dict(facecolor='white', alpha=0.7))
        
        # Display dominant color for the year
        if dominant_color:
            ax.text(0.98, 0.02, f'Dominant: {dominant_color}', transform=ax.transAxes, fontsize=14,
                   ha='right', bbox=dict(facecolor='white', alpha=0.7))
        
        # Set map extent
        ax.set_xlim(-25, 40)
        ax.set_ylim(35, 75)
        ax.axis('off')
        
        return ax,
    
    # Skip animation and go straight to saving individual frames
    print("Creating a series of PNG images...")
        
    # Create a directory for the frames
    os.makedirs('animation_frames', exist_ok=True)
    
    # Save individual frames
    for i, year in enumerate(years):
        try:
            colored_europe, dominant_color = interpolate_colors_to_countries(painting_data, europe_gdf, year)
            
            fig, ax = plt.subplots(figsize=(15, 10))
            colored_europe.plot(ax=ax, color=colored_europe['color'], edgecolor='black', linewidth=0.5)
            
            ax.set_title('Color Usage in European Paintings (1900-2000)', fontsize=16)
            ax.text(0.02, 0.02, f'Year: {year}', transform=ax.transAxes, fontsize=14,
                bbox=dict(facecolor='white', alpha=0.7))
            
            if dominant_color:
                ax.text(0.98, 0.02, f'Dominant: {dominant_color}', transform=ax.transAxes, fontsize=14,
                    ha='right', bbox=dict(facecolor='white', alpha=0.7))
                
            ax.set_xlim(-25, 40)
            ax.set_ylim(35, 75)
            ax.axis('off')
            
            frame_path = f'animation_frames/frame_{i:03d}_{year}.png'
            plt.savefig(frame_path)
            plt.close()
            print(f"Saved frame for year {year}")
        except Exception as e:
            print(f"Error processing frame for year {year}: {e}")
    
    print("Individual frames saved in 'animation_frames' directory")
    
    # Try to create a GIF from the saved frames using imageio if available
    try:
        import imageio
        print("Attempting to create GIF from frames using imageio...")
        
        frames = []
        frame_files = sorted([f for f in os.listdir('animation_frames') if f.startswith('frame_')])
        
        for frame_file in frame_files:
            frames.append(imageio.imread(os.path.join('animation_frames', frame_file)))
        
        imageio.mimsave('color_usage_animation.gif', frames, duration=0.5)
        print("GIF created as 'color_usage_animation.gif'")
    except Exception as e:
        print(f"Could not create GIF: {e}")
    
    plt.close()

def main():
    # Replace 'your_data.csv' with your actual data file path
    csv_path = 'C:\Users\kyold\Desktop\FAMAST\cax.csv'
    
    # Load the Europe map
    print("Loading Europe map...")
    europe_gdf = load_europe_map()
    
    # Load the painting data
    print("Loading painting data...")
    painting_data = load_painting_data(csv_path)
    
    # Create the animation
    print("Creating animation...")
    animate_color_usage(painting_data, europe_gdf)
    
    print("Done!")

if __name__ == "__main__":
    main()