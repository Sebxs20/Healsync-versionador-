from django.shortcuts import render
from django.http import JsonResponse
import re
from hospital.models import Patient, Doctor

# ------------------ 1. BASE DE CONOCIMIENTOS (SÍNTOMAS Y PRIMEROS AUXILIOS) ------------------
SYMPTOM_KNOWLEDGE = {
    "dolor de cabeza": {
        "keywords": ["dolor de cabeza", "cefalea", "me duele la cabeza", "cabeza", "migraña"],
        "recommendation": "Entiendo, los dolores de cabeza son muy molestos. 🧠 Mi recomendación es que descanses en un lugar oscuro y silencioso, tomes agua y, si es necesario, un analgésico suave como paracetamol. <b>Si el dolor es muy intenso o no se quita en 2 días, sería bueno que le avises a tu doctor.</b>"
    },
    "fiebre": {
        "keywords": ["fiebre", "temperatura", "calentura", "escalofríos", "38"],
        "recommendation": "La fiebre es una señal de que tu cuerpo está combatiendo algo. 🌡️ Lo más importante es que te mantengas hidratado y uses paños fríos en la frente y la nuca. <b>Si tu temperatura supera los 38.5°C o sientes que te falta el aire, no esperes, acude a urgencias de inmediato.</b>"
    },
    "tos": {
        "keywords": ["tos", "carraspera", "garganta irritada"],
        "recommendation": "La tos puede ser por alergias o un resfriado. Toma miel con limón para aliviar la garganta y evita los cambios bruscos de temperatura. 🍯 <b>Ojo: Si toses con flema verde o amarilla, podría ser una infección, así que mejor consulta a tu médico.</b>"
    },
    "dolor de estómago": {
        "keywords": ["dolor de estómago", "dolor de barriga", "gastritis", "acidez", "estómago", "barriga", "náuseas"],
        "recommendation": "Eso suena muy incómodo. 🤢 Evita las comidas pesadas, picantes o muy grasosas por unas horas. Tómate una infusión de manzanilla. <b>Si el dolor se vuelve punzante o no te deja ni moverte, por favor, acude al médico para descartar algo más serio.</b>"
    },
    "gripe": {
        "keywords": ["gripe", "influenza", "malestar general", "dolor muscular"],
        "recommendation": "La gripe te deja sin energía, lo sé. 😮‍💨 Necesitas reposo absoluto en cama y beber muchos líquidos (caldos, jugos, agua). El paracetamol te ayudará con los dolores musculares. <b>Si en 3 días no notas mejoría, visita a tu doctor.</b>"
    },
    "resfriado": {
        "keywords": ["resfriado", "catarro", "congestión nasal", "mocos"],
        "recommendation": "Los resfriados son molestos pero comunes. 🤧 Lávate las manos seguido, usa pañuelos desechables y descansa mucho. Si la congestión nasal te molesta mucho, los descongestionantes de venta libre pueden ayudarte."
    },
    "dolor de espalda": {
        "keywords": ["dolor de espalda", "lumbalgia", "ciática", "espalda"],
        "recommendation": "El dolor de espalda es de lo más común. 🧘‍♂️ Aplica hielo en la zona los primeros 2 días, y luego cambia a calor (bolsa de agua caliente). <b>Evita levantar peso y trata de dormir de lado con una almohada entre las rodillas para alinear tu columna.</b>"
    },
    "alergia": {
        "keywords": ["alergia", "picazón", "rinitis", "estornudos", "alérgico"],
        "recommendation": "Las alergias son muy irritantes. 🤧 Trata de evitar el polvo y los alérgenos (como el pelo de mascotas). Si tienes antihistamínicos recetados, úsalos. <b>¡Cuidado! Si sientes que se te hincha la garganta o te cuesta respirar, busca ayuda médica ya.</b>"
    }
}

