import os
import mlflow
import mlflow.sklearn
import joblib
from loguru import logger
import pandas as pd

from core.errors import PredictException, ModelLoadException
from core.config import MODEL_NAME, MODEL_PATH, USE_MLFLOW, ARTEFACT_PATH

class MachineLearningModelHandlerScore(object):
    model = None
    scaler = None
    label_encoder = None
    feature_columns = None

    # @classmethod
    # def predict(cls, input, method="predict"):
    #     clf = cls.get_model()
    #     if hasattr(clf, method):
    #         return getattr(clf, method)(input)
    #     raise PredictException(f"'{method}' attribute is missing")
    
    @classmethod
    def predict(cls,input_data,method="predict"):
        """Prédiction de la classe IRC avec les données fournies."""
        model,scaler,label_encoder,feature_columns = cls.get_model()
        # Préparer les données d'entrée sous forme de DataFrame
        input_data = pd.DataFrame([{
            'Na^+ (meq/L)': input_data['sodium'],
            'Ca^2+ (meq/L)': input_data['calcium'],
            'DFGe': input_data['dfge'],
            'Choc de Pointe/Perçu': 1 if input_data['choc_de_pointe'] in ['Oui', 1] else 0,
            'Mollets souples': 1 if input_data['mollets_souples'] in ['Oui', 1] else 0,
            'Anémie': 1 if input_data['anemie']  in ['Oui', 1] else 0
        }])

        # Mise à l’échelle des caractéristiques
        input_data[['Na^+ (meq/L)', 'Ca^2+ (meq/L)', 'DFGe']] = scaler.transform(
            input_data[['Na^+ (meq/L)', 'Ca^2+ (meq/L)', 'DFGe']]
        )

        # Encodage des variables catégorielles en colonnes binaires (dummy encoding)
        input_data = pd.get_dummies(input_data, columns=['Choc de Pointe/Perçu', 'Mollets souples', 'Anémie'])

        # Recréer les colonnes manquantes avec des valeurs à 0
        for col in cls.feature_columns:
            if col not in input_data.columns:
                input_data[col] = 0
        input_data = input_data[feature_columns]  # Assurer l’ordre des colonnes

        # Prédiction
        print(model.predict(input_data))
        pred = model.predict(input_data)[0]
        return label_encoder.inverse_transform([pred])[0]


    @classmethod
    def get_model(cls):
        if cls.model is None:
            cls.model, cls.scaler, cls.label_encoder, cls.feature_columns = cls.load()
        return cls.model,cls.scaler, cls.label_encoder, cls.feature_columns 

    @staticmethod
    def load():
        """Charge le modèle, scaler, label encoder et les colonnes de caractéristiques."""
        model, scaler, label_encoder, feature_columns = None, None, None, None

        # Vérification du paramètre USE_MLFLOW pour charger depuis MLflow
        if USE_MLFLOW:
            model, scaler, label_encoder, feature_columns = MachineLearningModelHandlerScore.load_from_mlflow()
        else:
            model, scaler, label_encoder, feature_columns = MachineLearningModelHandlerScore.load_from_local()

        if not model or not scaler or not label_encoder or not feature_columns:
            message = "Model, scaler, label encoder or feature columns could not be loaded!"
            logger.error(message)
            raise ModelLoadException(message)

        return model, scaler, label_encoder, feature_columns

    @staticmethod
    def load_from_local():
        """Charge le modèle, scaler, label encoder et feature columns depuis le chemin local."""
        if MODEL_PATH.endswith("/"):
            path = f"{MODEL_PATH}{MODEL_NAME}"
        else:
            path = f"{MODEL_PATH}/{MODEL_NAME}"
        
        if not os.path.exists(path):
            message = f"Machine learning model at {path} does not exist!"
            logger.error(message)
            raise FileNotFoundError(message)
        
        # Charger le modèle, scaler, label encoder et feature columns
        model = joblib.load(path)
        scaler = joblib.load(f'{ARTEFACT_PATH}/scalers/scaler.pkl')
        label_encoder = joblib.load(f'{ARTEFACT_PATH}/labels/label_encoder.pkl')
        feature_columns = joblib.load(f'{ARTEFACT_PATH}/features/feature_columns.pkl')

        if not model or not scaler or not label_encoder or not feature_columns:
            message = f"Model, scaler, label encoder or feature columns could not be loaded from {path}!"
            logger.error(message)
            raise ModelLoadException(message)

        logger.info(f"Model, scaler, label encoder, and feature columns loaded successfully from {path}.")
        return model, scaler, label_encoder, feature_columns

    @staticmethod
    def load_from_mlflow():
        """Charge le modèle, scaler, label encoder et feature columns depuis MLflow."""
        try:
            # Assurez-vous que le modèle est disponible dans le serveur MLflow
            logger.info(f"Loading model {MODEL_NAME} from MLflow...")
            model_uri = f"models:/{MODEL_NAME}/latest"  # Utilisation de la version 'latest'
            model = mlflow.sklearn.load_model(model_uri)

            # Charger également scaler, label encoder, et feature columns depuis MLflow
            scaler_uri = f"models:/{MODEL_NAME}_scaler/latest"
            label_encoder_uri = f"models:/{MODEL_NAME}_label_encoder/latest"
            feature_columns_uri = f"models:/{MODEL_NAME}_feature_columns/latest"

            scaler = mlflow.sklearn.load_model(scaler_uri)
            label_encoder = mlflow.sklearn.load_model(label_encoder_uri)
            feature_columns = mlflow.sklearn.load_model(feature_columns_uri)

            if model and scaler and label_encoder and feature_columns:
                logger.info(f"Model, scaler, label encoder, and feature columns loaded successfully from MLflow.")
            return model, scaler, label_encoder, feature_columns
        except Exception as e:
            message = f"Failed to load model, scaler, label encoder or feature columns from MLflow: {str(e)}"
            logger.error(message)
            raise ModelLoadException(message)
