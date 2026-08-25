import os
import joblib
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

app = Flask(__name__, static_folder='static', template_folder='templates')

# Global variables for model and transformers
model = None
scaler = None
le_gender = None
le_home = None
le_prev = None

# Model performance metadata precomputed on full dataset validation
MODEL_METRICS = {
    'algorithm': 'Random Forest Classifier (GridSearchCV)',
    'accuracy': 0.9833,
    'precision': 0.9727,
    'recall': 0.9451,
    'f1_score': 0.9587,
    'roc_auc': 0.9968,
    'dataset_records': 45000,
    'training_records': 39101,
    'confusion_matrix': {
        'tn': 30852, # Approved correctly
        'fp': 213,   # Rejected incorrectly
        'fn': 441,   # Approved incorrectly
        'tp': 7595   # Rejected correctly
    },
    'hyperparameters': {
        'n_estimators': 100,
        'criterion': 'gini',
        'max_depth': 'None (Full Depth)',
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'cross_validation': '5-Fold CV'
    }
}

FEATURE_COLS = [
    'Age', 'Gender', 'Person Income', 'Home Onwership', 'Loan Amount',
    'Loan interest Rate', 'Loan percentage', 'Credit History', 'Credit Score', 'Previous Loan'
]

def init_model_pipeline():
    global model, scaler, le_gender, le_home, le_prev
    
    model_path = os.path.join(os.path.dirname(__file__), 'loan_model.pkl')
    data_path = os.path.join(os.path.dirname(__file__), 'loan_data_new.csv')
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    print("Loading ML model from loan_model.pkl...")
    grid_search = joblib.load(model_path)
    model = grid_search.best_estimator_
    
    print("Fitting encoders and scaler on loan dataset...")
    df = pd.read_csv(data_path)
    df_clean = df[df['Employee Experience'] <= 80].copy()
    df_clean.reset_index(drop=True, inplace=True)
    
    # Notebook scaling transformation (multiplied by 60 to convert to INR currency scale)
    df_clean['Loan Amount'] = df_clean['Loan Amount'] * 60
    df_clean['Person Income'] = df_clean['Person Income'] * 60
    df_clean = df_clean[df_clean['Loan Amount'] < 1000000]
    
    le_gender = LabelEncoder()
    df_clean['Gender'] = le_gender.fit_transform(df_clean['Gender'])
    
    le_home = LabelEncoder()
    df_clean['Home Onwership'] = le_home.fit_transform(df_clean['Home Onwership'])
    
    le_prev = LabelEncoder()
    df_clean['Previous Loan'] = le_prev.fit_transform(df_clean['Previous Loan'])
    
    X = df_clean[FEATURE_COLS]
    scaler = StandardScaler()
    scaler.fit(X)
    
    # Store sorted feature importances
    importances = list(zip(FEATURE_COLS, [float(x) for x in model.feature_importances_]))
    importances.sort(key=lambda x: x[1], reverse=True)
    MODEL_METRICS['feature_importances'] = dict(importances)
    print("Model initialization complete successfully!")

# Initialize pipeline on startup
init_model_pipeline()


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/model-info', methods=['GET'])
def get_model_info():
    metrics = dict(MODEL_METRICS)
    if model is not None and hasattr(model, 'feature_importances_'):
        importances = list(zip(FEATURE_COLS, [float(x) for x in model.feature_importances_]))
        importances.sort(key=lambda x: x[1], reverse=True)
        metrics['feature_importances_list'] = [{'feature': k, 'importance': round(v * 100, 2)} for k, v in importances]
        metrics['feature_importances'] = {k: round(v * 100, 2) for k, v in importances}
    return jsonify({
        'status': 'success',
        'metrics': metrics,
        'feature_names': FEATURE_COLS
    })