# ------------------ 2. ENFERMEDADES CRÓNICAS Y TEÓRICAS (CON TRATAMIENTO) ------------------
DISEASE_KNOWLEDGE = {
    "diabetes": {
        "keywords": ["diabetes", "azúcar", "glucosa", "diabético", "insulina", "tipo 1", "tipo 2", "prediabetes"],
        "info": "<b>¿Qué es la Diabetes?</b><br>La diabetes es una enfermedad crónica que ocurre cuando el páncreas no produce suficiente insulina o cuando el cuerpo no puede usar la insulina que produce de manera eficaz.<br><br><b>Síntomas comunes:</b> Sed excesiva, micción frecuente, hambre constante, pérdida de peso inexplicable y cansancio extremo.<br><br><b>💊 Tratamiento (Pastillas vs Inyecciones):</b><br>- <b>Tipo 1:</b> Se trata estrictamente con <b>inyecciones de insulina</b> diarias.<br>- <b>Tipo 2:</b> Se controla con <b>pastillas orales</b> (como metformina), cambios en la dieta y ejercicio. En etapas avanzadas, puede requerir inyecciones.<br><br><b>⚕️ Recomendación:</b> Es fundamental medir tu glucosa a diario y visitar a tu endocrinólogo regularmente."
    },
    "hipertension": {
        "keywords": ["hipertensión", "presión alta", "tensión alta", "presión arterial"],
        "info": "<b>¿Qué es la Hipertensión?</b><br>Es el aumento sostenido de la presión arterial. Se le conoce como el 'asesino silencioso' porque muchas veces no da síntomas hasta que ocurre un daño grave.<br><br><b>Síntomas:</b> Puede causar dolores de cabeza, mareos, visión borrosa o sangrado nasal (aunque a menudo es asintomática).<br><br><b>💊 Tratamiento:</b><br>- Se trata principalmente con <b>pastillas antihipertensivas</b> (diuréticos, betabloqueantes, inhibidores de la ECA).<br>- No suele tratarse con inyecciones, a menos que sea una crisis hipertensiva en un hospital.<br><br><b>⚕️ Recomendación:</b> Reduce el consumo de sal, haz ejercicio cardiovascular diario y toma tu medicación exactamente como la recetó tu doctor."
    },
    "asma": {
        "keywords": ["asma", "falta de aire", "silbido al respirar", "bronquitis", "inhalador", "broncodilatador"],
        "info": "<b>¿Qué es el Asma?</b><br>Es una enfermedad inflamatoria crónica de las vías respiratorias. Causa episodios de sibilancias, falta de aire y opresión en el pecho.<br><br><b>💊 Tratamiento:</b><br>- <b>Inhaladores (no son inyecciones, pero son aplicación directa):</b> Se usan <b>inhaladores</b> de rescate (broncodilatadores) para aliviar los ataques, y de control (corticosteroides) para prevenir.<br>- El tratamiento siempre es inhalado; rara vez se usan pastillas orales para el asma (solo en casos muy específicos).<br><br><b>⚕️ Recomendación:</b> Siempre lleva tu inhalador de rescate contigo y evita los alérgenos desencadenantes (polen, polvo, humo)."
    },
    "colesterol": {
        "keywords": ["colesterol", "colesterol alto", "lípidos", "triglicéridos"],
        "info": "<b>¿Qué es el Colesterol Alto?</b><br>Es la acumulación de grasa (colesterol y triglicéridos) en la sangre, lo que puede obstruir las arterias y aumentar el riesgo de infartos.<br><br><b>💊 Tratamiento:</b><br>- Se controla con <b>pastillas</b> (estatinas, como la atorvastatina).<br>- Es fundamental cambiar la alimentación: reducir carnes rojas y fritos, y aumentar el consumo de verduras y pescado.<br>- No se usan inyecciones para esto, salvo en casos de hipercolesterolemia familiar grave.<br><br><b>⚕️ Recomendación:</b> Hazte chequeos de perfil lipídico al menos una vez al año."
    }
}

