# Markstrom
# Wed Sep 04 09:43:53 MDT 2019
# 
# This script runs against a CSV file and writes the
# contents into a set of netcdf files, one for each variable. It converts the
# whole CSV file to a netcdf file. If the files are big, this will be very slow.
#
# This one reads from repos/metadata/prms/variables.xml

#from prms_utils import csv_reader
import numpy as np
import csv
import xml.etree.ElementTree as ET
import datetime
import getpass
from netCDF4 import Dataset
import os
import sys

variable_metadata_file_name = "/work/markstro/operat/repos/metadata/prms/variables.xml"
# PRMS output files
dir = "/work/markstro/operat/setup/test/NHM-PRMS_CONUS/"
#dir = "./"
hru_dir = '/work/markstro/intern_demo/GIS_Data/hrus_all_conus_geo.shp'
seg_dir = '/work/markstro/intern_demo/GIS_Data/segs_all_conus_geo.shp'
outdir = dir + "/output/"
indir = dir + "/input/"
sandbox = dir + "/output/"
#fn = "/work/markstro/operat/setup/test/NHM-PRMS_CONUS/variable_info.json"
hru_lat_fn = indir + "hru_lat.txt"
hru_lon_fn = indir + "hru_lon.txt"
seg_lat_fn = indir + "lat_seg.txt"
seg_lon_fn = indir + "lon_seg.txt"
fill_value = "9.969209968386869e+36"

tz_code = '-05:00'

outvars=['albedo','cap_waterin','contrib_fraction', 'dprst_area_open',
         'dprst_evap_hru','dprst_insroff_hru', 'dprst_seep_hru',
         'dprst_sroff_hru','dprst_stor_hru','dprst_vol_open',
         'dprst_vol_open_frac','dunnian_flow','freeh2o','gwres_flow',
         'gwres_in','gwres_stor','hortonian_flow','hru_actet','hru_impervevap',
         'hru_impervstor','hru_intcpevap','hru_intcpstor','hru_lateral_flow',
         'hru_outflow','hru_ppt','hru_rain','hru_snow','hru_sroffi',
         'hru_sroffp','hru_streamflow_out','infil','intcp_on','net_ppt',
         'net_rain','net_snow','newsnow','perv_actet','pk_depth','pk_ice',
         'pk_precip','pk_temp','pkwater_equiv','potet','pref_flow',
         'pref_flow_stor','prmx','recharge','seg_gwflow','seginc_gwflow',
         'seginc_potet','seginc_sroff','ls','seginc_swrad',
         'seg_inflow','seg_lateral_inflow','segment_delta_flow','seg_outflow',
         'seg_sroff','seg_ssflow','seg_upstream_inflow','slow_flow',
         'slow_stor','snowcov_area','snow_evap','snow_free','snowmelt',
         'soil_moist','soil_moist_tot','soil_rechr','soil_to_gw','soil_to_ssr',
         'sroff','ssres_flow','swrad','tavgf','tmaxf','tminf','transp_on',
         'unused_potet']


# This function copied from onhm-runners/prms_utils/csv_reader.py
# Read a PRMS "output" csv. For these files, there is a remapping in the header line that tells the order of the columns
def read_output(csvfn):
    # figure out the number of features (ncol - 1)
    # figure out the number of timesteps (nrow -1)
    with open(csvfn, 'r') as csvfile:
        spamreader = csv.reader(csvfile)

        header = next(spamreader)
        nfeat = len(header) - 1

        ii = 0
        for row in spamreader:
            ii = ii + 1
        nts = ii

    vals = np.zeros(shape=(nts,nfeat))
    indx = np.zeros(shape=nfeat, dtype=int)
    with open(csvfn, 'r') as csvfile:
        spamreader = csv.reader(csvfile)

        # Read the header line
        header = next(spamreader)
        for ii in range(1,len(header)):
            indx[ii-1] = int(header[ii])

        # print(indx)

        # Read the CSV file values, line-by-line, column-by-column
        ii = 0
        for row in spamreader:
            jj = 0
            kk = 0
            for tok in row:
                # Now skip the date/time fields and put the values into the 2D array
                if jj > 0:
                    try:
                        vals[ii][indx[kk]-1] = float(tok)
                        kk = kk + 1
                    except:
                        print('read_output: ', str(tok), str(ii), str(kk), str(indx[kk]-1))
                else:
                    # Get the base date (ie date of first time step) from the first row of values
                    if ii == 0:
                        base_date = tok
                    else:
                        end_date = tok
                    # print(tok)

                jj = jj + 1
            ii = ii + 1
    return nts, nfeat, base_date, end_date, vals


