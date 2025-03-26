# PinPoint AI

## Overview
PinPoint AI is a project developed as part of the Further Artificial Intelligence module. This project includes various Python scripts and a Streamlit-based interface for visualizing and analyzing data.

## Folder Structure
The folder contains the following files:
- `data_loader.py`: Handles data loading and preprocessing.
- `poi_layer.py`: Implements the Point of Interest (POI) layer functionality.
- `streamlitMain.py`: The main Streamlit application for launching the user interface.
- `streamlitDBSCAN.py`: Streamlit interface for DBSCAN clustering.
- `streamlitHexbin.py`: Streamlit interface for hexbin visualizations.
- `streamlitSpider.py`: Streamlit interface for spider chart visualizations.
- `__pycache__/`: Contains compiled Python files.

## How to Run the Streamlit Interface
To launch the Streamlit interface, follow these steps:
1. Open a terminal and navigate to the project directory.
2. Run the following command:
    ```bash
    python -m streamlit run streamlitMain.py
    ```
3. This will start a local Streamlit server. Open the provided localhost URL in your web browser to access the application.

## Requirements
Ensure you have the following installed:
- Python 3.12 or higher
- Streamlit library (`pip install streamlit`)

## Notes
- Make sure all required dependencies are installed before running the application.
- For additional functionality, refer to the individual scripts in the folder.

## License
This project is for educational purposes as part of the Further Artificial Intelligence module.
