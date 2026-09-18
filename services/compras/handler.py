import json
import os
import uuid
import boto3

stage = os.environ.get('STAGE', 'dev')
dynamodb = boto3.resource('dynamodb')
tabla_compras = dynamodb.Table(f'ticketpass_compras_{stage}')

def respuesta_json(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }

def procesar_compra(event, context):
    try:
        data = json.loads(event.get('body', '{}'))

        evento_id = data.get('evento_id')
        zona_nombre = data.get('zona_nombre', 'General')
        cantidad = int(data.get('cantidad', 1))
        es_reembolsable = bool(data.get('es_reembolsable', False))
        metodo_pago = data.get('metodo_pago', 'Tarjeta de Crédito')
        email_comprador = data.get('email_comprador')
        precio_unitario = float(data.get('precio_unitario', 30.00))

        if not email_comprador or not evento_id:
            return respuesta_json(400, {"message": "Campos faltantes obligatorios"})

        monto_subtotal = precio_unitario * cantidad
        costo_reembolso = (12.99 * cantidad) if es_reembolsable else 0.0
        monto_total_final = monto_subtotal + costo_reembolso

        codigo_ticket = f"TK-{uuid.uuid4().hex[:8].upper()}"

        item_compra = {
            "codigo_ticket": codigo_ticket,
            "evento_id": str(evento_id),
            "zona_nombre": zona_nombre,
            "cantidad": cantidad,
            "es_reembolsable": es_reembolsable,
            "metodo_pago": metodo_pago,
            "email_comprador": email_comprador,
            "monto_total": str(monto_total_final)
        }

        tabla_compras.put_item(Item=item_compra)

        return respuesta_json(200, {
            "status": "success",
            "codigo_ticket": codigo_ticket,
            "monto_total": monto_total_final,
            "mensaje": "Compra realizada con éxito en AWS DynamoDB."
        })

    except Exception as e:
        return respuesta_json(500, {"error": str(e)})