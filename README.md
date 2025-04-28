# STM Transit Delay Prediction

## Dataset

[STM Developers](https://www.stm.info/en/about/developers)
Real-time and Scheduled General Transit Feed Specification (GTFS) from API
[GTFS Documentation](https://gtfs.org/documentation/realtime/feed-entities/vehicle-positions/)
[Weather Forecast API](https://open-meteo.com/en/docs)
[Tomtom Traffic API](https://developer.tomtom.com/)

## Libraries Requirements

- haversine
- matplotlib
- numpy
- pandas
- protobuf
- requests
- seaborn
- sklearn
- xgboost

## Methods & Models

Collecting every hour from late april to early may (at least 2 weeks)
Ideally 30 min but too much data to handle (add this to presentation)

Don't have access to official historical data, separated dataset in 2 past (past and current)

Mean decrease in inpurity (MDI)

## Future work

Model is overfitted to late april and early may. It would have been ideal to collect data all year
If collected all year, another feature to add would be if it's a holiday
Add events
Time-series analysis?
Deep learning?
Cross-validate incident distance window

## Featured Deliverables

- Notebooks
- Model
- Presentation
