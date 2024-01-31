from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess
import shutil
import random
import string
from PIL import Image
import cv2
import uuid

app = Flask(__name__)

# Ruta para la subida de archivos
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No se ha encontrado el archivo'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No se ha seleccionado ningún archivo'})

    # Generar un nombre aleatorio para el archivo
    random_name = generate_random_name() + os.path.splitext(file.filename)[1]

    # Guardar la imagen en la carpeta de archivos con el nuevo nombre
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
    file.save(file_path)

    # Obtener el prompt del request o establecer un valor predeterminado si está vacío
    prompt = request.form.get('prompt', 'Make him a black and white color realistic vector logo')

    # Comprimir la imagen si supera los 500 KB
    image_size_kb = os.path.getsize(file_path) / 1024
    if image_size_kb > 500:
        compressed_file_path = compress_image(file_path, app.config['TEMP_FOLDER'], 500)
        if compressed_file_path:
            # Reemplazar el archivo original con el comprimido
            os.replace(compressed_file_path, file_path)

    # Procesar la imagen
    if 'opencv' in prompt.lower():
        # Obtener los parámetros de umbral mínimo y máximo del prompt
        threshold_min, threshold_max = extract_threshold_params(prompt)

        # Generar la imagen en blanco y negro con OpenCV
        black_and_white_image_path = generate_black_and_white_image(file_path, threshold_min, threshold_max)

        # Generar un nuevo nombre aleatorio para la imagen procesada
        random_name_procesada = generate_random_name() + os.path.splitext(black_and_white_image_path)[1]

        # Mover la imagen procesada a la carpeta de archivos con el nuevo nombre
        imagen_procesada_nueva_path = os.path.join(app.config['UPLOAD_FOLDER'], random_name_procesada)
        shutil.move(black_and_white_image_path, imagen_procesada_nueva_path)

        # Generar el enlace a la imagen procesada
        imagen_procesada_link = f'http://ivancatalana.duckdns.org:{app.config["PORT"]}/uploads/{random_name_procesada}'

        # Agregar el enlace a la imagen procesada al response
        response_data = {'link': imagen_procesada_link}

        # Eliminar el archivo recibido
        os.remove(file_path)

        return jsonify(response_data)
    else:
        # Procesar la imagen con el programa aimg
        imagen_procesada_path = procesar_imagen(file_path, prompt)

        if imagen_procesada_path:
            # Generar un nuevo nombre aleatorio para la imagen procesada
            random_name_procesada = generate_random_name() + os.path.splitext(imagen_procesada_path)[1]

            # Mover la imagen procesada a la carpeta de archivos con el nuevo nombre
            imagen_procesada_nueva_path = os.path.join(app.config['UPLOAD_FOLDER'], random_name_procesada)
            shutil.move(imagen_procesada_path, imagen_procesada_nueva_path)

            # Generar el enlace a la imagen procesada
            imagen_procesada_link = f'http://ivancatalana.duckdns.org:{app.config["PORT"]}/uploads/{random_name_procesada}'

            # Agregar el enlace a la imagen procesada al response
            response_data = {'link': imagen_procesada_link}

            # Eliminar el archivo recibido
            os.remove(file_path)

            return jsonify(response_data)
        else:
            return jsonify({'error': 'Error al procesar la imagen'})

# Función para extraer los parámetros de umbral mínimo y máximo del prompt
def extract_threshold_params(prompt):
    try:
        params = prompt.split('opencv')[1].strip().split()
        threshold_min = int(params[0])
        threshold_max = int(params[1])
        return threshold_min, threshold_max
    except:
        return None, None

# Función para generar la imagen en blanco y negro con OpenCV
def generate_black_and_white_image(image_path, threshold_min, threshold_max):
    original_image = cv2.imread(image_path)
    if original_image is None:
        print(f"Error: Unable to load image from '{image_path}'")
        return None

    gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    _, black_and_white_image = cv2.threshold(gray_image, threshold_min, threshold_max, cv2.THRESH_BINARY)

    # Generar un nombre de archivo único aleatorio
    filename = str(uuid.uuid4()) + '.jpg'

    output_path = os.path.join(app.config['TEMP_FOLDER'], filename)  # Ruta y nombre del archivo de salida
    cv2.imwrite(output_path, black_and_white_image)
    print(f"Saved black and white image to '{output_path}'")

    return output_path

# Función para comprimir una imagen
def compress_image(input_path, output_folder, target_size_kb):
    # Cargar la imagen usando Pillow
    image = Image.open(input_path)

    # Obtener el tamaño actual de la imagen en bytes
    current_size_bytes = os.path.getsize(input_path)

    # Comprimir la imagen iterativamente hasta alcanzar el tamaño objetivo
    while current_size_bytes > target_size_kb * 1024:
        # Redimensionar la imagen a la mitad de su tamaño actual
        width, height = image.size
        new_width = width // 2 if width % 2 == 0 else (width - 1) // 2
        new_height = height // 2 if height % 2 == 0 else (height - 1) // 2
        image.thumbnail((new_width, new_height))

        # Guardar la imagen redimensionada en un archivo temporal
        temp_output_path = os.path.join(output_folder, "temp.jpg")
        image.save(temp_output_path, "JPEG")

        # Obtener el tamaño de la imagen redimensionada
        current_size_bytes = os.path.getsize(temp_output_path)

    # Obtener el tamaño de la imagen comprimida
    compressed_size_bytes = current_size_bytes
    compressed_size_kb = compressed_size_bytes / 1024

    return temp_output_path

# Función para procesar la imagen utilizando el programa aimg
def procesar_imagen(imagen_path, prompt):
    comando = f"aimg edit {imagen_path} -p '{prompt}' --outdir /home/ivan/ --steps 10 --output-file-extension jpg"
    proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while proceso.poll() is None:
        output = proceso.stdout.readline().decode()
        print(output.strip())
    stdout, stderr = proceso.communicate()
    if proceso.returncode == 0:
        imagen_procesada_path = None
        for file in os.listdir('/home/ivan/generated'):
            if file.endswith('.jpg'):
                imagen_procesada_path = os.path.join('/home/ivan/generated', file)
                break
        if imagen_procesada_path:
            return imagen_procesada_path
        else:
            print(f"No se encontró ningún archivo .jpg en /home/ivan/generated")
            return None
    else:
        print(f"Error al procesar la imagen: {stderr.decode('utf-8')}")
        return None

# Ruta para servir los archivos estáticos
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def generate_random_name(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'  # Carpeta donde se guardarán los archivos
    app.config['TEMP_FOLDER'] = 'temp'  # Carpeta temporal para almacenar las imágenes comprimidas
    app.config['PORT'] = 8000  # Puerto personalizado
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)  # Crear la carpeta temporal si no existe
    app.run(debug=True, host='0.0.0.0', port=app.config['PORT'])

