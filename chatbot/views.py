from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from collections import Counter
from fuzzywuzzy import fuzz
import spacy
import warnings
import os
from .models import ChatbotQuery
from patients.models import Patient
warnings.filterwarnings('ignore')
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

class SymptomExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            import subprocess
            subprocess.check_call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
            self.nlp = spacy.load('en_core_web_sm')
    
    def preprocess_text(self, text):
        doc = self.nlp(text.lower())
        tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and token.is_alpha and token.pos_ in ['NOUN', 'ADJ', 'VERB']]
        chunks = [chunk.text.lower() for chunk in doc.noun_chunks]
        return tokens, chunks
    
    def extract_symptoms(self, text, all_symptoms):
        tokens, chunks = self.preprocess_text(text)
        extracted = []
        
        for chunk in chunks:
            best_match = None
            highest_score = 0
            for symptom in all_symptoms:
                score = fuzz.ratio(chunk, symptom.lower())
                if score > highest_score and score > 70:
                    highest_score = score
                    best_match = symptom
            if best_match and best_match not in extracted:
                extracted.append(best_match)
        
        for token in tokens:
            best_match = None
            highest_score = 0
            for symptom in all_symptoms:
                for word in symptom.lower().split():
                    score = fuzz.ratio(token, word)
                    if score > highest_score and score > 70:
                        highest_score = score
                        best_match = symptom
            if best_match and best_match not in extracted:
                extracted.append(best_match)
        
        return extracted if extracted else []

class DiseasePredictionSystem:
    def __init__(self):
        self.models = {
            'LogisticRegression': LogisticRegression(random_state=42),
            'DecisionTreeClassifier': DecisionTreeClassifier(random_state=42),
            'RandomForestClassifier': RandomForestClassifier(random_state=42),
            'SVC': SVC(random_state=42),
            'GaussianNB': GaussianNB(),
            'KNeighborsClassifier': KNeighborsClassifier()
        }
        self.label_encoder = LabelEncoder()
        self.all_symptoms = []
        self.disease_to_specialist = {}
        self.symptom_extractor = SymptomExtractor()
        self._initialize_system()
    
    def _initialize_system(self):
        try:
            data_path = os.path.join(os.path.dirname(__file__), 'dataset', 'Original_Dataset.csv')
            specialist_path = os.path.join(os.path.dirname(__file__), 'dataset', 'Doctor_Specialist.csv')
            
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Dataset file not found: {data_path}")
                
            if not os.path.exists(specialist_path):
                raise FileNotFoundError(f"Specialist data file not found: {specialist_path}")
            
            X, y = self.load_and_preprocess_data(data_path)
            self.train_models(X, y)
            self.load_specialist_data(specialist_path)
        except Exception as e:
            print(f"Error initializing system: {e}")
            raise
    
    def load_and_preprocess_data(self, data_path):
        df = pd.read_csv(data_path)
        symptom_columns = [col for col in df.columns if col.startswith('Symptom_')]
        
        for col in symptom_columns:
            df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]
        
        symptoms = [symptom for col in symptom_columns for symptom in df[col].dropna().unique()]
        self.all_symptoms = list(set([s for s in symptoms if pd.notna(s) and s != 'None']))
        
        X = pd.DataFrame(0, index=range(len(df)), columns=self.all_symptoms)
        for index, row in df.iterrows():
            for col in symptom_columns:
                symptom = row[col]
                if pd.notna(symptom) and symptom != 'None':
                    X.loc[index, symptom.strip()] = 1
                    # print(x.loc[index, symptom.strip()])
                    print(symptom.strip())
                    # X.loc[index, symptom.strip()] = 0
        
        y = self.label_encoder.fit_transform(df['Disease'])
        
        return X, y
    
    def train_models(self, X, y):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        for name, model in self.models.items():
            model.fit(X_train, y_train)
    
    def process_symptoms(self, input_symptoms):
        if not input_symptoms:
            return None
            
        input_df = pd.DataFrame(0, index=[0], columns=self.all_symptoms)
        for input_symptom in input_symptoms:
            best_match = None
            highest_score = 0
            for known_symptom in self.all_symptoms:
                score = fuzz.ratio(input_symptom.lower(), known_symptom.lower())
                if score > highest_score and score > 70:
                    highest_score = score
                    best_match = known_symptom
            if best_match:
                input_df[best_match] = 1
        return input_df
    
    def predict_disease(self, input_symptoms):
        input_df = self.process_symptoms(input_symptoms)
        if input_df is None or input_df.sum().sum() == 0:
            return None, 0
        
        predictions = []
        for name, model in self.models.items():
            prediction = model.predict(input_df)
            predictions.extend(self.label_encoder.inverse_transform(prediction))
        
        disease_counts = Counter(predictions)
        predicted_disease = disease_counts.most_common(1)[0][0]
        confidence = disease_counts[predicted_disease] / len(predictions) * 100
        
        return predicted_disease, confidence
    
    def predict_from_text(self, text):
        if not text or not isinstance(text, str):
            return None, None, None, "Please provide a valid text description of your symptoms."
            
        extracted_symptoms = self.symptom_extractor.extract_symptoms(text, self.all_symptoms)
        
        if not extracted_symptoms:
            return None, None, None, "No symptoms could be extracted from the text. Please be more specific about your symptoms."
        
        disease, confidence = self.predict_disease(extracted_symptoms)
        
        if disease is None:
            return None, None, None, "Could not make a prediction based on the extracted symptoms. Please provide more specific symptoms."
            
        specialist = self.get_specialist(disease)
        
        return disease, confidence, specialist, extracted_symptoms
    
    def load_specialist_data(self, specialist_path):
        try:
            df = pd.read_csv(specialist_path)
            self.disease_to_specialist = dict(zip(df['Disease'], df['Specialist']))
        except Exception as e:
            print(f"Error loading specialist data: {e}")
            self.disease_to_specialist = {}
    
    def get_specialist(self, disease):
        return self.disease_to_specialist.get(disease, 'General Physician')

