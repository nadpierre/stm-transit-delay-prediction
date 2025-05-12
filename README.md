# STM Transit Delay Prediction

## Description (to be completed)

## Dataset (to be completed)

[STM GTFS](https://www.stm.info/en/about/developers)
Real-time and Scheduled General Transit Feed Specification (GTFS) from API
[Open-Meteo API](https://open-meteo.com/en/docs)

Trip updates and vehicle positions were collected from April 27th to May 11th.

Total of 1 Million rows

## Methods & Models (to be completed)

Don't have access to official historical data, separated dataset in 2 parts (past and current)

Mean decrease in inpurity (MDI)

## Results (to be completed)

## Future Improvements (to be completed)

Model is overfitted to the time period the data was collected. It would have been ideal to collect data all year
If collected all year, another feature to add would be month and if it's a holiday
Add events (concerts, festivals, sports events)
Cross-validate incident distance window (currently 500 meters)

## Featured Notebooks

- Data Collection and Cleaning
- Data Preprocessing
- Data Modeling

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

5. **Import Data and Model**

- Download the zip files from the following links:
  - [Data](https://drive.google.com/file/d/1GrZjOHlRLHzp_8HobkqwjebAieV8boO-/view?usp=sharing)
  - [Model]()
- Extract the archives.
- Move the `data` and `models` directories to the root of the project.

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

### API Key Setup

To run the script `fetch_stm_trip_updates.py` you need an API key from the STM Developer Hub.

1. Get API key:

- Visit this [STM page](https://www.stm.info/en/about/developers/faq-new-api-hub)
- Follow the instructions to create and account and obtain your API key.

2. Set up API key:

- In the `.env` file, Replace the values with your actual API key.
