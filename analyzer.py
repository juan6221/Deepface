# -*- coding: utf-8 -*-
from deepface import DeepFace
import cv2
import numpy as np
import base64

GENDER_LABELS_ES = {"Man": "Hombre", "Woman": "Mujer"}
RACE_LABELS_ES = {
    "asian": "Asiático", "indian": "Indio", "black": "Afrodescendiente",
    "white": "Caucásico", "middle eastern": "Oriente Medio", "latino hispanic": "Latino / Hispano",
}

def convert_numpy_to_python(obj):
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)): return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)): return float(obj)
    elif isinstance(obj, np.ndarray): return obj.tolist()
    elif isinstance(obj, dict): return {convert_numpy_to_python(k): convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)): return [convert_numpy_to_python(i) for i in obj]
    else: return obj

def enhance_image(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def analyze_from_bytes(image_bytes: bytes) -> tuple[list[dict], str]:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("No se pudo decodificar la imagen.")
    img = enhance_image(img)
    try:
        results = DeepFace.analyze(
            img_path=img,
            actions=["age", "gender", "emotion", "race"],
            enforce_detection=True,
            detector_backend="retinaface",
            silent=True,
            align=True,
        )
    except Exception as e:
        raise ValueError(f"Error al analizar: {str(e)}")
    faces = []
    for r in results:
        r = convert_numpy_to_python(r)
        dg = r["dominant_gender"]
        dr = r["dominant_race"]
        faces.append({
            "genero": GENDER_LABELS_ES.get(dg, dg),
            "genero_confianza": round(float(r["gender"][dg]), 1),
            "raza_dominante": RACE_LABELS_ES.get(dr, dr),
            "edad_estimada": int(r.get("age", 0)),
            "emocion": r.get("dominant_emotion", "Neutral"),
            "region": r.get("region", {}),
        })
    annotated = img.copy()
    for i, face in enumerate(faces, 1):
        reg = face.get("region", {})
        if reg:
            x, y, w, h = int(reg.get("x",0)), int(reg.get("y",0)), int(reg.get("w",0)), int(reg.get("h",0))
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (255, 200, 100), 3)
            cv2.putText(annotated, f"Rostro {i}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
    _, buffer = cv2.imencode(".jpg", annotated)
    return faces, base64.b64encode(buffer).decode("utf-8")