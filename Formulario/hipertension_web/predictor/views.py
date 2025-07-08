from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings
import requests
import json
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def predict(request):
    if request.method == 'POST':
        try:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = request.POST

            actividad_map = {
                '1': 1,  
                '2': 2,  
                '3': 3,  
                '4': 4,  
                '5': 5   
            }

            peso = float(data.get('peso', 0))
            estatura = float(data.get('estatura', 0)) / 100  
            masa_corporal = peso / (estatura * estatura) if estatura > 0 else 0

            form_data = {
                'masa_corporal': masa_corporal,
                'tension_arterial': float(data.get('tension_arterial', 0)),
                'medida_cintura': float(data.get('medida_cintura', 0)),
                'peso': peso,
                'actividad_total': actividad_map.get(data.get('nivel_actividad', '3'), 3),
                'edad': int(data.get('edad', 0)),
                'estatura': float(data.get('estatura', 0)),
                'sexo': int(data.get('sexo', 0)),
                'sueno_horas': float(data.get('sueno_horas', 0)),
                'valor_hemoglobina_glucosilada': float(data.get('valor_hemoglobina_glucosilada', 0)),
                'valor_insulina': float(data.get('valor_insulina', 0)),
                'resultado_glucosa_promedio': float(data.get('resultado_glucosa_promedio', 0)),
                'concentracion_hemoglobina': float(data.get('concentracion_hemoglobina', 0)),
                'valor_colesterol_ldl': float(data.get('valor_colesterol_ldl', 0)),
                'valor_trigliceridos': float(data.get('valor_trigliceridos', 0))
            }
            logger.debug(f"Datos del formulario procesados: {form_data}")

            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            api_url = 'http://localhost:8001/predict'
            logger.debug(f"Enviando datos a la API: {api_url}")
            logger.debug(f"Datos enviados: {json.dumps([form_data])}")

            response = requests.post(
                api_url,
                data=json.dumps([form_data]),
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Respuesta de la API: {result}")

            prediction = result['predictions'][0]

            nombre_completo = data.get('nombre_completo', '').strip()
            request.session['latest_prediction'] = {
                'form_data': form_data,
                'prediction': prediction,
                'nombre_completo': nombre_completo,
                'correo': data.get('correo', '')
            }

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'prediction': prediction
                })
            else:
                context = {
                    'result': {'prediction': prediction},
                    'form_data': data 
                }
                return render(request, 'index.html', context)

        except requests.exceptions.ConnectionError as ce:
            logger.error(f"Error de conexión con la API: {str(ce)}")
            return JsonResponse({'error': 'No se pudo conectar con la API.'}, status=500)
        except requests.exceptions.Timeout as te:
            logger.error(f"Timeout al conectar con la API: {str(te)}")
            return JsonResponse({'error': 'La solicitud al servidor tomó demasiado tiempo.'}, status=500)
        except requests.exceptions.HTTPError as he:
            logger.error(f"Error HTTP: {str(he)}")
            return JsonResponse({'error': f'Error en la API: {str(he)}'}, status=500)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)

    return render(request, 'index.html')

