import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from datetime import datetime, timezone
from decimal import Decimal
import boto3

# --- Helper de Serialización para DynamoDB ---
def decimal_default(obj):
    """
    Convierte tipos Decimal de DynamoDB a int o float para que json.dumps() no arroje error 500.
    """
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('COMPRAS_TABLE', 'ticketpass_compras_dev')
SMTP_EMAIL = os.environ.get('SMTP_EMAIL')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

# Configuración Completa de CORS
HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With,Accept",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
}

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(body, default=decimal_default) if isinstance(body, (dict, list)) else body
    }

def enviar_correo_gmail(datos):
    destinatario = datos.get('usuario_email')
    titulo_evento = datos.get('titulo_evento', 'Evento TicketPass')
    codigo_ticket = datos.get('codigo_ticket')
    zona = datos.get('zona', 'General')
    cantidad = datos.get('cantidad', 1)
    precio_total = datos.get('precio_total', 0.0)
    reembolsable = datos.get('reembolsable', False)
    
    # Extraer variables garantizando un valor visible si vienen vacías
    fecha_evento = datos.get('fecha_evento') or 'Por confirmar'
    lugar_evento = datos.get('lugar_evento') or 'Por confirmar'

    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    if not smtp_email or not smtp_password:
        print("ERROR CRÍTICO: Variables de entorno SMTP no configuradas.")
        return False

    # Versión en texto plano para el filtro antispam de Gmail
    text_body = f"""
    ¡Compra Confirmada!
    Gracias por tu compra en TicketPass.

    Detalles de la Entrada #{codigo_ticket}
    -------------------------------------------
    Evento: {titulo_evento}
    Lugar: {lugar_evento}
    Fecha y Hora: {fecha_evento}
    Zona: {zona}
    Cantidad: {cantidad} ticket(s)
    Total Pagado: S/ {float(precio_total):.2f}

    TicketPass Inc. - Todos los derechos reservados.
    """

    politica_html = """
    <div style="background-color: #e6fffa; border-left: 4px solid #319795; padding: 12px; margin-top: 15px; border-radius: 4px;">
        <strong style="color: #234e52;">Ticket Reembolsable</strong>
        <p style="margin: 4px 0 0 0; color: #2c7a7b; font-size: 13px;">
            Esta entrada aplica para reembolso completo si se solicita con al menos 48 horas de anticipación.
        </p>
    </div>
    """ if reembolsable else """
    <div style="background-color: #fff5f5; border-left: 4px solid #e53e3e; padding: 12px; margin-top: 15px; border-radius: 4px;">
        <strong style="color: #742a2a;">Ticket No Reembolsable</strong>
        <p style="margin: 4px 0 0 0; color: #9b2c2c; font-size: 13px;">
            Esta entrada se adquirió en modalidad de tarifa final sin opción a cancelación ni reembolso.
        </p>
    </div>
    """

    html_body = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f7fafc; color: #2d3748; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 24px; border: 1px solid #e2e8f0;">
            <div style="text-align: center; border-bottom: 2px solid #edf2f7; padding-bottom: 16px;">
                <h1 style="color: #2563eb; margin: 0; font-size: 24px;">¡Compra Confirmada!</h1>
                <p>Gracias por tu compra en TicketPass.</p>
            </div>

            <div style="margin-top: 20px;">
                <h3>Detalles de la Entrada #{codigo_ticket}</h3>
                <p><strong>Evento:</strong> {titulo_evento}</p>
                <p><strong>Lugar:</strong> {lugar_evento}</p>
                <p><strong>Fecha y Hora:</strong> {fecha_evento}</p>
                <p><strong>Zona:</strong> {zona}</p>
                <p><strong>Cantidad:</strong> {cantidad} ticket(s)</p>
                <p style="font-size: 18px; font-weight: bold; color: #16a34a; text-align: right; margin-top: 15px;">
                    Total Pagado: S/ {float(precio_total):.2f}
                </p>
            </div>

            {politica_html}

            <div style="text-align: center; margin-top: 24px; font-size: 12px; color: #a0aec0;">
                <p>TicketPass Inc. - Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Construcción de la estructura MIME Multipart
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Confirmación de Compra - TicketPass: {titulo_evento}"
    msg['From'] = f"TicketPass <{smtp_email}>"
    msg['To'] = destinatario
    msg['Reply-To'] = smtp_email
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain="gmail.com")

    # Adjuntar primero texto plano y luego HTML
    part1 = MIMEText(text_body, 'plain', 'utf-8')
    part2 = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, destinatario, msg.as_string())
        
        print(f"ÉXITO CRÍTICO: Correo enviado correctamente a {destinatario}")
        return True
    except Exception as e:
        print(f"ERROR SMTP EN LAMBDA: {type(e).__name__} - {str(e)}")
        return False

