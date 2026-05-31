"""
Entrenamiento de modelo de riesgo de mastitis para Mastitrack.

Soporta dos fuentes de datos:
  - Dataset publico de Kaggle (cow_milk_mastitis_dataset.csv)
  - Datos exportados desde Mastitrack (mastitrack_datos_*.csv)

Uso:
    uv run python entrenar.py --kaggle
    uv run python entrenar.py --mastitrack

Genera: output/modelo_mastitis_YYYYMMDD_HHMMSS.joblib (listo para cargar en Mastitrack)
"""

import argparse
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

SCRIPT_DIR = Path(__file__).parent
DATASETS_DIR = SCRIPT_DIR / "datasets"
OUTPUT_DIR = SCRIPT_DIR / "output"
NOMBRES_FEATURES = ["CCS", "Conductividad", "pH", "Temperatura", "Cumplimiento", "Fallas"]


def clasificar_nivel(prob):
    if prob < 0.3:
        return "verde"
    if prob < 0.7:
        return "amarillo"
    return "rojo"


class EntrenadorBase(ABC):
    """Clase base para entrenamiento de modelos de mastitis."""

    nombre_fuente: str

    def __init__(self):
        self.archivo = self._obtener_dataset()
        self.df = pd.read_csv(self.archivo)

    @abstractmethod
    def _obtener_dataset(self) -> Path:
        """Devuelve la ruta al CSV a utilizar."""

    @abstractmethod
    def preparar_features(self) -> np.ndarray:
        """Normaliza features con las mismas formulas que inference.py."""

    @abstractmethod
    def obtener_labels(self) -> np.ndarray:
        """Devuelve el array de labels binarios (0=sano, 1=mastitis)."""

    def entrenar(self):
        print(f"Dataset: {self.archivo.name} ({self.nombre_fuente})")
        y = self.obtener_labels()
        n_pos = int(y.sum())
        n_neg = len(y) - n_pos
        print(f"Registros: {len(self.df)} filas, {n_pos} positivos ({n_pos/len(self.df)*100:.1f}%)")

        if n_pos < 2 or n_neg < 2:
            print(f"\nError: se necesitan al menos 2 registros por clase para entrenar.")
            print(f"  Sanos: {n_neg} | Mastitis: {n_pos}")
            return
        print()

        X = self.preparar_features()
        self._mostrar_medias(X, y)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        print(f"Train: {len(X_train)} | Test: {len(X_test)}")

        modelo = MLPClassifier(
            hidden_layer_sizes=(16, 8),
            activation="relu",
            solver="lbfgs",
            max_iter=1000,
            random_state=42,
            alpha=0.001,
        )
        modelo.fit(X_train, y_train)
        print(f"Iteraciones: {modelo.n_iter_}")
        print(f"Loss: {modelo.loss_:.6f}")
        print()

        self._evaluar(modelo, X_test, y_test)
        self._guardar(modelo)

    def _mostrar_medias(self, X, y):
        print("Features normalizadas (media por clase):")
        for i, nombre in enumerate(NOMBRES_FEATURES):
            media_0 = X[y == 0, i].mean()
            media_1 = X[y == 1, i].mean()
            print(f"  {nombre:15s}  sano={media_0:+.4f}  mastitis={media_1:+.4f}")
        print()

    def _evaluar(self, modelo, X_test, y_test):
        y_pred = modelo.predict(X_test)
        y_proba = modelo.predict_proba(X_test)[:, 1]

        print("=== Reporte de clasificacion ===")
        print(classification_report(y_test, y_pred, target_names=["Sano", "Mastitis"],
                                    zero_division=0))
        print("Matriz de confusion:")
        cm = confusion_matrix(y_test, y_pred)
        print(f"  TN={cm[0][0]:3d}  FP={cm[0][1]:3d}")
        print(f"  FN={cm[1][0]:3d}  TP={cm[1][1]:3d}")
        print()

        print("=== Distribucion semaforo (test) ===")
        for nivel, (lo, hi) in [("Verde", (0, 0.3)), ("Amarillo", (0.3, 0.7)), ("Rojo", (0.7, 1.01))]:
            mask = (y_proba >= lo) & (y_proba < hi)
            n = mask.sum()
            positivos = int(y_test[mask].sum()) if n > 0 else 0
            print(f"  {nivel:10s}: {n:3d} vacas ({positivos} realmente enfermas)")
        print()

        print("=== Ejemplos de prediccion ===")
        idx_sano = np.where(y_test == 0)[0][:5]
        idx_enfermo = np.where(y_test == 1)[0][:5]
        for i in np.concatenate([idx_sano, idx_enfermo]):
            prob = y_proba[i]
            real = "Mastitis" if y_test[i] == 1 else "Sano"
            nivel = clasificar_nivel(prob)
            print(f"  {real:8s} -> prob={prob:.4f} ({nivel})")
        print()

    def _guardar(self, modelo):
        OUTPUT_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = OUTPUT_DIR / f"modelo_mastitis_{ts}.joblib"
        joblib.dump(modelo, archivo)
        print(f"Modelo guardado: {archivo.relative_to(SCRIPT_DIR)}")
        print("Listo para cargar en Mastitrack desde /entrenamiento/")


