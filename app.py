import pandas as pd

from pyongc import ongc, data

import streamlit as st

from streamlit_geolocation import streamlit_geolocation

import utils

from pathlib import Path

st.set_page_config(page_title="Astroscope")

location_data = streamlit_geolocation()

@st.cache_data
def get_common_names(dataframe):
    return [ongc.get(obj["name"]).identifiers[3] for _, obj in dataframe.iterrows()]

@st.cache_data
def load_data():
    return data.all()

def display_info(dso):
    common = dso.identifiers[3]

    with st.sidebar:
        st.header(f":milky_way: {dso.name}")
        if common:
            st.write(', '.join(common))

        with st.spinner("Loading object details..."):
            altaz = utils.get_sky_position(dso.name, location_data)
        if altaz:
            st.table(pd.DataFrame({
                "Magnitude": [f"{dso.magnitudes[1]:.2f}"],
                "Altitude": [utils.float_to_dms(altaz.alt)],
                "Azimuth": [utils.float_to_dms(altaz.az)]
            }).T)
    
            fig, start, end = utils.plot_visibility(dso.name, location_data)
            st.pyplot(fig)

            if start is not None:
                st.write(f"Best observed: {start}h - {end}h")
            else:
                st.write("This object cannot be observed tonight.")
        else:
            st.write("Cannot get object info.")
        st.write(f":information_source: [More information](https://ned.ipac.caltech.edu/cgi-bin/objsearch?objname={dso.name})")

st.title(":telescope: :eyes: Astroscope")

tab1, tab2 = st.tabs(["Overview", "Suggestions"])

with tab1:
    with st.spinner("Loading catalog..."):
        dataframe = load_data()[["name", "type", "const", "vmag"]].sort_values(by="vmag", ascending=True, na_position="last")

        constellations = sorted(set([obj["const"] for _, obj in dataframe.iterrows() if obj["const"]]))
        type_list = set([obj["type"] for _, obj in dataframe.iterrows() if obj["type"]])

        selected_constellations = st.multiselect("Constellations", constellations)
        if selected_constellations:
            dataframe = dataframe[dataframe["const"].isin(selected_constellations)]

        selected_types = st.pills("Object type", type_list, selection_mode="multi")
        if selected_types:
            dataframe = dataframe[dataframe["type"].isin(selected_types)]
        
        upper_mag = st.slider("Magnitude",
                                    min_value=dataframe["vmag"].min(),
                                    max_value=dataframe["vmag"].max(),
                                    value=10.)
        dataframe = dataframe[dataframe["vmag"] <= upper_mag]

        dataframe["common"] = get_common_names(dataframe)

    st.write(f"Total: {len(dataframe)}")
    selection = st.dataframe(data=dataframe, on_select="rerun", selection_mode="single-row")
    if selection['selection']['rows']:
        selected_obj = selection['selection']['rows'][0]
        obj = dataframe.iloc[selected_obj]
        dso = ongc.get(obj["name"])
        display_info(dso)

with tab2:
    if Path("objects.csv").exists():
        objects = pd.read_csv("objects.csv")[["Name", "Type", "Constellation", "Rise", "Set", "Duration", "Magnitude"]].sort_values(by="Magnitude")

        constellations2 = sorted(set([obj["Constellation"] for _, obj in objects.iterrows() if obj["Constellation"]]))

        selected_constellations2 = st.multiselect("Constellations", constellations, key="selected_constellations2")
        if selected_constellations2:
            objects = objects[objects["Constellation"].isin(selected_constellations2)]

        type_list2 = set([obj["Type"] for _, obj in objects.iterrows() if obj["Type"]])
        selected_types2 = st.pills("Object type", type_list2, selection_mode="multi", key="object_types2")
        if selected_types2:
            objects = objects[objects["Type"].isin(selected_types2)]
        
        upper_mag2 = st.slider("Magnitude", key="upper_mag2",
                                    min_value=objects["Magnitude"].min(),
                                    max_value=objects["Magnitude"].max(),
                                    value=10.)

        objects = objects[objects["Magnitude"] <= upper_mag2]

        st.write(f"Total: {len(objects)}")
        selection = st.dataframe(data=objects,
                                 on_select="rerun",
                                 selection_mode="single-row")
        if selection['selection']['rows']:
            selected_obj = selection['selection']['rows'][0]
            obj = objects.iloc[selected_obj]
            dso = ongc.get(obj["Name"])
            display_info(dso)
    else:
        st.write("No object data found.")