def send_report(request):
    if request.method == 'POST':
        try:
            prediction_data = request.session.get('latest_prediction')
            if not prediction_data:
                return JsonResponse({'error': 'Debes realizar una predicción antes de enviar el reporte.'}, status=400)

            email = request.POST.get('email')
            nombre_completo = request.POST.get('nombre_completo', '').strip()

            if not email or not nombre_completo:
                email = email or prediction_data.get('correo')
                nombre_completo = nombre_completo or prediction_data.get('nombre_completo', 'Usuario')
            if not email:
                return JsonResponse({'error': 'Correo electrónico no proporcionado en el formulario'}, status=400)

            sexo_map = {2: 'Femenino', 1: 'Masculino'}
            actividad_map = {
                1: 'Muy Baja',
                2: 'Baja',
                3: 'Moderada',
                4: 'Alta',
                5: 'Muy Alta'
            }

            styles = getSampleStyleSheet()
            section_title_style = ParagraphStyle(
                name='SectionTitle',
                fontSize=14,
                leading=16,
                spaceAfter=12,
                fontName='Helvetica-Bold'
            )

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []

            story.append(Paragraph("Reporte de Predicción de Riesgo de Hipertensión Arterial", styles['Title']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>Para:</b> {nombre_completo}", styles['Normal']))
            story.append(Spacer(1, 24))

            story.append(Paragraph("Información Personal", section_title_style))
            form_data = prediction_data.get('form_data', {})
            personal_fields = ['edad', 'sexo', 'estatura', 'peso', 'masa_corporal']
            for key in personal_fields:
                value = form_data.get(key, 0)
                if key == 'sexo':
                    value = sexo_map.get(value, str(value))
                elif key == 'masa_corporal':
                    value = f"{float(value):.2f} kg/m²"
                elif key == 'estatura':
                    value = f"{float(value)} cm"
                elif key == 'peso':
                    value = f"{float(value)} kg"
                label = f"{key.replace('_', ' ').title()}: "
                story.append(Paragraph(f"<b>{label}</b>{value}", styles['Normal']))
            story.append(Spacer(1, 12))

            story.append(Paragraph("Mediciones Clínicas", section_title_style))
            clinical_fields = [
                'tension_arterial', 'medida_cintura', 'actividad_total', 'sueno_horas',
                'valor_hemoglobina_glucosilada', 'valor_insulina', 'resultado_glucosa_promedio',
                'concentracion_hemoglobina', 'valor_colesterol_ldl', 'valor_trigliceridos'
            ]
            for key in clinical_fields:
                value = form_data.get(key, 0)
                if key == 'actividad_total':
                    value = actividad_map.get(value, str(value))
                elif key == 'tension_arterial':
                    value = f"{float(value)} mmHg"
                elif key == 'medida_cintura':
                    value = f"{float(value)} cm"
                elif key == 'sueno_horas':
                    value = f"{float(value)} horas"
                elif key == 'valor_hemoglobina_glucosilada':
                    value = f"{float(value)} %"
                elif key == 'valor_insulina':
                    value = f"{float(value)} µU/mL"
                elif key == 'resultado_glucosa_promedio':
                    value = f"{float(value)} mg/dL"
                elif key == 'concentracion_hemoglobina':
                    value = f"{float(value)} g/dL"
                elif key == 'valor_colesterol_ldl':
                    value = f"{float(value)} mg/dL"
                elif key == 'valor_trigliceridos':
                    value = f"{float(value)} mg/dL"
                label = f"{key.replace('_', ' ').title()}: "
                story.append(Paragraph(f"<b>{label}</b>{value}", styles['Normal']))
            story.append(Spacer(1, 12))

            story.append(Paragraph("Resultado de Predicción", section_title_style))
            prediction_text = "El paciente presenta riesgo de Hipertensión Arterial" if prediction_data.get('prediction') == "Con riesgo" else "El paciente no presenta riesgo de Hipertensión Arterial"
            story.append(Paragraph(prediction_text, styles['Normal']))

            doc.build(story)
            buffer.seek(0)

            email_message = EmailMessage(
                subject='Reporte de Predicción de Riesgo de Hipertensión Arterial',
                body=f'Hola {nombre_completo},\n\nAdjunto encontrarás el reporte de predicción de riesgo de hipertensión arterial.\n\nSaludos,\nEquipo de Predicción',
                from_email=settings.EMAIL_HOST_USER,
                to=[email]
            )
            email_message.attach('reporte_hipertension.pdf', buffer.getvalue(), 'application/pdf')
            email_message.send()

            return JsonResponse({'message': 'Reporte enviado con éxito'})

        except Exception as e:
            logger.error(f"Error al enviar el reporte: {str(e)}")
            return JsonResponse({'error': f'Error al enviar el reporte: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

def clear_session(request):
    if request.method == 'POST':
        try:
            logger.debug("Limpiando datos de la sesión")
            if 'latest_prediction' in request.session:
                del request.session['latest_prediction']
            request.session.flush()
            logger.debug("Sesión limpiada exitosamente")
            return redirect('/?fresh=true')
        except Exception as e:
            logger.error(f"Error al limpiar la sesión: {str(e)}")
            return JsonResponse({'error': f'Error al limpiar la sesión: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)