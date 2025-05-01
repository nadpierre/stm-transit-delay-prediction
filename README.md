# STM Transit Delay Prediction

## Introduction

## Description (to be completed)

## Dataset (to be completed)

[STM Developers](https://www.stm.info/en/about/developers)
Real-time and Scheduled General Transit Feed Specification (GTFS) from API
[Weather Forecast API](https://open-meteo.com/en/docs)
[Tomtom Traffic API](https://developer.tomtom.com/)

Trip updates and vehicle positions were collected from April 27th to May 11th.

## Methods & Models (to be completed)

Don't have access to official historical data, separated dataset in 2 parts (past and current)

Mean decrease in inpurity (MDI)

## Results (to be completed)

## Future Improvements (to be completed)

Model is overfitted to the time period the data was collected. It would have been ideal to collect data all year
If collected all year, another feature to add would be month and if it's a holiday
Add events (concerts, festivals, sports events)
Cross-validate incident distance window (currently 500 meters)

## Featured Deliverables (to be completed)

- Notebooks
- Model
- Presentation

## Getting Started

### Import Data (to be completed)

- Create data directory
- Create models directory

### Project Installation

1. Clone the repository

- Open your terminal or command prompt.
- Navigate to the directory where you want to install the project.
- Run the following command to clone the GitHub repository:
  ```
  git clone https://github.com/nadpierre/stm-transit-delay-prediction.git
  ```

2. Create a virtual environment
   ```
   cd stm-transit-delay-prediction
   python<version> -m venv <virtual-environment-name>
   ```
   Note: the python version used in this project is 3.13.
3. Activate the virtual environment

- Activate the virtual environment based on your operating system
  ```
  source <venv-folder>/bin/activate
  ```

4. Install dependencies

- Navigate to the project directory
  ```
  cd <project-directory>
  ```
- Run the following command to install project dependencies:
  ```
  pip install -r requirements.txt
  ```

5. Run the project

- Start the project by running the appropriate command.
  ```
  python app.py
  ```

6. Access the project

- Open a web browser or the appropriate client to access the project

### API Key Setup

To run some of the scripts of this project you need an API key from STM Developer Hub and TomTom Developer.

1. Get API keys:

- Visit this [STM page](https://www.stm.info/en/about/developers/faq-new-api-hub) and this [TomTom page](https://developer.tomtom.com/knowledgebase/platform/articles/how-to-get-an-tomtom-api-key/).
- Follow the instructions to create and account and obtain your API key.

2. Set up API keys:

- Copy the file `.env-sample` and rename it `.env`
- Replace the values with your actual API keys.

### Usage (to be completed)
