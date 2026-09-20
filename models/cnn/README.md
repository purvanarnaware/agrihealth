---
language: en
tags:
  - image-classification
  - plant-disease
  - pytorch
  - computer-vision
license: mit
---

# 🌿 Plant Disease Classifier

A CNN model trained on the PlantVillage dataset to classify plant leaf diseases.

## Model Details
- **Architecture**: Custom CNN (4 convolutional blocks)
- **Classes**: 38 plant disease categories
- **Best Validation Accuracy**: 98.27%
- **Training Framework**: PyTorch
- **GPU Used**: NVIDIA RTX 4070 Laptop

## Dataset
Trained on [PlantVillage Dataset](https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset)
containing 54,000+ images of healthy and diseased plant leaves.

## Usage
```python
import torch
from torchvision import transforms
from PIL import Image
import json

# Load class names
with open("class_names.json") as f:
    class_names = json.load(f)

# Load model
checkpoint = torch.load("best_model.pth", map_location="cpu")

# Preprocess image
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

image = Image.open("your_leaf.jpg").convert("RGB")
tensor = transform(image).unsqueeze(0)  # add batch dimension

# Predict
with torch.no_grad():
    outputs = model(tensor)
    _, predicted = outputs.max(1)
    print(f"Prediction: {class_names[predicted.item()]}")
```
