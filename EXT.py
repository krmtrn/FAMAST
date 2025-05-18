import extcolors
from PIL import Image
import csv

fotolist = [
    "C:/Users/kyold/Desktop/FAMAST/foto1.jpg",
    "C:/Users/kyold/Desktop/FAMAST/aa.jpg",
    "C:/Users/kyold/Desktop/FAMAST/1.png",
    "C:/Users/kyold/Desktop/FAMAST/bahadir.jpg"


]

# Open a CSV file to save the results
with open("color_analysis.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    # Write the header row
    writer.writerow(["File Name", "Color", "Percentage"])

    for i in range(len(fotolist)):
        img = Image.open(fotolist[i])
        print("NEXT")
        colors, pixel_count = extcolors.extract_from_image(img)
        for color, count in colors:
            percentage = (count / pixel_count) * 100
            if percentage < 10:
                continue
            # Write the data to the CSV file
            writer.writerow([fotolist[i], color, f"{percentage:.2f}%"])
            print(f"Color: {color}, Percentage: {percentage:.2f}%")