@app.route('/api/sample-data', methods=['GET'])
def get_sample_data():
    samples = [
        {
            'id': 'prime',
            'name': 'Prime Professional',
            'tag': 'High Income • Low Risk',
            'age': 34,
            'gender': 'male',
            'person_income': 5500000,
            'currency': 'INR',
            'home_ownership': 'OWN',
            'loan_amount': 350000,
            'loan_interest_rate': 7.5,
            'credit_history': 10,
            'credit_score': 780,
            'previous_loan': 'No'
        },
        {
            'id': 'standard',
            'name': 'Standard Borrower',
            'tag': 'Moderate Income • Prime',
            'age': 29,
            'gender': 'female',
            'person_income': 4200000,
            'currency': 'INR',
            'home_ownership': 'MORTGAGE',
            'loan_amount': 450000,
            'loan_interest_rate': 9.2,
            'credit_history': 6,
            'credit_score': 690,
            'previous_loan': 'No'
        },
        {
            'id': 'subprime',
            'name': 'Subprime Borrower',
            'tag': 'High Debt Ratio • Moderate Risk',
            'age': 25,
            'gender': 'male',
            'person_income': 2400000,
            'currency': 'INR',
            'home_ownership': 'RENT',
            'loan_amount': 550000,
            'loan_interest_rate': 14.5,
            'credit_history': 3,
            'credit_score': 610,
            'previous_loan': 'Yes'
        },
        {
            'id': 'high_risk',
            'name': 'High Default Risk',
            'tag': 'Low Income • High Rate • Past Default',
            'age': 22,
            'gender': 'female',
            'person_income': 1500000,
            'currency': 'INR',
            'home_ownership': 'RENT',
            'loan_amount': 600000,
            'loan_interest_rate': 18.5,
            'credit_history': 1,
            'credit_score': 520,
            'previous_loan': 'Yes'
        }
    ]
    return jsonify({'status': 'success', 'samples': samples})

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON payload provided'}), 400
        
        # Parse inputs
        age = float(data.get('age', 30))
        gender_str = str(data.get('gender', 'male')).lower()
        person_income = float(data.get('person_income', 4000000))
        home_ownership = str(data.get('home_ownership', 'RENT')).upper()
        loan_amount = float(data.get('loan_amount', 400000))
        loan_interest_rate = float(data.get('loan_interest_rate', 10.0))
        credit_history = float(data.get('credit_history', 5))
        credit_score = float(data.get('credit_score', 650))
        previous_loan_str = str(data.get('previous_loan', 'No')).capitalize()
        
        # Convert currency if user submitted in USD (assuming approx 1 USD = 60 dataset scale unit)
        currency = str(data.get('currency', 'INR')).upper()
        if currency == 'USD':
            person_income_scaled = person_income * 60
            loan_amount_scaled = loan_amount * 60
        else:
            person_income_scaled = person_income
            loan_amount_scaled = loan_amount
            
        # Calculate loan percentage (Loan Amount / Income ratio)
        loan_percentage = round(loan_amount_scaled / person_income_scaled, 4) if person_income_scaled > 0 else 1.0
        
        # Encode categorical variables safely
        gender_encoded = 1 if gender_str in ['male', 'm', '1'] else 0
        
        home_map = {'MORTGAGE': 0, 'OTHER': 1, 'OWN': 2, 'RENT': 3}
        home_encoded = home_map.get(home_ownership, 3)
        
        prev_encoded = 1 if previous_loan_str in ['Yes', 'Y', '1', 'True', 'true'] else 0
        
        raw_features = [
            age,
            gender_encoded,
            person_income_scaled,
            home_encoded,
            loan_amount_scaled,
            loan_interest_rate,
            loan_percentage,
            credit_history,
            credit_score,
            prev_encoded
        ]
        
        # Scale features
        df_input = pd.DataFrame([raw_features], columns=FEATURE_COLS)
        scaled_input = scaler.transform(df_input)
        
        # Predict
        prediction_class = int(model.predict(scaled_input)[0]) # 0 = Approved, 1 = Rejected
        probabilities = model.predict_proba(scaled_input)[0]
        
        prob_approved = float(probabilities[0]) # Class 0
        prob_rejected = float(probabilities[1]) # Class 1
        
        # Risk tier determination
        if prob_approved >= 0.75:
            risk_tier = 'Low Risk'
            status_badge = 'APPROVED'
            status_color = 'emerald'
            risk_description = 'Excellent profile. High probability of seamless loan repayment.'
        elif prob_approved >= 0.45:
            risk_tier = 'Moderate Risk'
            status_badge = 'CONDITIONAL APPROVAL'
            status_color = 'amber'
            risk_description = 'Moderate risk profile. Approval may require additional collateral or manual underwriting.'
        else:
            risk_tier = 'High Risk'
            status_badge = 'REJECTED'
            status_color = 'rose'
            risk_description = 'High default probability. Exceeds standard risk thresholds.'
            
        # Feature impact analysis
        drivers = []
        if prev_encoded == 1:
            drivers.append({'feature': 'Previous Loan Default History', 'impact': 'Negative', 'weight': 'High', 'desc': 'Applicant has a previous default on record.'})
        else:
            drivers.append({'feature': 'Clean Credit History', 'impact': 'Positive', 'weight': 'High', 'desc': 'No previous loan default on record.'})
            
        if loan_percentage > 0.25:
            drivers.append({'feature': 'High Loan-to-Income Ratio', 'impact': 'Negative', 'weight': 'High', 'desc': f'Loan represents {loan_percentage*100:.1f}% of annual income.'})
        else:
            drivers.append({'feature': 'Healthy Debt-to-Income Ratio', 'impact': 'Positive', 'weight': 'Medium', 'desc': f'Loan represents only {loan_percentage*100:.1f}% of annual income.'})
            
        if credit_score < 620:
            drivers.append({'feature': 'Subprime Credit Score', 'impact': 'Negative', 'weight': 'High', 'desc': f'Credit score of {int(credit_score)} is below optimal prime range.'})
        elif credit_score >= 700:
            drivers.append({'feature': 'Prime Credit Score', 'impact': 'Positive', 'weight': 'Medium', 'desc': f'Strong credit score of {int(credit_score)}.'})
            
        if loan_interest_rate > 14.0:
            drivers.append({'feature': 'Elevated Interest Rate', 'impact': 'Negative', 'weight': 'Medium', 'desc': f'Interest rate of {loan_interest_rate:.1f}% increases debt burden.'})
            
        return jsonify({
            'status': 'success',
            'prediction': {
                'class': prediction_class,
                'status_badge': status_badge,
                'status_color': status_color,
                'risk_tier': risk_tier,
                'approval_probability': round(prob_approved * 100, 2),
                'rejection_probability': round(prob_rejected * 100, 2),
                'loan_to_income_ratio': round(loan_percentage * 100, 2),
                'risk_description': risk_description,
                'key_drivers': drivers,
                'input_summary': {
                    'age': int(age),
                    'gender': 'Male' if gender_encoded == 1 else 'Female',
                    'person_income': person_income,
                    'person_income_formatted': f"₹{person_income:,.0f}" if currency == 'INR' else f"${person_income:,.0f}",
                    'home_ownership': home_ownership,
                    'loan_amount': loan_amount,
                    'loan_amount_formatted': f"₹{loan_amount:,.0f}" if currency == 'INR' else f"${loan_amount:,.0f}",
                    'loan_interest_rate': loan_interest_rate,
                    'credit_score': int(credit_score),
                    'previous_loan': previous_loan_str
                }
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/batch-predict', methods=['POST'])
def batch_predict():
    try:
        # Generate dynamic batch evaluation on 100 samples from dataset
        data_path = os.path.join(os.path.dirname(__file__), 'loan_data_new.csv')
        df = pd.read_csv(data_path)
        sample_df = df.sample(n=100, random_state=42).copy()
        
        sample_df_clean = sample_df[sample_df['Employee Experience'] <= 80].copy()
        sample_df_clean['Loan Amount'] = sample_df_clean['Loan Amount'] * 60
        sample_df_clean['Person Income'] = sample_df_clean['Person Income'] * 60
        
        g_enc = le_gender.transform(sample_df_clean['Gender'])
        h_enc = le_home.transform(sample_df_clean['Home Onwership'])
        p_enc = le_prev.transform(sample_df_clean['Previous Loan'])
        
        sample_df_clean['Gender'] = g_enc
        sample_df_clean['Home Onwership'] = h_enc
        sample_df_clean['Previous Loan'] = p_enc
        
        X_batch = sample_df_clean[FEATURE_COLS]
        scaled_batch = scaler.transform(X_batch)
        
        preds = model.predict(scaled_batch)
        probs = model.predict_proba(scaled_batch)
        
        approved_count = int(np.sum(preds == 0))
        rejected_count = int(np.sum(preds == 1))
        avg_approval_prob = float(np.mean(probs[:, 0])) * 100
        
        return jsonify({
            'status': 'success',
            'batch_size': len(preds),
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'approved_percentage': round((approved_count / len(preds)) * 100, 1),
            'avg_approval_probability': round(avg_approval_prob, 1),
            'risk_distribution': {
                'low_risk': int(np.sum(probs[:, 0] >= 0.75)),
                'moderate_risk': int(np.sum((probs[:, 0] >= 0.45) & (probs[:, 0] < 0.75))),
                'high_risk': int(np.sum(probs[:, 0] < 0.45))
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    init_model_pipeline()
    app.run(host='0.0.0.0', port=5000, debug=True)