# Initialize the prediction system
try:
    prediction_system = DiseasePredictionSystem()
except Exception as e:
    print(f"Failed to initialize prediction system: {e}")
    prediction_system = None

def chat_home(request):
    return render(request, 'chatbot/chat.html')

@login_required
def chat_history(request):
    if not hasattr(request.user, 'patient'):
        return redirect('patient_profile_setup')
    
    queries = ChatbotQuery.objects.filter(patient=request.user.patient).order_by('-created_at')
    paginator = Paginator(queries, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'chatbot/chat_history.html', {
        'page_obj': page_obj
    })

@csrf_exempt
def predict_disease(request):
    if request.method == 'POST':
        try:
            if prediction_system is None:
                print("Error: Prediction system not initialized")
                return JsonResponse({
                    'error': 'Disease prediction system is not initialized properly. Please try again later.'
                }, status=500)
                
            symptoms = request.POST.get('symptoms', '')
            if not symptoms:
                print("Error: No symptoms provided")
                return JsonResponse({
                    'error': 'Please provide symptoms'
                }, status=400)
            
            print(f"Processing symptoms: {symptoms}")
            result = prediction_system.predict_from_text(symptoms)
            
            if result is None or len(result) != 4:
                print("Error: Invalid prediction result")
                return JsonResponse({
                    'error': 'Could not process the symptoms. Please try again.'
                }, status=400)
                
            disease, confidence, specialist, extracted_symptoms = result
            
            if isinstance(extracted_symptoms, str):
                print("Error: Invalid extracted symptoms format")
                return JsonResponse({
                    'error': extracted_symptoms
                }, status=400)
            
            if disease is None:
                print("Error: No disease predicted")
                return JsonResponse({
                    'error': 'Could not predict disease from the given symptoms. Please be more specific.'
                }, status=400)
            
            # Save to database if user is logged in
            if request.user.is_authenticated and hasattr(request.user, 'patient'):
                try:
                    ChatbotQuery.objects.create(
                        patient=request.user.patient,
                        query=symptoms,
                        response=f"Predicted Disease: {disease}\nConfidence: {confidence:.2f}%\nSuggested Specialist: {specialist}",
                        disease_predicted=disease,
                        confidence_score=confidence,
                        specialist_suggested=specialist
                    )
                except Exception as e:
                    print(f"Error saving chat history: {e}")
            
            response = {
                'success': True,
                'extracted_symptoms': extracted_symptoms,
                'disease': disease,
                'confidence': f"{confidence:.2f}",
                'specialist': specialist
            }
            
            print("Successful prediction:", response)
            return JsonResponse(response)
            
        except Exception as e:
            print(f"Error in predict_disease view: {e}")
            import traceback
            print("Traceback:", traceback.format_exc())
            return JsonResponse({
                'error': 'An unexpected error occurred. Please try again later.'
            }, status=500)
    
    return JsonResponse({
        'error': 'Only POST requests are allowed'
    }, status=405)
