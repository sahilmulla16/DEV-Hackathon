from PIL import Image, ImageDraw

# Create a blank image with white background
width, height = 200, 200
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

# Draw a simple cat face
# Cat face (circle)
draw.ellipse((50, 50, 150, 150), outline='black', fill='gray')

# Left ear
draw.polygon([(70, 60), (90, 30), (110, 60)], outline='black', fill='gray')

# Right ear
draw.polygon([(110, 60), (130, 30), (150, 60)], outline='black', fill='gray')

# Left eye
draw.ellipse((80, 80, 95, 95), fill='white')
draw.ellipse((85, 85, 90, 90), fill='black')

# Right eye
draw.ellipse((120, 80, 135, 95), fill='white')
draw.ellipse((125, 85, 130, 90), fill='black')

# Nose
draw.polygon([(100, 105), (95, 115), (105, 115)], fill='pink')

# Mouth
draw.line([(100, 115), (100, 125)], fill='black')
draw.line([(100, 125), (90, 130)], fill='black')
draw.line([(100, 125), (110, 130)], fill='black')

# Save the image
image.save('cat_image.png')

print('Cat image generated and saved as cat_image.png')