import numpy as np

from pydantic import BaseModel
import pandas as pd


class MachineLearningResponse(BaseModel):
    stade: str


class HealthResponse(BaseModel):
    status: bool




class MachineLearningDataInput(BaseModel):
    choc_de_pointe: bool 
    mollets_souples: bool       
    anemie: bool                
    creatinine: float      
    sodium: float              
    calcium: float             
    age: int
    creatinine_mg_L: float
    sex : str

    def calcul_dfge(self,creatinine_mg_L, age, sexe):
        cr = creatinine_mg_L * 88.4
        if sexe == 'F':
            k, alpha, sex_factor = 61.9, -0.329, 1.018
        else:
            k, alpha, sex_factor = 79.6, -0.411, 1.0

        cr_k = cr / k if k != 0 else 0
        min_ratio = min(cr_k, 1) if cr_k != 0 else 1
        max_ratio = max(cr_k, 1) if cr_k != 0 else 1

        return 141 * np.power(min_ratio, alpha) * np.power(max_ratio, -1.209) * \
            np.power(0.993, age) * sex_factor * 1.159
            
            
    
    def get_df(self):
        # Créer un DataFrame avec une seule ligne, chaque attribut comme une colonne
        return {
            'choc_de_pointe': self.choc_de_pointe,
            'mollets_souples': self.mollets_souples,
            'anemie': self.anemie,
            'creatinine': self.creatinine,
            'sodium': self.sodium,
            'calcium': self.calcium,
            'dfge': self.calcul_dfge(self.creatinine_mg_L, self.age, self.sex),  # sexe par défaut 'F'
        }
    def get_np_array(self):
        return np.array(list(self.get_df().values())).reshape(1, -1)