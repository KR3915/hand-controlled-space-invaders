import pandas as pd
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

# Load the dataset
df = pd.read_csv('../data/numbers/gestures-snake.csv', header=None)

if len(df) < 2:
    print("Not enough data to train the model. Please capture more gestures.")
else:
    # Separate features and labels
    y = df.iloc[:, 0].values
    handedness = df.iloc[:, 1].values
    landmarks = df.iloc[:, 2:].values

    # Encode labels and handedness
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)
    handedness = label_encoder.fit_transform(handedness)

    # Reshape landmarks to (num_samples, 1, 6, 7)
    landmarks = landmarks.reshape(-1, 1, 6, 7)

    # Convert to PyTorch tensors
    X_landmarks = torch.tensor(landmarks, dtype=torch.float32)
    X_handedness = torch.tensor(handedness, dtype=torch.float32).unsqueeze(1)
    y = torch.tensor(y, dtype=torch.long)

    # Split data into training and testing sets
    X_landmarks_train, X_landmarks_test, X_handedness_train, X_handedness_test, y_train, y_test = train_test_split(
        X_landmarks, X_handedness, y, test_size=0.2, random_state=42
    )

    # Create TensorDatasets and DataLoaders
    train_dataset = TensorDataset(X_landmarks_train, X_handedness_train, y_train)
    test_dataset = TensorDataset(X_landmarks_test, X_handedness_test, y_test)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

from src.MediPipeHandsModule.CNNModel import CNN

    # Instantiate the model, loss function, and optimizer
    num_classes = len(np.unique(y))
    model = CNN(num_classes=num_classes)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Training loop
    num_epochs = 20
    for epoch in range(num_epochs):
        for landmarks, handedness, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(landmarks, handedness)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

    # Evaluation
    model.eval()
    with torch.no_grad():
        correct = 0
        total = 0
        for landmarks, handedness, labels in test_loader:
            outputs = model(landmarks, handedness)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    print(f'Accuracy of the model on the test set: {accuracy:.2f}%')

    # Save the model
    joblib.dump(model, '../models/gesture_model_cnn.pkl')
    print('Saved CNN gesture model.')
