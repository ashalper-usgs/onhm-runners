# Markstrom
# Wed Sep 04 09:43:53 MDT 2019
# 
# This script runs against a CSV file and writes the
# contents into a set of netcdf files, one for each variable. It converts the
# whole CSV file to a netcdf file. If the files are big, this will be very slow.

#from prms_utils import csv_reader
import numpy as np
import csv
import json
import datetime
import getpass
from netCDF4 import Dataset
import os
import sys

outvars=['dprst_stor_hru','gwres_stor','hru_impervstor','hru_intcpstor',
         'pkwater_equiv','soil_moist_tot']

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


def read_feature_georef(cntl, name):
    fn1 = cntl["feature_georef"][name]["file"]
    print (fn1)

    nfeat = sum(1 for line in open(fn1))
    vals = np.zeros(shape=(nfeat))
    with open(fn1, 'r') as csvfile:
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


def main(dir):
    json_file = str(dir) + "/" + "variable_info.json"
    with open(json_file, "r") as read_file:
        cntl = json.load(read_file)

# Read the PRMS output
    var_names = cntl["output_variables"].keys()
    val_list = []
    dim_list = set()

    for var_name in outvars:
        var_names = cntl["output_variables"].keys()
        val_list = []
        dim_list = set()
    
        print("processing " + var_name)
        dim_list.add(cntl["output_variables"][var_name]["georef"]["dimid"])

        csv_fn = cntl["output_variables"][var_name]["prms_out_file"]
#        nts, nfeats, base_date, end_date, vals = csv_reader.read_output(csv_fn)
#        print("####### pwd = " + os.getcwd())
        print("reading ", csv_fn)
        nts, nfeats, base_date, end_date, vals = read_output(csv_fn)
        print("nts = ", nts, " nfeats = ", nfeats, ' base_date = ', base_date, " end_date = ", end_date)

        conversion_factor = float(cntl["output_variables"][var_name]["conversion_factor"])
        iis = len(vals)
        jjs = len(vals[0])

        for ii in range(0, iis):
            for jj in range(1, jjs):
                vals[ii,jj] = vals[ii,jj] * conversion_factor

        print("done converting vals")

        val_list.append(vals)

        nhrus = -1
        if 'hruid' in dim_list:
            hru_lat_vals = read_feature_georef(cntl, "hru_lat")
            hru_lon_vals = read_feature_georef(cntl, "hru_lon")
            nhrus = len(hru_lat_vals)


#        nsegments = -1
#        if 'segid' in dim_list:
#            seg_lat_vals = read_feature_georef(cntl, "seg_lat")
#            seg_lon_vals = read_feature_georef(cntl, "seg_lon")
#            nsegments = len(seg_lat_vals)

# write the ncf file
        ofn = str(dir) + "/output/" + str(end_date) + "_" + var_name + "_out.nc"
    # print('writing netcdf file ' + cntl['ncf_file_name'])
        print('writing netcdf file ' + ofn)
        ncf = Dataset(ofn, 'w', format='NETCDF4_CLASSIC')

        # Write dimensions block
        if nhrus > 0:
            hru_dim = ncf.createDimension('hruid', nhrus)
#        if nsegments > 0:
#            nsegments_dim = ncf.createDimension('segid', nsegments)
        time_dim = ncf.createDimension('time', None)

        # Put in the indexes for the dimensions
        time_idx = ncf.createVariable("time", np.int32, ("time"), )
        time_idx.long_name = "time"
        time_idx.standard_name = "time"
        time_idx.cf_role = "timeseries_id"
        time_idx.units = "days since " + base_date + " 00:00" + cntl["tz_code"]

        if nhrus > 0:
            hru_idx = ncf.createVariable("hruid", np.int32, ("hruid"), )
            hru_idx.long_name = "local model hru id"

#        if nsegments > 0:
#            seg_idx = ncf.createVariable("segid", np.int32, ("segid"), )
#            seg_idx.long_name = "local model seg id"

        if nhrus > 0:
            hru_lat = write_variable_block(cntl, ncf, "hru_lat")
            hru_lon = write_variable_block(cntl, ncf, "hru_lon")

#        if nsegments > 0:
#            seg_lat = write_variable_block(cntl, ncf, "seg_lat")
#            seg_lon = write_variable_block(cntl, ncf, "seg_lon")

        ncf_vars = []
#        for var_name in var_names:  comment out the loop if one variable per file
        ncf_vars.append(write_timeseries_block(cntl, ncf, var_name))

        ncf.conventions = "CF-1.8"
        ncf.featureType = "timeSeries"
        ncf.history = str(datetime.datetime.now()) + ',' + str(getpass.getuser()) + ',prms_outputs3_ncf.py'

        # Write data
        time_idx[:] = np.arange(0, nts, 1)
        if nhrus > 0:
            hru_idx[:] = np.arange(1, nhrus+1, 1)
#        if nsegments > 0:
#            seg_idx[:] = np.arange(1, nsegments + 1, 1)

        if nhrus > 0:
            hru_lat[:] = hru_lat_vals
            hru_lon[:] = hru_lon_vals

#        if nsegments > 0:
#            seg_lat[:] = seg_lat_vals
#            seg_lon[:] = seg_lon_vals

        ii = 0
 #   for var_name in var_names:
        write_timeseries_values(cntl, ncf, var_name, val_list[ii], ncf_vars[ii])
        ii = ii + 1
        
        ncf.close()


if __name__ == '__main__':
    dir = "/work/markstro/operat/setup/test/NHM-PRMS_CONUS"
    argc = len(sys.argv) - 1
    # print(argc)

    if argc == 1:
        print('setting dir = ' + sys.argv[1])
        dir = sys.argv[1]

    os.chdir(dir)
    main(dir)
