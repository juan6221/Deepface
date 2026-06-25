# -*- coding: utf-8 -*-
from deepface import DeepFace
import cv2
import numpy as np
import base64
import os
import tempfile

GENDER_LABELS_ES = {
    "Man":   "Hombre",
    "Woman": "Mujer",
}

RACE_LABELS_ES = {
    "asian":           "Asiático",
    "indian":          "Indio",
    "black":           "Afrodescendiente",
    "white":           "Caucásico",
    "middle eastern":  "Oriente Medio",
    "latino hispanic": "Latino / Hispano",
}


def convert_numpy_to_python(obj):
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {convert_numpy_to_python(k): convert_numpy_to_python(v)
                for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_to_python(item) for item in obj]
    else:
        return obj


def analyze_image(image_path: str) -> list[dict]:
    try:
        results = DeepFace.analyze(
            img_path=image_path,
            actions=["age", "gender", "emotion", "race"],
            enforce_detection=False,
            detector_backend="retinaface",
            silent=True,
        )
        if not results:
            raise ValueError("No se detectó ningún rostro.")
    except Exception as e:
        raise ValueError(f"Error al analizar la imagen: {str(e)}")

    faces = []
    for r in results:
        r_clean = convert_numpy_to_python(r)
        dominant_gender = r_clean["dominant_gender"]
        dominant_race   = r_clean["dominant_race"]

        face_data = {
            "genero":            GENDER_LABELS_ES.get(dominant_gender, dominant_gender),
            "genero_confianza":  round(float(r_clean["gender"][dominant_gender]), 1),
            "raza_dominante":    RACE_LABELS_ES.get(dominant_race, dominant_race),
            "edad_estimada":     int(r_clean.get("age", 0)),
            "emocion":           r_clean.get("dominant_emotion", "Neutral"),
            "emociones_detalle": [
                {"nombre": k, "porcentaje": round(float(v), 1)}
                for k, v in r_clean.get("emotion", {}).items()
            ],
            "razas_detalle": {
                k: round(float(v), 1)
                for k, v in r_clean.get("race", {}).items()
            },
            "region": r_clean.get("region", {})
        }
        faces.append(face_data)
    return faces


def analyze_from_bytes(image_bytes: bytes) -> tuple[list[dict], str]:
    # Usar tempfile para evitar problemas con rutas que tienen acentos
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        # Verificar que el archivo se escribió correctamente
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise ValueError("No se pudo guardar la imagen temporal.")

        faces = analyze_image(tmp_path)

        # Leer la imagen para anotar
        img = cv2.imread(tmp_path)
        if img is None:
            # Si cv2 falla, crear imagen en blanco
            img = np.zeros((100, 100, 3), dtype=np.uint8)

        annotated = draw_annotations(img.copy(), faces)
        _, buffer  = cv2.imencode(".jpg", annotated)
        img_b64    = base64.b64encode(buffer).decode("utf-8")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return faces, img_b64


def draw_annotations(img: np.ndarray, faces: list[dict]) -> np.ndarray:
    for i, face in enumerate(faces, start=1):
        r = face.get("region", {})
        if not r:
            continue
        x, y, w, h = int(r.get("x",0)), int(r.get("y",0)), int(r.get("w",0)), int(r.get("h",0))
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 200, 100), 3)
        cv2.putText(img, f"Rostro {i}", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
    return img