class EntrenadorKaggle(EntrenadorBase):
    """Entrena con el dataset publico de Kaggle (cow_milk_mastitis_dataset.csv)."""

    nombre_fuente = "kaggle"

    def _obtener_dataset(self) -> Path:
        archivo = DATASETS_DIR / "cow_milk_mastitis_dataset.csv"
        if not archivo.exists():
            raise FileNotFoundError(f"No se encontro {archivo}")
        return archivo

    def preparar_features(self) -> np.ndarray:
        # SCC en el dataset esta en x10^3 cells/mL, multiplicar por 1000
        scc = self.df["Somatic_Cell_Count"] * 1000
        return np.column_stack([
            scc / 1_000_000,
            self.df["Milk_Conductivity"] / 10.0,
            (self.df["Milk_pH"] - 6.0) / 1.0,
            (self.df["Milk_Temperature"] - 37.0) / 3.0,
            np.zeros(len(self.df)),
            np.zeros(len(self.df)),
        ])

    def obtener_labels(self) -> np.ndarray:
        return self.df["class1"].values


class EntrenadorMastitrack(EntrenadorBase):
    """Entrena con datos exportados desde la app Mastitrack."""

    nombre_fuente = "mastitrack"

    def __init__(self):
        super().__init__()
        if "diagnostico_mastitis" not in self.df.columns:
            raise ValueError(
                "El CSV no tiene columna 'diagnostico_mastitis'. "
                "Exporta un CSV nuevo desde la app."
            )
        total = len(self.df)
        self.df = self.df[self.df["diagnostico_mastitis"].notna()].copy()
        self.df["diagnostico_mastitis"] = self.df["diagnostico_mastitis"].astype(int)
        descartados = total - len(self.df)
        if descartados > 0:
            print(f"Filtrados: {descartados} registros sin diagnostico confirmado")

    def _obtener_dataset(self) -> Path:
        csvs = sorted(DATASETS_DIR.glob("mastitrack_datos_*.csv"), key=lambda p: p.stat().st_mtime)
        if not csvs:
            raise FileNotFoundError(
                f"No se encontraron archivos mastitrack_datos_*.csv en {DATASETS_DIR}"
            )
        return csvs[-1]

    def preparar_features(self) -> np.ndarray:
        return np.column_stack([
            self.df["conteo_celulas_somaticas"] / 1_000_000,
            self.df["conductividad_electrica"] / 10.0,
            (self.df["ph"] - 6.0) / 1.0,
            (self.df["temperatura"] - 37.0) / 3.0,
            (100 - self.df["porcentaje_cumplimiento"]) / 100.0,
            self.df["fallas_criticas"] / 5.0,
        ])

    def obtener_labels(self) -> np.ndarray:
        return self.df["diagnostico_mastitis"].values


def main():
    parser = argparse.ArgumentParser(description="Entrenar modelo de riesgo de mastitis")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--kaggle", action="store_true", help="Usar dataset publico de Kaggle")
    grupo.add_argument("--mastitrack", action="store_true", help="Usar datos exportados de Mastitrack")
    args = parser.parse_args()

    if args.kaggle:
        entrenador = EntrenadorKaggle()
    else:
        entrenador = EntrenadorMastitrack()

    entrenador.entrenar()


if __name__ == "__main__":
    main()