def read_feature_georef(fn1):
    nfeat = sum(1 for line in open(fn1))
    vals = np.zeros(shape=(nfeat))
    with open(fn1, 'r') as csvfile:
        spamreader = csv.reader(csvfile)
        ii = 0
        for row in spamreader:
            vals[ii] = float(row[0])
            ii = ii + 1
    return vals


def write_variable_block(ncf, name, did, fi, d, s, ou):
    v1 = ncf.createVariable(name, np.float64, did, fill_value=fi)
    v1.long_name = d
    v1.standard_name = s
    v1.units = ou
    return v1


def write_timeseries_block(ncf, name, did, fi, d, s, ou):
    v1 = ncf.createVariable(name, np.float64, ("time", did), fill_value=fi)
    v1.long_name = d
    v1.standard_name = s
    v1.units = ou
    return v1


def write_timeseries_values(vals, nc_var):
    print("write_timeseries_values " + str(len(vals)) + " " + str(len(nc_var)))
    for ii in range(0, len(vals)):
        print(vals[ii])
        nc_var[ii, :] = vals[ii]
        

def read_xml(root, var_name):
    t = root.findall("./variable[@name='" + var_name + "']/type")[0].text
    u = root.findall("./variable[@name='" + var_name + "']/units")[0].text
    d = root.findall("./variable[@name='" + var_name + "']/desc")[0].text
    s = root.findall("./variable[@name='" + var_name + "']/standard_name")[0].text
    fi = root.findall("./variable[@name='" + var_name + "']/fill_value")[0].text
    fo = root.findall("./variable[@name='" + var_name + "']/format")[0].text
    ou = root.findall("./variable[@name='" + var_name + "']/out_units")[0].text
    m = root.findall("./variable[@name='" + var_name + "']/georef/map")[0].text
    mt = root.findall("./variable[@name='" + var_name + "']/georef/type")[0].text
    did = root.findall("./variable[@name='" + var_name + "']/georef/dimid")[0].text
    a = root.findall("./variable[@name='" + var_name + "']/georef/attribute")[0].text
    
    return t,u,d,s,fi,fo,ou,m,mt,did,a


def write_lat_lon(dir, lat_fn, lon_fn, dimid, id_name, name, fill_value,
                      lat_long_name, lat_standard_name, lat_units,
                      lon_long_name, lon_standard_name, lon_units):
    lat_vals = read_feature_georef(lat_fn)
    lon_vals = read_feature_georef(lon_fn)
    nfeats = len(lat_vals)

    ofn = str(dir) + "/output/" + name + "_lat_lon_v1_0.nc"
    try:
        os.remove(ofn)
    except:
        pass
        
    print('writing netcdf file ' + ofn)
    ncf = Dataset(ofn, 'w', format='NETCDF4_CLASSIC')

    ncf.createDimension(dimid, nfeats)

    idx = ncf.createVariable(dimid, np.int32, (dimid), )
    idx.long_name = id_name

    lat = write_variable_block(ncf, name + "_lat", dimid, fill_value,
                                   lat_long_name, lat_standard_name, lat_units)
    lon = write_variable_block(ncf, name + "_lon", dimid, fill_value,
                                   lon_long_name, lon_standard_name, lon_units)

    ncf.conventions = "CF-1.8"
    ncf.history = str(datetime.datetime.now()) + ',' + str(getpass.getuser()) + ',prms_outputs5_ncf.py'
    idx[:] = np.arange(1, nfeats+1, 1)
    lat[:] = lat_vals
    lon[:] = lon_vals
    ncf.close()
    

def write_vars(dir):
    tree = ET.parse(variable_metadata_file_name)
    root = tree.getroot()
    
    
    for var_name in outvars:        
        data_type, prms_units, long_name, cf_standard_name, fill_value, print_format, ncf_units, map_name, feature_type, dim_id, attribute_name = read_xml(root, var_name)
    
#        print(data_type)
#        print(prms_units)
#        print(long_name)
#        print(cf_standard_name)
#        print(fill_value)
#        print(print_format)
#        print(ncf_units)
#        print(map_name)
#        print(feature_type)
#        print(dim_id)
#        print(attribute_name)
    
        dim_list = set()
    
        print("processing " + var_name)
        print("dim_id = " + dim_id)
        dim_list.add(dim_id)
