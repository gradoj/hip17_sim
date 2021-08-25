# hip17_sim
Helium hip17 density scale calculator

hip17.py is a python script that calculates the scaling factor for the helium network. Scaling factors are calculated based off h3 hex hotspot densities as described in the hip. The ```density``` dictionary can be modified to explore the impact of changing these variables. A hotspots.csv file is created from the helium api when hip17.py is first run which can be deleted to get an updated version or hotspots could be manually added to see their impact.   
See https://github.com/helium/HIP/blob/master/0017-hex-density-based-transmit-reward-scaling.md 

To visualize this hip17kml.py uses the hip17 class to display in Google Earth desktop. Google Earth has Network Links https://developers.google.com/kml/documentation/kml_tut#network-links so this script uses a light internal Python webserver to generate kml files for google earth dynamically. Each time the view stops in google earth the density scale is calculated for the current h3 hex. It can take a little time to calculate in dense areas so you might not want to move around too fast.

## Requirements

Python 3
Uber H3 for Python https://github.com/uber/h3-py
Simplekml https://readthedocs.org/projects/simplekml/

## How to Run Visualization

Run the python script with ```python3 hip17kml.py 8001``` Double click or open hip17.kml to make the connection from Google Earth desktop.
This is running with Google Earth set to meters and all other default settings.

## Usage

```import hip17
   sc=hip17.scale_calculator()
   sc.get_scale('8412ccdffffffff')
   sc.get_hotspots(h3hex)
   ```
