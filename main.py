# %%

import os
import pandas as pd 
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import random
import math
import datetime
import geopy.distance
import json 
from fastapi import FastAPI
import warnings
warnings.filterwarnings("ignore")


from modules.pre_processing import *
from modules.route_opt import create_data_model,route_calc,plot_solution

#%%

app = FastAPI()

days = [ 
    "2023-03-03",
    "2023-03-13",
    "2023-03-14",
    "2023-03-15",
    "2023-03-16",
    "2023-03-17",
    "2023-03-20",
    "2023-03-21",
    "2023-03-22",
    "2023-03-23",
    "2023-03-24",
    "2023-03-25",
    "2023-03-27",
    "2023-03-28",
    "2023-03-29",
    "2023-03-30",
    "2023-03-31"
    ]

#%%
@app.get("/")
def echo():
    return "We are runnig!"

@app.get("/route_opt/{day}")
def run (day):
    # Imputs
    docs_file_path = "docs.json"
    #day = "2023-03-25"
    info_cd_list = [("Centro De Distribuição","AVENIDA LOURENÇO BELLOLI",0,0,-23.498034, -46.780126)]
    biggest_travel_allowed = 3.5 

    days = [ 
    "2023-03-03",
    "2023-03-13",
    "2023-03-14",
    "2023-03-15",
    "2023-03-16",
    "2023-03-17",
    "2023-03-20",
    "2023-03-21",
    "2023-03-22",
    "2023-03-23",
    "2023-03-24",
    "2023-03-25",
    "2023-03-27",
    "2023-03-28",
    "2023-03-29",
    "2023-03-30",
    "2023-03-31"
    ]

    """Stores the data for the problem."""
    data = {}
    data['vehicle_capacities'] = [ 500,  500,  500,  500,   500, 500,  500,  500,  500,   500,  500,  500,  500,  500,   500, 500,  500,  500,  500,   500,
                                1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,  1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 
                                1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500,  1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 
                                6500, 6500, 6500, 6500, 6500, 6500, 6500, 6500, 6500, 6500,  6500, 6500, 6500, 6500, 6500, 6500, 6500, 6500, 6500, 6500 ]
    data['num_vehicles'] = 80
    data['depot'] = 0
    if day not in days:
        print('no on list')
        return f'{day} is not on the list, please pick one day of the list {days}'
    day = day.replace("-","/")
    print(f"simulação para o dia {day}")
    docs_df_normalized = read_and_normalize_docs_file(docs_file_path)
    docs_df_normalized_with_dates = create_date_fields (docs_df_normalized)
    docs_df_normalized_with_dates = drop_docs_with_overcapacity(docs_df_normalized_with_dates,data,day)
    deliveries_grouped_by_location = group_deliveries_location_per_day(day,docs_df_normalized_with_dates)
    deliveries_grouped_by_location_with_coords = add_coords(docs_df_normalized,deliveries_grouped_by_location)
    deliveries_grouped_by_location_with_coords = check_and_ajust_location_with_overcapacity(deliveries_grouped_by_location_with_coords,docs_df_normalized_with_dates,data,day)
    deliveries_df =add_dc_info(info_cd_list,deliveries_grouped_by_location_with_coords)

    coords = deliveries_df[["coords.lat","coords.lng"]]
    deslocamento = create_matrix_distances_in_hours(coords,avg_kmh=60)

    deliveries_df, location_out_of_range_index_list =  dropp_location_out_range (deslocamento, biggest_travel_allowed,deliveries_df)
    deliveries_df = deliveries_df.reset_index(drop=True)
    
    disntance_df = create_matrix_distances(coords)
            
    demands_list = deliveries_df["peso_total"].astype(int).to_list()
    data['demands'] = demands_list
    data['distance_in_hours_matrix'] = deslocamento.drop(columns=location_out_of_range_index_list).drop(index=location_out_of_range_index_list).to_numpy()
    data['distance_matrix'] = disntance_df.drop(columns=location_out_of_range_index_list).drop(index=location_out_of_range_index_list).to_numpy()

    try:
        data, manager, routing, solution,plans = route_calc(data,max_hours=8,deliveries_df = deliveries_df)
        return(plans)
    
    except:
        print("No Solutions")
        return("No Solutions")
#%%
