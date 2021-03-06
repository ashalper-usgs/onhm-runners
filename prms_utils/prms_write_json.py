# Markstrom
# Wed Mar 13 09:43:53 MDT 2019

import json

# PRMS output files
dir = "/work/markstro/operat/docker_test/NHM-PRMS_CONUS"
outdir = dir + "/output/"
sandbox = dir + "/sandbox/"
fn = dir + "/" + "variable_info.json"

data = {
    "tz_code":'-05:00',
    "nc_name":'nhm_conus',
    "cdl_file_name":sandbox + 'nhm_output_example.cdl',
    "ncf_file_name":sandbox + 'nhm_output_example.ncf',

    "output_variables": {
        "soil_moist": {
            "long_name": "Soil moisture content",
            "standard_name": "lwe_thickness_of_moisture_content_of_soil_layer",
            "source": outdir + "nhru_soil_moist_tot.csv",
            "fill_value": "9.969209968386869e+36",
            "format": "%.1f",
            "in_units": "inch",
            "out_units": "mm",
            "conversion_factor": "25.4",
            "prms_out_file": outdir + "nhru_soil_moist_tot.csv",
            "georef": {
                "map": '/work/markstro/intern_demo/GIS_Data/hrus_all_conus_geo.shp',
                "type": 'Polygon',
                "dimid":"hruid",
                "attribute": 'nhm_id'
            }
        },
        "lateral_flow": {
            "long_name": "Lateral flow from HRU into the corresponding stream segment",
            "standard_name": "lateral_flow",
            "source": outdir + "nhru_hru_lateral_flow.csv",
            "fill_value": "9.969209968386869e+36",
            "format": "%.1f",
            "in_units": "inch/day",
            "out_units": "mm/day",
            "conversion_factor": "25.4",
            "prms_out_file": outdir + "nhru_hru_lateral_flow.csv",
            "georef": {
                "map": '/work/markstro/intern_demo/GIS_Data/hrus_all_conus_geo.shp',
                "type": 'Polygon',
                "dimid":"hruid",
                "attribute": 'nhm_id'
            }
        },
        "streamflow": {
            "long_name": "Streamflow in channel",
            "standard_name": "water_volume_transport_in_river_channel",
            "source": outdir + "nsegment_seg_outflow.csv",
            "fill_value": "9.969209968386869e+36",
            "format": "%.1f",
            "in_units": "ft3/s",
            "out_units": "m3/s",
            "conversion_factor": "0.0283168",
            "prms_out_file": outdir + "nsegment_seg_outflow.csv",
            "georef": {
                "map": '/work/markstro/intern_demo/GIS_Data/segs_all_conus_geo.shp',
                "type": 'LineString',
                "dimid":"segid",
                "attribute": 'nhm_seg'
            }
        }
    },
    "feature_georef": {
        "hru_lat":{
            "file":"/work/markstro/operat/ncdf_samples/nhm_animation_ncdf/prms_files/hru_lat.txt",
            "dimid":"hruid",
            "long_name": "Latitude of HRU centroid",
            "units":"degrees_north",
            "standard_name": "hru_latitude",
            "fill_value": "9.969209968386869e+36"
        },
        "hru_lon":{
            "file":"/work/markstro/operat/ncdf_samples/nhm_animation_ncdf/prms_files/hru_lon.txt",
            "dimid":"hruid",
            "long_name": "Longitude of HRU centroid",
            "units":"degrees_east",
            "standard_name": "hru_longitude",
            "fill_value": "9.969209968386869e+36"
        },
        "seg_lat":{
            "file": "/work/markstro/operat/ncdf_samples/nhm_animation_ncdf/prms_files/lat_seg.txt",
            "dimid":"segid",
            "long_name": "Latitude of stream segment centroid",
            "units":"degrees_north",
            "standard_name": "segment_latitude",
            "fill_value": "9.969209968386869e+36"
        },
        "seg_lon":{
            "file": "/work/markstro/operat/ncdf_samples/nhm_animation_ncdf/prms_files/lon_seg.txt",
            "dimid":"segid",
            "long_name": "Longitude of stream segment centroid",
            "units":"degrees_east",
            "standard_name": "segment_longitude",
            "fill_value": "9.969209968386869e+36"
        }
    }
}


def main():
    with open(fn, "w") as write_file:
        json.dump(data, write_file)


if __name__ == '__main__':
    main()
