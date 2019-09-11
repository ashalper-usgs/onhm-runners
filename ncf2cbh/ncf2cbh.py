from netCDF4 import Dataset  # http://code.google.com/p/netcdf4-python/
from netCDF4 import num2date
import datetime
import sys

def read(nc_fn):
    nc_fid = Dataset(nc_fn, 'r')
    nc_attrs = nc_fid.ncattrs()
    # print 'attrs', nc_attrs

    nc_dims = [dim for dim in nc_fid.dimensions]
    # print 'dims', nc_dims

    # Figure out the variable names with data in the ncf.
    nc_vars = [var for var in nc_fid.variables]
    remove_list = list(nc_dims)
    remove_list.extend(['hru_lat', 'hru_lon', 'seg_lat', 'seg_lon'])
    var_names = [e for e in nc_vars if e not in remove_list]
    # print 'var_names', var_names

    time = nc_fid.variables['time'][:]
    nts = len(time)
    # print(time, nts)

    time_var = nc_fid.variables['time']
    # print(str(time_var))
    dtime = num2date(time_var[:],time_var.units)
    # print("dtime = " + str(dtime[0]))

    base_date_str = str(dtime[0])
    print('base_date_str ' + base_date_str)
    # base_date_str = "2019-05-05"
    tok = base_date_str.split(' ')
    ymd = tok[0]
    tok = ymd.split('-')
    base_date = datetime.date(int(tok[0]), int(tok[1]), int(tok[2]))
    print(base_date)

    # Read the values into a dictionary.
    vals = {}
    for var in var_names:
        f1 = nc_fid.variables[var][:]
        vals[var] = f1

    nc_fid.close()

    return var_names, base_date, nts, vals

# dir is where to write the CBH files
# full path required for nc_fn
def run(dir, nc_fn):
    var_names, base_date, nts, vals = read(nc_fn)

    # Write CBH files.
    for name in var_names:
        v = vals[name]
        nfeats = len(v[0])
        fn2 = dir + name + ".cbh"
        current_date = base_date
        print('writing ' + fn2)
        with open(fn2, 'w') as fp:
            fp.write('Written by ncf2cbh.py\n')
            fp.write(name + ' ' + str(nfeats) + '\n')
            fp.write('########################################\n')

            for ii in range(nts):
                fp.write(str(current_date.year) + ' ' + str(current_date.month) + ' '
                         + str(current_date.day) + ' 0 0 0')
                for jj in range(nfeats):
                    if name == 'prcp':
                        v[ii, jj] = v[ii, jj] / 25.4
                    elif name == 'tmax':
                        v[ii, jj] = v[ii, jj] * 9 / 5 + 32
                    elif name == 'tmin':
                        v[ii, jj] = v[ii, jj] * 9 / 5 + 32
                    else:
                        "don't know how to convert units"
                    fp.write(' ' + str(v[ii,jj]))
                fp.write('\n')
                current_date += datetime.timedelta(days=1)


def main(dir, nc_fn):
    run(dir, nc_fn)

if __name__ == '__main__':
    work_dir = '/var/lib/nhm/NHM-PRMS_CONUS/'

    argc = len(sys.argv) - 1
    # print(argc)

    if argc == 1:
        print('setting dir = ' + sys.argv[1])
        dir = sys.argv[1]
    else:
        dir='/var/lib/nhm/ofp/Output/'

    nc_fn = dir + 'climate_'+str(datetime.datetime.now().strftime('%Y_%m_%d'))+'.nc'

    main(dir, nc_fn)
