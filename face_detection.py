'''
@file face_detection.py
Backend processing to detect faces, align them, resize and compare them.
'''
import logging
import traceback
import os
import cv2
#import sys
import hashlib
import numpy as np
print("Loading MTCNN Face Recognition...")
from mtcnn import MTCNN
print("MTCNN Face Recognition loaded.")
from scipy.spatial import distance
from tensorflow.keras.applications.resnet import ResNet152, preprocess_input
from PIL import Image
import PIL.ExifTags


def is_hidden(filepath):

    """ 
    Check if a given filepath corresponds to a hidden file.
    For UNIX-like systems, a file is considered hidden if its name starts with a dot.
    For Windows, the function checks for the FILE_ATTRIBUTE_HIDDEN attribute.
    """
    try:
        # For Windows
        import os
        import ctypes

        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(filepath))
        assert attrs != -1

        result = attrs & 2  # FILE_ATTRIBUTE_HIDDEN = 2

        # If the path has the FILE_ATTRIBUTE_HIDDEN attribute set, it's hidden
        if result:
            return True

    except (ImportError, AttributeError, AssertionError):
        # For UNIX-like systems
        # If the basename of the path starts with a dot, it's hidden
        if os.path.basename(filepath).startswith('.'):
            return True

    return False

try:
    logging.basicConfig(filename=r'.\debug.log',
                        filemode='w',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.debug('Logging setup successful')
    print("Logging setup1 successful.")
except Exception as e:
    print(f"Logging setup failed: {str(e)}")

logger = logging.getLogger()

output_folder = "./output/"
face_detector = MTCNN()
print("Initialising Resnet models...")
resnet_model = ResNet152(weights='imagenet', include_top=False)
print('Resnet models initialized successfully.')

# Create output directory if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def is_valid_image_extension(file_path):
    """ 
    Check if the given file path has a valid image extension.
    """
    valid_extensions = ['.png', '.jpeg', '.jpg', '.bmp']
    ext = os.path.splitext(file_path)[-1].lower()
    return ext in valid_extensions


def convert_to_decimal(coord, direction):
    """ 
    Convert GPS coordinates to decimal format.
    """
    degrees, minutes, seconds = coord
    decimal = degrees + minutes / 60 + seconds / 3600
    if direction in ['S', 'W']:
        decimal *= -1
    return float(decimal)

def get_image_exif_data(image_path):
    """
    Extract EXIF data from the provided image path.
    """
    try:
        img_obj = Image.open(image_path)
        exif_data = img_obj._getexif()
        
        if exif_data is not None:
            desired_fields = ["Make", "Model", "DateTimeDigitized", "GPSInfo"]
            exif_info = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in exif_data.items()
                if k in PIL.ExifTags.TAGS and PIL.ExifTags.TAGS[k] in desired_fields
            }
            
            if 'DateTimeDigitized' in exif_info:
                date_time = exif_info.pop('DateTimeDigitized')  # Pop returns the value and removes the key
                date, time = date_time.split()
                exif_info['DateDigitized'] = date
                exif_info['TimeDigitized'] = time

            if 'GPSInfo' in exif_info:
                gps_info = exif_info['GPSInfo']
                lat = round(convert_to_decimal(gps_info[2], gps_info[1]), 6)
                lon = round(convert_to_decimal(gps_info[4], gps_info[3]), 6)
                exif_info['GPSInfo'] = {'Latitude': lat, 'Longitude': lon}
                
            print(f"EXIF data for {image_path}: {exif_info}")
            return exif_info
        else:
            return {}
    except Exception as e:
        logger.exception(f'Error while reading EXIF data from {image_path}')
        return {}

def align_face(face_img, left_eye, right_eye):
    """
    Align the face image such that the eyes are horizontally aligned.
    """
    # Calculate the angle between the two eyes
    dx = right_eye[0] - left_eye[0]
    dy = right_eye[1] - left_eye[1]
    angle = np.degrees(np.arctan2(dy, dx))
    
    # Get the center of the face
    center_y, center_x = np.round(np.array(face_img.shape[:2]) / 2).astype(int)
    
    # Convert numpy.int32 to native int
    center = (int(center_x), int(center_y))
    
    # Rotate the face image to align the eyes horizontally
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1)
    aligned_face = cv2.warpAffine(face_img, rot_mat, face_img.shape[:2][::-1], flags=cv2.INTER_LINEAR)
    
    return aligned_face

