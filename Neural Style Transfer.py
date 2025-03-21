# -*- coding: utf-8 -*-
"""
Original file is located at
    https://colab.research.google.com/drive/1XQd8-WQFeJqXueqRC9HLQQr3TM8DA-4i
    
***NEURAL STYLE TRANSFER***

***PRAVEEN KUMAR V***
"""

import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.applications import vgg19
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import Model
from google.colab import files

# Function to upload images in Colab
def upload_image():
    uploaded = files.upload()
    return list(uploaded.keys())[0]

# Upload content and style images
print("Upload the content image:")
content_path = upload_image()
print("Upload the style image:")
style_path = upload_image()


# Function to load and preprocess images
def load_and_process_image(image_path):
    img = load_img(image_path, target_size=(512, 512))
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    return vgg19.preprocess_input(img)

# Function to deprocess the generated image for visualization
def deprocess_image(img):
    img[:, :, 0] += 103.939
    img[:, :, 1] += 116.779
    img[:, :, 2] += 123.68
    img = img[:, :, ::-1]
    return np.clip(img, 0, 255).astype("uint8")

# Load the images
content_image = load_and_process_image(content_path)
style_image = load_and_process_image(style_path)

# Load pre-trained VGG19 model
def get_model():
    vgg = vgg19.VGG19(weights="imagenet", include_top=False)
    vgg.trainable = False

    style_layers = ["block1_conv1", "block2_conv1", "block3_conv1", "block4_conv1", "block5_conv1"]
    content_layers = ["block5_conv2"]

    outputs = [vgg.get_layer(name).output for name in style_layers + content_layers]
    return Model(vgg.input, outputs)

# Compute content loss
def compute_content_loss(base_content, target_content):
    return tf.reduce_mean(tf.square(base_content - target_content))

# Compute Gram matrix for style loss
def gram_matrix(tensor):
    channels = int(tensor.shape[-1])
    vectorized_features = tf.reshape(tensor, [-1, channels])
    gram = tf.matmul(tf.transpose(vectorized_features), vectorized_features)
    return gram / tf.cast(tf.shape(vectorized_features)[0], tf.float32)

# Compute style loss
def compute_style_loss(style, target):
    return tf.reduce_mean(tf.square(gram_matrix(style) - gram_matrix(target)))

# Compute total variation loss
def total_variation_loss(image):
    return tf.reduce_mean(tf.image.total_variation(image))

# Style Transfer function using gradient descent
def neural_style_transfer(content_path, style_path, content_weight=1e4, style_weight=1e-2, tv_weight=30, iterations=50):
    content_image = load_and_process_image(content_path)
    style_image = load_and_process_image(style_path)

    model = get_model()
    style_outputs = model(style_image)[:5]
    content_outputs = model(content_image)[5]

    generated_image = tf.Variable(content_image, dtype=tf.float32)

    optimizer = tf.optimizers.Adam(learning_rate=5.0)

    @tf.function
    def train_step():
        with tf.GradientTape() as tape:
            model_outputs = model(generated_image)
            style_generated_outputs = model_outputs[:5]
            content_generated_output = model_outputs[5]

            style_loss = sum(compute_style_loss(style_generated_outputs[i], style_outputs[i]) for i in range(5))
            content_loss = compute_content_loss(content_generated_output, content_outputs)
            tv_loss = total_variation_loss(generated_image)

            total_loss = content_weight * content_loss + style_weight * style_loss + tv_weight * tv_loss

        grads = tape.gradient(total_loss, generated_image)
        optimizer.apply_gradients([(grads, generated_image)])
        return total_loss

    # Training loop
    for i in range(iterations):
        loss_value = train_step()
        if i % 50 == 0:
            print(f"Iteration {i}, Loss: {loss_value.numpy()}")

    # Convert back to displayable image
    output_image = deprocess_image(generated_image.numpy()[0])
    plt.imshow(output_image)
    plt.axis("off")
    plt.show()

# Run the Neural Style Transfer
neural_style_transfer(content_path, style_path)
