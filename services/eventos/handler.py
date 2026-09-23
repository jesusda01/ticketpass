import json
import os
import boto3
from decimal import Decimal

# Helper para convertir floats a Decimal antes de guardar en DynamoDB
def convertir_floats_a_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convertir_floats_a_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convertir_floats_a_decimal(v) for v in obj]
    return obj

# Helper para convertir los tipos Decimal que devuelve DynamoDB a valores numéricos en JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o) if o % 1 > 0 else int(o)
        return super(DecimalEncoder, self).default(o)

stage = os.environ.get('STAGE', 'dev')
dynamodb = boto3.resource('dynamodb')
tabla_eventos = dynamodb.Table(f'ticketpass_eventos_{stage}')

def respuesta_json(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, cls=DecimalEncoder, ensure_ascii=False)
    }

def obtener_eventos(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        categoria = params.get('categoria')
        search_query = params.get('q', '').lower().strip()

        response = tabla_eventos.scan()
        eventos = response.get('Items', [])

        # Filtro por categoría
        if categoria and categoria != "Todas" and categoria != "":
            eventos = [e for e in eventos if e.get('categoria') == categoria]

        # Filtro por término de búsqueda (título o descripción)
        if search_query:
            eventos = [
                e for e in eventos 
                if search_query in e.get('titulo', '').lower() or search_query in e.get('descripcion', '').lower()
            ]

        return respuesta_json(200, eventos)
    except Exception as e:
        return respuesta_json(500, {"error": str(e)})

def obtener_evento_por_id(event, context):
    try:
        path_params = event.get('pathParameters') or {}
        evento_id = path_params.get('id')

        if not evento_id:
            return respuesta_json(400, {"detail": "Falta el parámetro ID"})

        response = tabla_eventos.get_item(Key={'id': str(evento_id)})
        
        item = response.get('Item')
        if not item:
            return respuesta_json(404, {"detail": "Evento no encontrado"})

        return respuesta_json(200, item)
    except Exception as e:
        return respuesta_json(500, {"error": str(e)})

def obtener_zonas(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        evento_id = params.get('evento_id') or params.get('id')

        if not evento_id:
            return respuesta_json(400, {"detail": "Falta el parámetro evento_id"})

        response = tabla_eventos.get_item(Key={'id': str(evento_id)})
        item = response.get('Item')

        if not item:
            return respuesta_json(404, {"detail": "Evento no encontrado"})

        # Extrae la lista de zonas asociadas al evento
        zonas = item.get('zonas', [])
        return respuesta_json(200, zonas)
    except Exception as e:
        return respuesta_json(500, {"error": str(e)})

def precargar_eventos(event, context):
    EVENTOS_INICIALES = [
        # CINE
        {
            "id": "1",
            "titulo": "Maratón Cine de Terror Clásico",
            "categoria": "Cine",
            "lugar": "Cinemark Jockey Plaza",
            "fecha": "31 Oct 2026 - 18:00 hrs",
            "descripcion": "Una noche espeluznante con las mejores películas de terror clásico.",
            "imagen_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&q=80",
            "precio_base": 30.00,
            "zonas": [
                {"nombre": "General", "precio": 30.00},
                {"nombre": "VIP Proyección", "precio": 45.00}
            ]
        },
        {
            "id": "2",
            "titulo": "Festival de Cine Independiente",
            "categoria": "Cine",
            "lugar": "Cineplanet Alcázar",
            "fecha": "15 Nov 2026 - 16:00 hrs",
            "descripcion": "Proyección de cortometrajes y largometrajes galardonados.",
            "imagen_url": "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80",
            "precio_base": 25.00,
            "zonas": [
                {"nombre": "General", "precio": 25.00},
                {"nombre": "Preferencial", "precio": 38.00}
            ]
        },
        {
            "id": "3",
            "titulo": "Estreno Exclusivo: Sci-Fi 2026",
            "categoria": "Cine",
            "lugar": "Cinepolis Larcomar",
            "fecha": "20 Nov 2026 - 20:00 hrs",
            "descripcion": "Premier exclusiva de la película de ciencia ficción más esperada.",
            "imagen_url": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=600&q=80",
            "precio_base": 45.00,
            "zonas": [
                {"nombre": "Standard", "precio": 45.00},
                {"nombre": "IMAX VIP", "precio": 65.00}
            ]
        },
        {
            "id": "4",
            "titulo": "Cine Bajo las Estrellas",
            "categoria": "Cine",
            "lugar": "Parque Reducto, Miraflores",
            "fecha": "05 Dic 2026 - 19:00 hrs",
            "descripcion": "Función al aire libre en pantalla gigante con mantas.",
            "imagen_url": "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=600&q=80",
            "precio_base": 20.00,
            "zonas": [
                {"nombre": "Césped General", "precio": 20.00},
                {"nombre": "Cama Lounge VIP", "precio": 40.00}
            ]
        },
        # CONCIERTOS
        {
            "id": "5",
            "titulo": "Rock Fest Lima 2026",
            "categoria": "Conciertos",
            "lugar": "Estadio Nacional",
            "fecha": "12 Nov 2026 - 19:00 hrs",
            "descripcion": "El festival de rock más masivo del país.",
            "imagen_url": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=600&q=80",
            "precio_base": 120.00,
            "zonas": [
                {"nombre": "Tribuna Norte", "precio": 120.00},
                {"nombre": "Campo A", "precio": 220.00}
            ]
        },
        {
            "id": "6",
            "titulo": "Noche de Jazz & Blues",
            "categoria": "Conciertos",
            "lugar": "Gran Teatro Nacional",
            "fecha": "18 Nov 2026 - 20:30 hrs",
            "descripcion": "Velada íntima con referentes del jazz contemporáneo.",
            "imagen_url": "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=600&q=80",
            "precio_base": 85.00,
            "zonas": [
                {"nombre": "Piso 4", "precio": 85.00},
                {"nombre": "Platea Preferencial", "precio": 160.00}
            ]
        },
        {
            "id": "7",
            "titulo": "Sinfonía Electrónica",
            "categoria": "Conciertos",
            "lugar": "Arena 1, San Miguel",
            "fecha": "27 Nov 2026 - 22:00 hrs",
            "descripcion": "Fusión entre orquesta filarmónica y DJs electrónicos.",
            "imagen_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=600&q=80",
            "precio_base": 110.00,
            "zonas": [
                {"nombre": "General Dance", "precio": 110.00},
                {"nombre": "VIP Stage", "precio": 180.00}
            ]
        },
        {
            "id": "8",
            "titulo": "Festival Cumbia & Salsa All-Stars",
            "categoria": "Conciertos",
            "lugar": "Exposición de Lima",
            "fecha": "10 Dic 2026 - 17:00 hrs",
            "descripcion": "12 horas ininterrumpidas de baile.",
            "imagen_url": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=600&q=80",
            "precio_base": 70.00,
            "zonas": [
                {"nombre": "General", "precio": 70.00},
                {"nombre": "VIP Baile", "precio": 120.00}
            ]
        },
        # DEPORTE
        {
            "id": "9",
            "titulo": "Final Torneo Clausura 2026",
            "categoria": "Deporte",
            "lugar": "Estadio Monumental",
            "fecha": "22 Nov 2026 - 15:30 hrs",
            "descripcion": "Partido decisivo por el título del fútbol peruano.",
            "imagen_url": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=600&q=80",
            "precio_base": 50.00,
            "zonas": [
                {"nombre": "Popular Norte/Sur", "precio": 50.00},
                {"nombre": "Oriente", "precio": 110.00}
            ]
        },
        {
            "id": "10",
            "titulo": "Maratón Internacional de Lima",
            "categoria": "Deporte",
            "lugar": "Miraflores (Partida)",
            "fecha": "29 Nov 2026 - 06:00 hrs",
            "descripcion": "Modalidades 42k, 21k y 10k.",
            "imagen_url": "https://images.unsplash.com/photo-1452626038306-9aae5e071dd3?auto=format&fit=crop&w=600&q=80",
            "precio_base": 80.00,
            "zonas": [
                {"nombre": "Kit Participante 10K", "precio": 80.00},
                {"nombre": "Kit Participante 21K/42K", "precio": 100.00}
            ]
        },
        {
            "id": "11",
            "titulo": "Exhibición Internacional de Tenis",
            "categoria": "Deporte",
            "lugar": "Club Terrazas Miraflores",
            "fecha": "04 Dic 2026 - 18:00 hrs",
            "descripcion": "Exhibición entre tenistas Top 20 ATP.",
            "imagen_url": "https://images.unsplash.com/photo-1595435934249-5df7ed86e1c0?auto=format&fit=crop&w=600&q=80",
            "precio_base": 150.00,
            "zonas": [
                {"nombre": "Tribuna Preferencial", "precio": 150.00},
                {"nombre": "Cancha VIP", "precio": 280.00}
            ]
        },
        {
            "id": "12",
            "titulo": "Campeonato Surf Open Pro",
            "categoria": "Deporte",
            "lugar": "Playa Punta Hermosa",
            "fecha": "12 Dic 2026 - 08:00 hrs",
            "descripcion": "Megariders en olas de clase mundial.",
            "imagen_url": "https://images.unsplash.com/photo-1502680390469-be75c86b636f?auto=format&fit=crop&w=600&q=80",
            "precio_base": 35.00,
            "zonas": [
                {"nombre": "Acceso Bleachers", "precio": 35.00},
                {"nombre": "Lounge Atletas", "precio": 75.00}
            ]
        },
        # ARTE Y CULTURA
        {
            "id": "13",
            "titulo": "Exposición Inmersiva Van Gogh",
            "categoria": "Arte & Cultura",
            "lugar": "Museo de Arte de Lima (MALI)",
            "fecha": "10 Nov 2026 - 10:00 hrs",
            "descripcion": "Proyecciones 360 grados de las obras de Van Gogh.",
            "imagen_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=600&q=80",
            "precio_base": 40.00,
            "zonas": [
                {"nombre": "Entrada General", "precio": 40.00},
                {"nombre": "Entrada VR Experiencia", "precio": 60.00}
            ]
        },
        {
            "id": "14",
            "titulo": "Ballet Clásico: El Lago de los Cisnes",
            "categoria": "Arte & Cultura",
            "lugar": "Teatro Municipal de Lima",
            "fecha": "25 Nov 2026 - 20:00 hrs",
            "descripcion": "Interpretación del Ballet Nacional con orquesta.",
            "imagen_url": "https://images.unsplash.com/photo-1518834107812-67b0b7c58434?auto=format&fit=crop&w=600&q=80",
            "precio_base": 90.00,
            "zonas": [
                {"nombre": "Cazuela", "precio": 90.00},
                {"nombre": "Platea Central", "precio": 130.00}
            ]
        },
        {
            "id": "15",
            "titulo": "Obra Teatral: Odisea Contemporánea",
            "categoria": "Arte & Cultura",
            "lugar": "Teatro Pirandello",
            "fecha": "02 Dic 2026 - 20:30 hrs",
            "descripcion": "Adaptación moderna del clásico de Homero.",
            "imagen_url": "https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?auto=format&fit=crop&w=600&q=80",
            "precio_base": 60.00,
            "zonas": [
                {"nombre": "Mezzanine", "precio": 60.00},
                {"nombre": "Plate VIP", "precio": 85.00}
            ]
        },
        {
            "id": "16",
            "titulo": "Feria Internacional del Libro Nocturna",
            "categoria": "Arte & Cultura",
            "lugar": "Parque de la Reserva",
            "fecha": "15 Dic 2026 - 17:00 hrs",
            "descripcion": "Presentaciones de libros y firma de autores.",
            "imagen_url": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?auto=format&fit=crop&w=600&q=80",
            "precio_base": 15.00,
            "zonas": [
                {"nombre": "Pase Diario General", "precio": 15.00},
                {"nombre": "Pase VIP + Libro", "precio": 45.00}
            ]
        }
    ]

    try:
        with tabla_eventos.batch_writer() as batch:
            for ev in EVENTOS_INICIALES:
                ev_decimal = convertir_floats_a_decimal(ev)
                batch.put_item(Item=ev_decimal)

        return respuesta_json(200, {"message": "16 eventos precargados exitosamente en DynamoDB"})
    except Exception as e:
        return respuesta_json(500, {"error": str(e)})