def resize_image_with_aspect_ratio(img, size):
    """
    Resize an image while maintaining its aspect ratio.
    """
    try:
        # Get the aspect ratio
        aspect_ratio = img.shape[1] / img.shape[0]
        target_aspect_ratio = size[1] / size[0]

        # If the aspect ratios are equal, we don't need to do anything
        if aspect_ratio == target_aspect_ratio:
            return cv2.resize(img, size)
        elif aspect_ratio < target_aspect_ratio:
            # If the aspect ratio of the image is less than the target aspect ratio
            # then we need to add padding to the width
            scale_factor = size[0] / img.shape[0]
            new_width = int(img.shape[1] * scale_factor)
            rescaled_img = cv2.resize(img, (new_width, size[0]))
            pad_width = size[1] - new_width
            left_pad = pad_width // 2
            right_pad = pad_width - left_pad
            padded_img = cv2.copyMakeBorder(rescaled_img, 0, 0, left_pad, right_pad, cv2.BORDER_CONSTANT, value=0)
        else:
            # If the aspect ratio of the image is greater than the target aspect ratio
            # then we need to add padding to the height
            scale_factor = size[1] / img.shape[1]
            new_height = int(img.shape[0] * scale_factor)
            rescaled_img = cv2.resize(img, (size[1], new_height))
            pad_height = size[0] - new_height
            top_pad = pad_height // 2
            bottom_pad = pad_height - top_pad
            padded_img = cv2.copyMakeBorder(rescaled_img, top_pad, bottom_pad, 0, 0, cv2.BORDER_CONSTANT, value=0)

        return padded_img
    except Exception as e:
        traceback.print_exc()
        logger.exception(f'Error while resizing image')
        return None

def convert_image_to_vector(img):
    """
    Convert an image to a feature vector using the ResNet152 model.
    """
    try:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.expand_dims(img, axis=0)
        img = preprocess_input(img)
        feature_vector = resnet_model.predict(img)
        return feature_vector.flatten()

    except Exception as e:
        traceback.print_exc()
        logger.exception("Error occurred in save_faces_from_folder")
        print(traceback.format_exc())
        print('An error occurred. Please check the logs for more details.')
        raise e