#
        csv_fn = outdir + var_name + ".csv"
        print("reading ", csv_fn)
        nts, nfeats, base_date, end_date, vals = read_output(csv_fn)
        print("nts = ", nts, " nfeats = ", nfeats, ' base_date = ', base_date, " end_date = ", end_date)

        if prms_units == 'inches':
            if ncf_units == 'mm':
                conversion_factor = 25.4
        elif prms_units == 'acres':
            if ncf_units == 'km2':
                conversion_factor = 0.00404686
        elif prms_units == 'acre-inches':
            if ncf_units == 'm3':
                conversion_factor = 102.79015461
        elif prms_units == 'cfs':
            if ncf_units == 'm3/s':
                conversion_factor = 0.028316847
        elif prms_units == 'none':
            if ncf_units == 'None':
                conversion_factor = 1
        elif prms_units == 'decimal fraction':
            if ncf_units == '1':
                conversion_factor = 1
        elif prms_units == 'degrees Celsius':
            if ncf_units == 'degree_Celsius':
                conversion_factor = 1
        else:
            print("conversion_factor for " + prms_units + " not found.")
            exit()
                
        iis = len(vals)
        jjs = len(vals[0])
        for ii in range(0, iis):
            for jj in range(1, jjs):
                vals[ii,jj] = vals[ii,jj] * conversion_factor

        print("done converting vals")

        nhrus = -1
        if 'hruid' in dim_list:
            hru_lat_vals = read_feature_georef(hru_lat_fn)
#            hru_lon_vals = read_feature_georef(hru_lon_fn)
            nhrus = len(hru_lat_vals)


        nsegments = -1
        if 'segid' in dim_list:
            seg_lat_vals = read_feature_georef(seg_lat_fn)
#            seg_lon_vals = read_feature_georef(seg_lon_fn)
            nsegments = len(seg_lat_vals)

# write the ncf file
        ofn = str(dir) + "/output/" + str(end_date) + "_" + var_name + "_out.nc"
        try:
            os.remove(ofn)
        except:
            pass
            
        print('writing netcdf file ' + ofn)
        ncf = Dataset(ofn, 'w', format='NETCDF4_CLASSIC')

        # Write dimensions block
        if nhrus > 0:
            ncf.createDimension('hruid', nhrus)
        if nsegments > 0:
            ncf.createDimension('segid', nsegments)
        ncf.createDimension('time', None)

        # Put in the indexes for the dimensions
        time_idx = ncf.createVariable("time", np.int32, ("time"), )
        time_idx.long_name = "time"
        time_idx.standard_name = "time"
        time_idx.cf_role = "timeseries_id"
        time_idx.units = "days since " + base_date + " 00:00" + tz_code

        if nhrus > 0:
            hru_idx = ncf.createVariable("hruid", np.int32, ("hruid"), )
            hru_idx.long_name = "local model hru id"

        if nsegments > 0:
            seg_idx = ncf.createVariable("segid", np.int32, ("segid"), )
            seg_idx.long_name = "local model seg id"

#        for var_name in var_names:  comment out the loop if one variable per file
        ncf_var = write_timeseries_block(ncf, var_name, dim_id,
                                         fill_value, long_name,
                                         cf_standard_name, ncf_units)
        

        ncf.conventions = "CF-1.8"
        ncf.featureType = "timeSeries"
        ncf.history = str(datetime.datetime.now()) + ',' + str(getpass.getuser()) + ',prms_outputs3_ncf.py'

        # Write data
        time_idx[:] = np.arange(0, nts, 1)
        if nhrus > 0:
            hru_idx[:] = np.arange(1, nhrus+1, 1)
        if nsegments > 0:
            seg_idx[:] = np.arange(1, nsegments + 1, 1)

        if nhrus > 0:
            hru_lat[:] = hru_lat_vals
            hru_lon[:] = hru_lon_vals

        if nsegments > 0:
            seg_lat[:] = seg_lat_vals
            seg_lon[:] = seg_lon_vals

#   for var_name in var_names:
        write_timeseries_values(vals, ncf_var)
        
        ncf.close()
        
        
def main(dir):
    # Write the ncf with the lat/lon for the HRUs and segments
    write_lat_lon(dir, hru_lat_fn, hru_lon_fn, "hruid",
                  "local model hru id", "hru", fill_value,
                  "Latitude of HRU centroid", "hru_latitude", "degrees_north",
                  "Longitude of HRU centroid", "hru_longitude", "degrees_east")
    

    write_lat_lon(dir, seg_lat_fn, seg_lon_fn, "segid",
                  "local model segment id", "seg", fill_value,
                  "Latitude of segment midpoint", "seg_latitude", "degrees_north",
                  "Longitude of segment midpoint", "seg_longitude", "degrees_east")
    
    write_vars(dir)


if __name__ == '__main__':
    dir = "/work/markstro/operat/setup/test/NHM-PRMS_CONUS"
    argc = len(sys.argv) - 1
    # print(argc)

    if argc == 1:
        print('setting dir = ' + sys.argv[1])
        dir = sys.argv[1]

    os.chdir(dir)
    main(dir)
