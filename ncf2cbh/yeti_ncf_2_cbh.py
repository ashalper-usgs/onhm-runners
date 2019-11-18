
#from netCDF4 import Dataset  # http://code.google.com/p/netcdf4-python/
import datetime
from prms_utils import ncf_reader
import sys
import numpy as np
import csv

nhm_id_file = "/work/markstro/operat/setup/test/NHM-PRMS_CONUS/input/nhm_id"

def main(dir, nc_fn, yr_str):
    var_names, base_date, nts, vals = ncf_reader.read(nc_fn)
    
    # read the mapping
    nhm_id = np.zeros(109951, dtype = np.int)
    ii = 0
    with open(nhm_id_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            nhm_id[ii] = int(row[0])
            ii = ii + 1

    print(nhm_id)
        
    # Write CBH files.
    for name in var_names:
        v = vals[name]
        v2 = np.zeros(109951)
        nfeats = len(v[0])
        fn2 = dir + yr_str + "_" + name + ".cbh"
        current_date = base_date
        print("base_date", str(base_date))
        print('writing ' + fn2)
        with open(fn2, 'w') as fp:
            fp.write('Written by yeti_ncf_2_cbh.py\n')
            fp.write(name + ' ' + str(nfeats) + '\n')
            fp.write('########################################\n')

            for ii in range(nts):
                fp.write(str(current_date.year) + ' ' + str(current_date.month) + ' '
                         + str(current_date.day) + ' 0 0 0')
                for jj in range(nfeats):
                    if name == 'prcp':
                        v2[jj] = v[ii, nhm_id[jj]-1] / 25.4
                    elif name == 'tmax':
                        v2[jj] = v[ii, nhm_id[jj]-1] * 9 / 5 + 32
                    elif name == 'tmin':
                        v2[jj] = v[ii, nhm_id[jj]-1] * 9 / 5 + 32
                    else:
                        "don't know how to convert units"
                for jj in range(nfeats):
                    if name == 'prcp':
                        fp.write(' ' + '{:.2f}'.format(v2[jj]))
                    elif name == 'tmax':
                        fp.write(' ' + '{:.1f}'.format(v2[jj]))
                    elif name == 'tmin':
                        fp.write(' ' + '{:.1f}'.format(v2[jj]))
                    else:
                        fp.write(' ' + '{:.2f}'.format(v2[jj]))
                        
                fp.write('\n')
                current_date += datetime.timedelta(days=1)


if __name__ == '__main__':
    dir = '/work/markstro/operat/setup/init_file/updated_cbh_20191018/'
    
    ft = [('1979','_climate_2019_10_08.nc'),('1980','_climate_2019_10_08.nc'),
          ('1981','_climate_2019_10_09.nc'),('1982','_climate_2019_10_10.nc'),
          ('1983','_climate_2019_10_11.nc'),('1984','_climate_2019_10_12.nc'),
          ('1985','_climate_2019_10_13.nc'),('1986','_climate_2019_10_14.nc'),
          ('1987','_climate_2019_10_16.nc'),('1988','_climate_2019_10_17.nc'),
          ('1989','_climate_2019_10_18.nc'),('1990','_climate_2019_10_08.nc'),
          ('1991','_climate_2019_10_09.nc'),('1992','_climate_2019_10_10.nc'),
          ('1993','_climate_2019_10_11.nc'),('1994','_climate_2019_10_12.nc'),
          ('1995','_climate_2019_10_13.nc'),('1996','_climate_2019_10_14.nc'),
          ('1997','_climate_2019_10_15.nc'),('1998','_climate_2019_10_16.nc'),
          ('1999','_climate_2019_10_17.nc'),('2000','_climate_2019_10_08.nc'),
          ('2001','_climate_2019_10_09.nc'),('2002','_climate_2019_10_10.nc'),
          ('2003','_climate_2019_10_11.nc'),('2004','_climate_2019_10_12.nc'),
          ('2005','_climate_2019_10_13.nc'),('2006','_climate_2019_10_14.nc'),
          ('2007','_climate_2019_10_15.nc'),('2008','_climate_2019_10_16.nc'),
          ('2009','_climate_2019_10_17.nc'),('2010','_climate_2019_10_08.nc'),
          ('2011','_climate_2019_10_09.nc'),('2012','_climate_2019_10_10.nc'),
          ('2013','_climate_2019_10_11.nc'),('2014','_climate_2019_10_12.nc'),
          ('2015','_climate_2019_10_13.nc'),('2016','_climate_2019_10_14.nc'),
          ('2017','_climate_2019_10_15.nc'),('2018','_climate_2019_10_16.nc'),
          ('2019','_climate_2019_10_17.nc')
          ]
    
    for f in ft:
        nc_fn = dir + f[0] + f[1]

#        argc = len(sys.argv) - 1
#    # print(argc)
#
#        if argc == 1:
#            print('setting dir = ' + sys.argv[1])
#            dir = sys.argv[1]

        main(dir, nc_fn, f[0])
        diff