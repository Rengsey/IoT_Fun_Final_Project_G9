import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import numpy as np


def load_data(file_path):
    data = pd.read_csv(file_path)
    data['Date_Time'] = pd.to_datetime(data['Date_Time']).astype(np.int64) // 10**9
    return data

def train_and_save_models(data, output_dir):

# Inside train_and_save_models function
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    X = data.drop(['Air_Pressure', 'Air_Temperature', 'Temperature', 'Humidity'], axis=1)
    y = data[['Air_Pressure', 'Air_Temperature', 'Temperature', 'Humidity']]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    models = {}
    predictions = {}
    for target in y.columns:
        lr = LinearRegression()
        lr.fit(X_train, y_train[target])
        predictions[target + "_LinearRegression"] = lr.predict(X_test)
        
        svm = SVR(kernel='rbf')
        svm.fit(X_train, y_train[target])
        predictions[target + "_SVM"] = svm.predict(X_test)
        
        models[target] = {'LinearRegression': lr, 'SVM': svm}
        joblib.dump(lr, f'{output_dir}/{target}_LinearRegression.pkl')
        joblib.dump(svm, f'{output_dir}/{target}_SVM.pkl')
    
    evaluate_and_plot(models, X_test, y_test, predictions)

def evaluate_and_plot(models, X_test, y_test, predictions):
    fig, axs = plt.subplots(nrows=4, ncols=2, figsize=(14, 20), sharex=True)
    fig.subplots_adjust(hspace=0.4, wspace=0.2)
    
    for i, target in enumerate(y_test.columns):
        mse_lr = mean_squared_error(y_test[target], predictions[target + "_LinearRegression"])
        r2_lr = r2_score(y_test[target], predictions[target + "_LinearRegression"])
        mae_lr = mean_absolute_error(y_test[target], predictions[target + "_LinearRegression"])
        
        mse_svm = mean_squared_error(y_test[target], predictions[target + "_SVM"])
        r2_svm = r2_score(y_test[target], predictions[target + "_SVM"])
        mae_svm = mean_absolute_error(y_test[target], predictions[target + "_SVM"])

        axs[i, 0].scatter(y_test[target], predictions[target + "_LinearRegression"], alpha=0.5)
        axs[i, 0].plot([y_test[target].min(), y_test[target].max()], [y_test[target].min(), y_test[target].max()], 'k--', lw=2)
        axs[i, 0].set_title(f'{target} - Linear Regression\nMSE: {mse_lr:.2f}, R2: {r2_lr:.2f}, MAE: {mae_lr:.2f}')
        axs[i, 0].set_xlabel('True Values')
        axs[i, 0].set_ylabel('Predictions')

        axs[i, 1].scatter(y_test[target], predictions[target + "_SVM"], alpha=0.5, color='r')
        axs[i, 1].plot([y_test[target].min(), y_test[target].max()], [y_test[target].min(), y_test[target].max()], 'k--', lw=2)
        axs[i, 1].set_title(f'{target} - SVM\nMSE: {mse_svm:.2f}, R2: {r2_svm:.2f}, MAE: {mae_svm:.2f}')
        axs[i, 1].set_xlabel('True Values')
        axs[i, 1].set_ylabel('Predictions')
    
    plt.show()

if __name__ == '__main__':
    data_path = 'C:/Users/USer/Documents/Chulalongkorn_University/2023-2/IoT/IoT-Final-Project/Data_Analysis/IoTCloudServe@TEIN/ModelTraining/test_data_set.csv'
    output_dir = 'C:/Users/USer/Documents/Chulalongkorn_University/2023-2/IoT/IoT-Final-Project/Data_Analysis/IoTCloudServe@TEIN/ModelTraining/models'
    data = load_data(data_path)
    train_and_save_models(data, output_dir)
