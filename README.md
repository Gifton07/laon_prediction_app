# Loan Status Prediction

A Machine Learning project that predicts whether a loan application will be **Approved** or **Not Approved** using applicant, financial, and credit-related features.

## Dataset

- **45,000 records**
- **14 columns**
- **10,000 approved loans**
- **35,000 non-approved loans**
- Target: `Loan Status`

## Project Workflow

- Data cleaning and exploratory data analysis
- Outlier detection and handling
- Categorical feature encoding
- Feature scaling using StandardScaler
- Train-test split
- Model training and comparison
- Hyperparameter tuning using GridSearchCV
- Model evaluation using Accuracy, Precision, Recall, F1 Score, and Confusion Matrix
- Model saving using Joblib

## Models Used

- Logistic Regression
- KNN
- Decision Tree
- SVM
- Random Forest

## Best Model

**Random Forest**

| Metric | Score |
|---|---:|
| Accuracy | 92.52% |
| Precision | 85.68% |
| Recall | 76.22% |
| F1 Score | 80.67% |

The final Random Forest model was saved as `loan_model.pkl`.

## Technologies

Python • Pandas • NumPy • Scikit-learn • Matplotlib • Seaborn • XGBoost • Joblib