def save_faces_from_folder(folder_path, output_folder, face_detector, progress_callback=None, cancel_flag=None, partial_update_callback=None):
    """
    Detect and save faces from all images within the provided folder path.
    """
    face_data = {}
    valid_extensions = ['.png', '.jpeg', '.jpg', '.bmp']
    processed_images = set()  # Keep track of processed images
    processed_faces = set()  # Keep track of processed faces

    # Use os.walk to traverse directories
    image_paths = [os.path.join(root, name)
                   for root, dirs, files in os.walk(folder_path)
                   for name in files if not is_hidden(os.path.join(root, name))
                   if os.path.splitext(name)[-1].lower() in valid_extensions]

    num_images = len(image_paths)

    for idx, image_path in enumerate(image_paths, start=1):
        img_hash = None 
        # Check if processing should be cancelled
        if cancel_flag and cancel_flag():
            break
        if not is_valid_image_extension(image_path):
            logger.warning(f"{image_path} does not have a valid image extension. Skipping.")
            continue

        image_name = os.path.basename(image_path)
        logger.debug(f'Processing image {idx} of {num_images}: {image_name}')

        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Failed to read image from {image_path}")
        except Exception as e:
            logger.exception(f"Error reading or processing image {image_name} in save_faces_from_folder: {str(e)}")
            continue  # Skip to the next image

        # Only retrieve EXIF data for the original input images
        if os.path.splitext(image_name)[-1].lower() in valid_extensions:
            exif_data = get_image_exif_data(image_path)
        else:
            exif_data = {}

        # Print the EXIF data
        logger.debug(f"EXIF data for {image_name}: {exif_data}")
            
        try:
            # Using MTCNN for face detection
            detected_faces = face_detector.detect_faces(img)
            print(f'Number of faces detected: {len(detected_faces)}')

            # Print confidence scores
            
            if not detected_faces:
                print('No faces detected in the image.')

            for face in detected_faces:
                        confidence_score = face['confidence']
                        print(f"Image: {image_name}, Face Confidence: {confidence_score}")
                    
        except Exception as e:
            logger.exception(f'Error detecting faces in {image_name}. Skipping...')
            continue

        if len(detected_faces) > 0:
            try:
                img_hash = hashlib.md5(open(image_path, 'rb').read()).hexdigest()

                # If we have processed this image, continue to the next
                if img_hash in processed_images:
                    continue
                
                # Mark this image as processed
                processed_images.add(img_hash)

                face_data[img_hash] = {"file_name": image_name, "full_path": image_path, "faces": [], "exif_data": exif_data}

                
                if not detected_faces:
                    print('No faces detected in the image.')

                for face in detected_faces:
                                confidence = face['confidence']
                                if confidence < 0.9:  # adjust this threshold as needed
                                    continue
                                left, top, width, height = face['box']
                                right, bottom = left + width, top + height
                                face_img = img[top:bottom, left:right] 
                                
                                # Align the face
                                keypoints = face['keypoints']
                                aligned_face_img = align_face(face_img, keypoints['left_eye'], keypoints['right_eye'])

                                # Resize the aligned face to the desired size
                                resized_face_img = resize_image_with_aspect_ratio(aligned_face_img, (224, 224))
                                
                                # Convert the face image into a feature vector
                                face_vector = convert_image_to_vector(resized_face_img)

                                face_img_hash = hashlib.sha256(face_vector.tobytes()).hexdigest()
                                
                                # If we have processed this face, continue to the next
                                if face_img_hash in processed_faces:
                                    continue
                                
                                # Mark this face as processed
                                processed_faces.add(face_img_hash)

                                face_data[img_hash]["faces"].append(face_vector)
                                image_output_path = os.path.join(output_folder, f"{img_hash}_{len(face_data[img_hash]['faces'])}.png")
                                cv2.imwrite(image_output_path, resized_face_img)
            except Exception as e:
                logger.exception(f"Error occurred in save_faces_from_folder: {e}")
                continue

        if progress_callback:
            progress = idx / num_images * 100
            progress_callback(progress)

    return face_data

def find_matching_face(image_path, face_data, face_detector, threshold=.75):
    """
    Find faces in the provided image that match with any face from the given face data.
    """
    logger.debug(f'Starting to find matching face for image at {image_path}')
    matching_faces = []
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Unable to read image from {image_path}")

        # Using MTCNN for face detection
        detected_faces = face_detector.detect_faces(img)
        print(f'Number of faces detected: {len(detected_faces)}')
        
        if not detected_faces:
            print('No faces detected in the image.')

        for face in detected_faces:
                confidence = face['confidence']
                if confidence < 0.9:  # adjust this threshold as needed
                    continue
                # Get face box
                left, top, width, height = face['box']
                right, bottom = left + width, top + height

                face_img = img[top:bottom, left:right]  # Extract the face from the image

                # Align the face
                keypoints = face['keypoints']
                aligned_face_img = align_face(face_img, keypoints['left_eye'], keypoints['right_eye'])

                # Resize the aligned face to the desired size
                resized_face_img = resize_image_with_aspect_ratio(aligned_face_img, (224, 224))

                # Convert face image to vector
                face_vector = convert_image_to_vector(resized_face_img)

                for img_hash, stored_data in face_data.items():
                    stored_faces = stored_data["faces"]
                    for i, stored_face in enumerate(stored_faces):
                        if stored_face.size == 0:  # Add this check for empty vectors
                            continue

                        # Compare vectors instead of images
                        similarity = distance.cosine(face_vector, stored_face)
                        p_similarity = abs(similarity - 1)

                        if similarity < threshold:
                            matching_faces.append((img_hash, stored_data["file_name"], stored_face, p_similarity, f"{img_hash}_{i+1}.png"))

    except Exception as e:
        traceback.print_exc()
        logger.exception("Error occurred in find_matching_face")
        print(traceback.format_exc())
        print('An error occurred. Please check the logs for more details.')
        raise e
        
    print(f'Number of matches found: {len(matching_faces)}')
    
    if not matching_faces:
        print('No matching faces found for the image.')

    return matching_faces