def procesarCompra(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})

    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else (event.get('body') or {})
        
        evento_id = body.get('evento_id') or body.get('eventoId')
        usuario_email = body.get('usuario_email') or body.get('email') or body.get('comprador', {}).get('email')
        zona = body.get('zona', 'General')
        cantidad = body.get('cantidad', 1)
        precio_total = body.get('precio_total') or body.get('precioTotal', 0)
        reembolsable = bool(body.get('reembolsable', False))
        titulo_evento = body.get('titulo_evento', 'Evento TicketPass')

        # Extracción flexible de Fecha, Hora y Lugar
        fecha_evento = body.get('fecha_evento') or body.get('fecha') or 'Por confirmar'
        hora_evento = body.get('hora_evento') or body.get('hora') or 'Por confirmar'
        lugar_evento = body.get('lugar_evento') or body.get('lugar') or body.get('ubicacion') or 'Por confirmar'

        if not usuario_email:
            return response(400, {"error": "El correo del usuario es obligatorio"})

        email_clean = str(usuario_email).strip().lower()
        now = datetime.now(timezone.utc)
        codigo_ticket = f"TK-{int(now.timestamp() * 1000)}"
        fecha_compra = now.isoformat()

        # Guardar la información en DynamoDB incluyendo fecha, hora y lugar
        item = {
            'codigo_ticket': codigo_ticket,
            'evento_id': str(evento_id),
            'usuario_email': email_clean,
            'email': email_clean,
            'titulo_evento': titulo_evento,
            'zona': zona,
            'cantidad': int(cantidad),
            'precio_total': str(precio_total),
            'reembolsable': reembolsable,
            'fecha_compra': fecha_compra,
            'fecha_evento': fecha_evento,
            'hora_evento': hora_evento,
            'lugar_evento': lugar_evento
        }

        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item=item)

        # Envío de correo
        correo_enviado = False
        try:
            correo_enviado = enviar_correo_gmail({
                "usuario_email": email_clean,
                "codigo_ticket": codigo_ticket,
                "titulo_evento": titulo_evento,
                "zona": zona,
                "cantidad": cantidad,
                "precio_total": precio_total,
                "reembolsable": reembolsable,
                "fecha_evento": fecha_evento,
                "hora_evento": hora_evento,
                "lugar_evento": lugar_evento
            })
        except Exception as err_mail:
            print(f"Error secundario en envio de correo: {str(err_mail)}")

        return response(201, {
            "mensaje": "Compra procesada exitosamente",
            "correo_enviado": correo_enviado,
            "compra": item
        })

    except Exception as e:
        print(f"Error en procesarCompra: {str(e)}")
        return response(500, {"error": f"Error interno: {str(e)}"})

def obtenerComprasPorUsuario(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {"message": "OK"})

    try:
        query_params = event.get('queryStringParameters') or {}
        email_buscado = query_params.get('email')

        if not email_buscado:
            return response(400, {"error": "El parámetro 'email' es requerido"})

        email_clean = str(email_buscado).strip().lower()

        table = dynamodb.Table(TABLE_NAME)

        # Escanear DynamoDB trayendo todos los elementos para filtrar flexiblemente
        res = table.scan()
        todos_los_items = res.get('Items', [])

        while 'LastEvaluatedKey' in res:
            res = table.scan(ExclusiveStartKey=res['LastEvaluatedKey'])
            todos_los_items.extend(res.get('Items', []))

        # Filtrado en Python flexible e insensible a mayúsculas/minúsculas
        compras_usuario = []
        for item in todos_los_items:
            u_email = item.get('usuario_email') or item.get('email') or (item.get('comprador', {}).get('email') if isinstance(item.get('comprador'), dict) else None)
            
            if u_email and str(u_email).strip().lower() == email_clean:
                compras_usuario.append(item)

        return response(200, compras_usuario)

    except Exception as e:
        print(f"Error interno en obtenerComprasPorUsuario: {str(e)}")
        return response(500, {"error": f"Error al obtener compras: {str(e)}"})