# ------------------ 3. VISTA DEL CHATBOT (CON CORRECCIÓN DE DOCTOR) ------------------
def chatbot_view(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '').lower().strip()
        
        # --- 1. DETECCIÓN DE SALUDOS ---
        greetings = ["hola", "buen día", "buenas", "qué tal", "hey", "buenas tardes", "buenas noches"]
        for g in greetings:
            if g in user_message:
                response = "¡Hola! 👋 Soy HealthSync, tu asistente médico virtual.<br>¿Cómo te sientes hoy? Si quieres, puedes contarme qué síntoma tienes o preguntarme sobre alguna enfermedad (por ejemplo: diabetes, hipertensión, asma)."
                return JsonResponse({'response': response})

        # --- 2. DETECCIÓN DE AYUDA ---
        if "ayuda" in user_message or "¿qué haces" in user_message:
            response = "🤖 <b>¡Claro que sí, te ayudo!</b><br><br>Puedes escribirme lo siguiente:<br>- <b>Un síntoma:</b> Dolor de cabeza, fiebre, tos, etc. Te daré recomendaciones iniciales.<br>- <b>Una enfermedad:</b> Diabetes, hipertensión, asma o colesterol. Te explicaré en qué consiste y cómo se trata (pastillas vs inyecciones).<br>- <b>Tu número de teléfono</b> (si estás logueado): Para decirte quién es tu doctor asignado.<br><br>¿Con qué te puedo apoyar hoy? 🩺"
            return JsonResponse({'response': response})

        # --- 3. Lógica de detección de síntomas o enfermedades ---
        recommendation = "Lo siento, no reconozco ese síntoma o condición. 🤔 Por seguridad, te recomiendo que consultes a un médico presencialmente para tener un diagnóstico preciso. Si tienes una emergencia, llama al 911."
        
        # 3A. Buscar en ENFERMEDADES TEÓRICAS
        detected_disease = None
        for disease, data in DISEASE_KNOWLEDGE.items():
            for keyword in data["keywords"]:
                if re.search(r'\b' + re.escape(keyword) + r'\b', user_message):
                    detected_disease = disease
                    recommendation = data["info"]
                    break
            if detected_disease:
                break
                
        # 3B. Si no encontró enfermedad, buscar en SÍNTOMAS
        detected_symptom = None
        if not detected_disease:
            for symptom, data in SYMPTOM_KNOWLEDGE.items():
                for keyword in data["keywords"]:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', user_message):
                        detected_symptom = symptom
                        recommendation = data["recommendation"]
                        break
                if detected_symptom:
                    break

        # --- 4. Lógica para identificar al paciente ---
        found_patient = None
        if request.user.is_authenticated:
            try:
                found_patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                pass

        if not found_patient:
            phone_match = re.search(r'\b(\d{7,15})\b', user_message)
            if phone_match:
                patient_phone = phone_match.group(1)
                try:
                    found_patient = Patient.objects.filter(mobile=patient_phone).first()
                except:
                    pass

        # --- 5. Consultar Base de Datos (Doctor Asignado) - CORREGIDO ---
        doctor_info = ""
        if found_patient:
            if found_patient.assignedDoctorId:
                try:
                    doctor_id = int(found_patient.assignedDoctorId)
                    
                    # CORRECCIÓN AQUÍ: Se usa 'user_id' en lugar del 'id' primario del doctor
                    doctor = Doctor.objects.get(user_id=doctor_id)
                    
                    if doctor:
                        if doctor.mobile:
                            doctor_info = f"<br><br><b>👨‍⚕️ Tu doctor asignado es:</b> {doctor.get_name}<br><b>📞 Teléfono:</b> {doctor.mobile} <br> <b> Llama a tu médico si es necesario asistir a una consulta </b>"
                        else:
                            doctor_info = f"<br><br><b>👨‍⚕️ Tu doctor asignado es:</b> {doctor.get_name}<br><b>📞 Teléfono:</b> No registrado."
                except (Doctor.DoesNotExist, ValueError):
                    doctor_info = "<br><br>⚠️ *El doctor asignado no se encuentra en la base de datos.*"
            else:
                doctor_info = "<br><br>📌 *No tienes un doctor asignado actualmente.*"
        else:
            if not request.user.is_authenticated:
                doctor_info = "<br><br>📌 *Para saber quién es tu doctor, inicia sesión o escribe tu teléfono.*"

        # --- 6. Construir la respuesta final ---
        final_response = f"{recommendation}{doctor_info}"
        return JsonResponse({'response': final_response})
        
    return render(request, 'chatbot/chatbot.html')