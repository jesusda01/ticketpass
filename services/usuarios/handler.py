import json
import os
import hashlib
from datetime import datetime, timezone
import boto3

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('USUARIOS_TABLE', 'ticketpass_usuarios_dev')

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With,Accept",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
}

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(body) if isinstance(body, (dict, list)) else body
    }

def hash_password(password: str) -> str:
    """Genera un hash SHA-256 para la contraseña."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def registrarUsuario(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})

    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else (event.get('body') or {})
        
        email = body.get('email')
        nombre = body.get('nombre') or body.get('name', 'Usuario')
        password = body.get('password')

        if not email or not password:
            return response(400, {"error": "El email y la contraseña son obligatorios"})

        email_clean = str(email).strip().lower()
        table = dynamodb.Table(TABLE_NAME)

        # Verificar si el usuario ya existe
        res = table.get_item(Key={'email': email_clean})
        if 'Item' in res:
            return response(409, {"error": "El correo ya se encuentra registrado"})

        now = datetime.now(timezone.utc).isoformat()
        
        item = {
            'email': email_clean,
            'nombre': nombre.strip(),
            'password_hash': hash_password(password),
            'fecha_registro': now
        }

        table.put_item(Item=item)

        # Retornar perfil omitiendo la contraseña
        user_data = {
            'email': item['email'],
            'nombre': item['nombre'],
            'fecha_registro': item['fecha_registro']
        }

        return response(201, {
            "mensaje": "Usuario registrado exitosamente",
            "usuario": user_data
        })

    except Exception as e:
        print(f"Error en registrarUsuario: {str(e)}")
        return response(500, {"error": f"Error interno al registrar usuario: {str(e)}"})


def loginUsuario(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})

    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else (event.get('body') or {})
        
        email = body.get('email')
        password = body.get('password')

        if not email or not password:
            return response(400, {"error": "Email y contraseña requeridos"})

        email_clean = str(email).strip().lower()
        table = dynamodb.Table(TABLE_NAME)

        res = table.get_item(Key={'email': email_clean})
        item = res.get('Item')

        if not item:
            return response(404, {"error": "Usuario no encontrado"})

        # Validar Hash de contraseña
        if item.get('password_hash') != hash_password(password):
            return response(401, {"error": "Contraseña incorrecta"})

        user_data = {
            'email': item['email'],
            'nombre': item.get('nombre', 'Usuario'),
            'fecha_registro': item.get('fecha_registro', '')
        }

        return response(200, {
            "mensaje": "Login exitoso",
            "usuario": user_data
        })

    except Exception as e:
        print(f"Error en loginUsuario: {str(e)}")
        return response(500, {"error": f"Error interno en login: {str(e)}"})


def obtenerPerfil(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})

    try:
        query_params = event.get('queryStringParameters') or {}
        email = query_params.get('email')

        if not email:
            return response(400, {"error": "El parámetro 'email' es requerido"})

        email_clean = str(email).strip().lower()
        table = dynamodb.Table(TABLE_NAME)

        res = table.get_item(Key={'email': email_clean})
        item = res.get('Item')

        if not item:
            return response(404, {"error": "Usuario no encontrado"})

        user_data = {
            'email': item['email'],
            'nombre': item.get('nombre', 'Usuario'),
            'fecha_registro': item.get('fecha_registro', '')
        }

        return response(200, user_data)

    except Exception as e:
        print(f"Error en obtenerPerfil: {str(e)}")
        return response(500, {"error": f"Error interno al obtener perfil: {str(e)}"})