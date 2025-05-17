# STM Transit Delay Prediction

## Introduction

The _Société de transport de Montréal (STM)_ is Montreal’s public transport agency. The network contains four subway lines and 235 bus routes. The STM is one the biggest transit systems in Canada and North America.

## Description

The objective of this project is to build a machine learning model that predicts, in seconds, the STM transit delays with the best accuracy.

## Dataset

The data comes from three different sources:

- [STM Website](https://www.stm.info/en/info/networks/bus) to collect the route types through web scraping.
- [STM General Transit Feed Specification (GTFS)](https://www.stm.info/en/about/developers) to collect the real-time trip updates and schedules.
- [Open-Meteo API](https://open-meteo.com/en/docs) to collect the weather archive and forecast.

The cleaned dataset contains a total of 7,530,892 rows and 27 columns.

## Methods & Models

### Data Preprocessing

- There were extreme delay outliers of -10000 and 50000 seconds, which have been removed.
- Due to the large volume of data, the majority has been used as past data, to calculate the average delay per stop. The most recent 1.5 Million rows have been kept for data modeling.
- Temporal feature extraction was used to engineer features like `time_of_day` or `is_peak_hour`.
- The categorial features have been encoded with One-Hot Encoding.

### Models Tested

The following tree-based regression models have been tested in this project: **XGBoost**, **LightGBM** and **CatBoost**. They have been selected because they are more suitable for high-cardinality, non-linear and mixed data. Also, they have a shorter fitting time for large datasets.

### Evaluation Metrics

- Mean Average Error (MAE)
- Root Mean Squared Error (RMSE)
- Coefficient of Determination (R²)
- Feature Importances
- SHapley Additive exPlanations (SHAP) analysis for interpretability

## Results

- The best performing model is **XGBoost** with a MAE of 58.64, a RMSE of 115.39 and a R² of 0.4526.
- The higher RMSE compared to MAE suggests that there are some significant prediction errors that influence the overall error metric.
- The R² is not very high but it's understandable, considering how random transit delays can be (weather, vehicle breakdown, accidents, etc.)

## Future Improvements

- Add third degree feature interactions
- Use a weighed and/or a quantile regression model because the extreme delays were underestimated.
- Insert the data into a database
- The model is overfitted to the time period the data was collected. It would have been ideal to collect data all year round.
- If there was a year worth of data, other time-based features like `month` and `is_holiday` could have been added.
- Adding events (concerts, festivals, sports events) and traffic incidents would enrich the model.
- The results showed that delay is highly dependent on past performance. Exploring time-series models would have been interesting.
- Explore advanced ensemble methods or deep learning models.

## Featured Notebooks

- [Data Collection and Cleaning](./notebooks/data_cleaning.ipynb)
- [Data Preprocessing](./notebooks/data_preprocessing.ipynb)
- [Data Modeling](./notebooks/data_modeling.ipynb)

## Project Installation

1. **Clone the repository**

- Open your terminal or command prompt.
- Navigate to the directory where you want to install the project.
- Run the following command to clone the GitHub repository:
  ```
  git clone https://github.com/nadpierre/stm-transit-delay-prediction.git
  ```

2. **Create a virtual environment**

   ```
   cd stm-transit-delay-prediction
   python<version> -m venv <virtual-environment-name>
   ```

   > [!NOTE]
   > The python version used in this project is 3.13.

3. **Activate the virtual environment**

- Activate the virtual environment based on your operating system
  ```
  source <venv-folder>/bin/activate
  ```

4. **Install dependencies**

- Navigate to the project directory
  ```
  cd <project-directory>
  ```
- Run the following command to install project dependencies:
  ```
  pip install -r requirements.txt
  ```

5. **Import Data**

- Download the zip file from the [following link](https://drive.google.com/file/d/1eXAkEukoViIvppB9rGH-laS75mtNNgbr/view?usp=sharing)
- Extract the archive.
- Move the `data` directory to the root of the project.

6. **Create an environment file**

- Copy the file `.env-sample` and rename it `.env`

7. **Import custom python code**
   To avoid the following error `ModuleNotFoundError: No module named <directory_name>`, run the following commands:

   ```
   set -a
   source .env
   ```

8. **Run the project**

- Execute the following command in the root directory:
  ```
  python app.py
  ```
- Open your browser to `http://127.0.0.1:5000`.

## API Key Setup

To run the script `fetch_stm_trip_updates.py` you need an API key from the STM Developer Hub.

1. Get API key:

- Visit this [STM page](https://www.stm.info/en/about/developers/faq-new-api-hub)
- Follow the instructions to create and account and obtain your API key.

2. Set up API key:

- In the `.env` file, replace the values with your actual API key.
