# Markstrom
# Wed Apr 09 09:43:53 MDT 2019

#from prms_utils import csv_reader
import numpy as np
import csv
import json
import datetime
import getpass
from netCDF4 import Dataset
import os
import sys


# This function copied from onhm-runners/prms_utils/csv_reader.py
# Read a PRMS "output" csv. For these files, there is a remapping in the header line that tells the order of the columns


###############################################################################
# DANGER
# This only writes the last line of the output CSV to the ncf !!!
# Only use this for onhm simulation to Makerspace. All they need is the output
# for the last day of the simulation!
# DANGER
###############################################################################

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

    vals = np.zeros(shape=(1,nfeat))
    indx = np.zeros(shape=nfeat, dtype=int)
    with open(csvfn, 'r') as csvfile:
        spamreader = csv.reader(csvfile)

        # Read the header line
        header = next(spamreader)
        for ii in range(1,len(header)):
            indx[ii-1] = int(header[ii])

        # print(indx)
        # skip to last line
        for row in spamreader:
            last = row

        # Read the CSV file values, line-by-line, column-by-column
        jj = 0
        kk = 0
        for tok in last:
            # Now skip the date/time fields and put the values into the 2D array
            if jj > 0:
                try:
                    vals[0][indx[kk]-1] = float(tok)
                    kk = kk + 1
                except:
                    print('read_output: ', str(tok), str(0), str(kk), str(indx[kk]-1))
            else:
                # Get the base date (ie date of first time step) from the first row of values
                base_date = tok
                end_date = tok

            jj = jj + 1
        
    return nts, nfeat, base_date, end_date, vals


def read_feature_georef(dir, cntl, name):
    fn1 = cntl["feature_georef"][name]["file"]
#    print (fn1)

    nfeat = sum(1 for line in open(dir + fn1))
    vals = np.zeros(shape=(nfeat))
    with open(dir + fn1, 'r') as csvfile:
        spamreader = csv.reader(csvfile)
        ii = 0
        for row in spamreader:
            vals[ii] = float(row[0])
            ii = ii + 1
    return vals


def write_variable_block(cntl, ncf, name):
    v1 = ncf.createVariable(name, np.float64, (cntl["feature_georef"][name]["dimid"]),
                            fill_value=float(cntl["feature_georef"][name]["fill_value"]))
    v1.long_name = cntl["feature_georef"][name]["long_name"]
    v1.standard_name = cntl["feature_georef"][name]["standard_name"]
    v1.units = cntl["feature_georef"][name]["units"]
    return v1


def write_timeseries_block(cntl, ncf, name):
    v1 = ncf.createVariable(name, np.float64, ("time", cntl["output_variables"][name]["georef"]["dimid"]),
                            fill_value=float(cntl["output_variables"][name]["fill_value"]))
    v1.long_name = cntl["output_variables"][name]["long_name"]
    v1.standard_name = cntl["output_variables"][name]["standard_name"]
    v1.units = cntl["output_variables"][name]["out_units"]
    return v1


def write_timeseries_values(cntl, ncf, name, vals, nc_var):
    for ii in range(0, len(vals)):
        nc_var[ii, :] = vals[ii]
    
    
def write_timeseries_last_value(vals, nc_var):
    for ii in range(0, len(vals)):
        nc_var[ii] = vals[ii]


def write_ncf(dir, varnames):
    json_file = str(dir) + "/" + "variable_info.json"
    with open(json_file, "r") as read_file:
        cntl = json.load(read_file)

# Read the PRMS output
#    var_names = cntl["output_variables"].keys()

    for var_name in varnames:
        dim_list = set()
#        print("processing " + var_name)
        dim_list.add(cntl["output_variables"][var_name]["georef"]["dimid"])
#        print(dim_list)

        csv_fn = cntl["output_variables"][var_name]["prms_out_file"]
#        print(csv_fn)
#        nts, nfeats, base_date, end_date, vals = csv_reader.read_output(csv_fn)
#        print("####### pwd = " + os.getcwd())
        nts, nfeats, base_date, end_date, vals = read_output(dir + csv_fn)
        conversion_factor = float(cntl["output_variables"][var_name]["conversion_factor"])
#        print(conversion_factor)
        iis = len(vals)
        jjs = len(vals[0])
#        print(iis, jjs)

        for ii in range(0, iis):
            for jj in range(1, jjs):
                vals[ii,jj] = vals[ii,jj] * conversion_factor

        nhrus = -1
        if 'hruid' in dim_list:
            hru_lat_vals = read_feature_georef(dir, cntl, "hru_lat")
            hru_lon_vals = read_feature_georef(dir, cntl, "hru_lon")
            nhrus = len(hru_lat_vals)
    
    
        nsegments = -1
        if 'segid' in dim_list:
            seg_lat_vals = read_feature_georef(dir, cntl, "seg_lat")
            seg_lon_vals = read_feature_georef(dir, cntl, "seg_lon")
            nsegments = len(seg_lat_vals)

# write the ncf file
        ofn = str(dir) + "output/" + str(end_date) + "_" + var_name + ".nc"
        # print('writing netcdf file ' + cntl['ncf_file_name'])
        print('writing netcdf file ' + ofn)
        ncf = Dataset(ofn, 'w', format='NETCDF4_CLASSIC')

    # Write dimensions block
        if nhrus > 0:
            hru_dim = ncf.createDimension('hruid', nhrus)
        if nsegments > 0:
            nsegments_dim = ncf.createDimension('segid', nsegments)
        time_dim = ncf.createDimension('time', None)

    # Put in the indexes for the dimensions
        time_idx = ncf.createVariable("time", np.int32, ("time"), )
        time_idx.long_name = "time"
        time_idx.standard_name = "time"
        time_idx.cf_role = "timeseries_id"
        time_idx.units = "days since " + end_date + " 00:00" + cntl["tz_code"]

        if nhrus > 0:
            hru_idx = ncf.createVariable("hruid", np.int32, ("hruid"), )
            hru_idx.long_name = "local model hru id"
    
        if nsegments > 0:
            seg_idx = ncf.createVariable("segid", np.int32, ("segid"), )
            seg_idx.long_name = "local model seg id"

        if nhrus > 0:
            hru_lat = write_variable_block(cntl, ncf, "hru_lat")
            hru_lon = write_variable_block(cntl, ncf, "hru_lon")
    
        if nsegments > 0:
            seg_lat = write_variable_block(cntl, ncf, "seg_lat")
            seg_lon = write_variable_block(cntl, ncf, "seg_lon")

        ncf.conventions = "CF-1.8"
        ncf.featureType = "timeSeries"
        ncf.history = str(datetime.datetime.now()) + ',' + str(getpass.getuser()) + ',prms_outputs2_ncf.py'

        # Write data
        time_idx[:] = np.arange(0, 1, 1)
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
            
        ncf_var = write_timeseries_block(cntl, ncf, var_name)
        write_timeseries_last_value(vals, ncf_var)
        ncf.close()
    
    
def main(dir):

    # testing for onhm
    dir = '/var/lib/nhm/NHM-PRMS_CONUS/'
    VARNAMES = ['dprst_stor_hru','gwres_stor','hru_impervstor','hru_intcpstor',
            'pkwater_equiv','soil_moist_tot']
    write_ncf(dir, VARNAMES)


if __name__ == '__main__':
    dir = "/var/lib/nhm/NHM-PRMS_CONUS"
    argc = len(sys.argv) - 1

    if argc == 1:
        print('setting dir = ' + sys.argv[1])
        dir = sys.argv[1]

    main(dir)
