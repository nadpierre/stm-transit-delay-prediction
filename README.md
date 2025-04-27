# STM Transit Delay Prediction

## Dataset

[STM Developers](https://www.stm.info/en/about/developers)
Real-time General Transit Feed Specification (GTFS) from API
Downloaded Scheduled GTFS (updated weekly)
[Weather Forecast API](https://open-meteo.com/en/docs)

## Libraries Requirements

- matplotlib
- numpy
- pandas
- protobuf
- requests
- sklearn
- xgboost

## Methods & Models

Collecting every hour from late april to early may

Mean decrease in inpurity (MDI)

SHAP (SHapley Additive exPlanations) values are a method from game theory to explain the output of a machine learning model, especially how much each feature contributes to a specific prediction.

## Future work

Ideally 30 min but too much data to handle (add this to presentation)
Model is overfitted to late april and early may. It would have been ideal to collect data all year
If collected all year, another feature to add would be if it's a holiday
Time-series analysis?

## Featured Deliverables

- Notebooks
- Model
- Presentation
