# U.S. Geological Survey
#
# File - onhm.py
#
# Purpose - Run-time controller for the ONHM. Can be run everyday or
#           when needed to update to the current state.
#
# Date - 2019-09-06
#
# Authors - Steven Markstrom, Andrew Halper

import os
import sys
import glob
import datetime

# These are onhm modules
import run_prms
import prms_verifier
import prms_outputs2_ncf
import ncf2cbh
from fponhm import FpoNHM

RESTARTDIR = 'restart/'
INDIR = 'input/'
OUTDIR = 'output/'
GRIDMET_PROVISIONAL_DAYS = 59
PRMSPATH = '/work/markstro/operat/repos/prms/prms/prms'
WORKDIR = '/work/markstro/operat/setup/test/NHM-PRMS_CONUS/'
CONTROLPATH = './NHM-PRMS.control'
PRMSLOGPATH = './prms.log'
MAKERSPACE = ['dprst_stor_hru', 'gwres_stor', 'hru_impervstor',
              'hru_intcpstor', 'pkwater_equiv', 'soil_moist_tot']
CBHFILES = ['tmin.cbh', 'tmax.cbh', 'prcp.cbh']

# This one will probably need to change
FPWRITEDIR = WORKDIR

# Check the restart directory for restart files.
# Return the date of the latest one.
def last_simulation_date(dir):
    foo = glob.glob(dir + RESTARTDIR + '*.restart')

    restart_dates_present = []
    for fn in foo:
        head, tail = os.path.split(fn)
        restart_dates_present.append(datetime.datetime.strptime(tail[0:10], "%Y-%m-%d"))
    
    restart_dates_present.sort(reverse=True)
    f1 = restart_dates_present[0].date()
    return f1

def compute_pull_dates(restart_date):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    pull_date = yesterday - datetime.timedelta(days=GRIDMET_PROVISIONAL_DAYS)
    
    # if the restart date is earlier than the pull date, reset the pull date
    if restart_date < pull_date:
        pull_date = restart_date
        print('log message: pull_date reset to restart_date')
    
    return pull_date, yesterday


def main(dir):

    # Determine the date for the last simulation by finding the last
    # restart file.
    lsd = last_simulation_date(dir)
    restart_date = lsd + datetime.timedelta(days=1)
    print('last simulation date = ' + lsd.strftime('%Y-%m-%d'))
    print('restart date = ' + restart_date.strftime('%Y-%m-%d'))
        
    # Determine the dates for the data pull
    start_pull_date, end_pull_date = compute_pull_dates(restart_date)
    
    start_pull_date = datetime.date(2019, 9, 1)
    end_pull_date = datetime.date(2019, 9, 2)
    
    print('pull period start = ', start_pull_date, ' end = ', end_pull_date)
    
    # Run the Fetcher/Parser to pull available data.
    #
    # RMCD: Not sure this works, I imagine this would be the call to
    # make over-riding the START_DATE and END_DATE ENV variables setup
    # in the nhmusgs-ofp Dockerfile. The code below is one method to
    # run ofp through nhumusgs/docker-images commented out.
    sformat = "%Y-%m-%d"
    str_start_pull_date = start_pull_date.strftime(sformat)
    str_end_pull_date = end_pull_date.strftime(sformat)
    # # START_DATE and END_DATE are ENV variables in nhmusgs-ofp Docker file we over-ride with -e option
    # ofp_docker_cmd = f"docker run ofp -e START_DATE={str_start_pull_date} END_DATE={str_end_pull_date}"
    # with open("ofp_log.log", "a") as output:
    #     subprocess.call(ofp_docker_cmd, stdout=output, stderr=output)
    # Code below call fetch-parser thorough; assumes hru*.shp are in INDIR; will output to OUTDIR
    print('starting Script')
    #numdays = 2
    fp = FpoNHM()
    print('instantiated')

    extract_type = 'date'
    numdays = 2

    ready = fp.initialize(dir + INDIR + 'nhm_hru_data/', dir + OUTDIR, dir + INDIR+'nhm_hru_data/weights.csv',
                          type=extract_type,
                          start_date=start_pull_date,
                          end_date=end_pull_date)
    if ready:
        print('initalized\n')
        print('running')
        fp.run_weights()
        print('finished running')
        fp.finalize()
        print('finalized')
    else:
        if extract_type == 'days' or extract_type == 'date':
            print('Gridmet not updated continue with numdays -1')
            fp.setNumdays(numdays-1)
            print('initalized\n')
            print('running')
            fp.run_weights()
            print('finished running')
            fp.finalize()
            print('finalized')
        else:
            print('error: extract did not return period specified')

    # Add/overwrite the CBH files with the new Fetcher/Parser data.
    #
    # Note that "_" are used instead of "-" in the date name.
    #
    # end_pull_date.strftime('%Y_%m_%d')
    #    nc_fn = FPWRITEDIR + 'climate_' + end_pull_date.strftime('%Y_%m_%d') + '.nc'
    #    ncf2cbh.run(dir + INDIR, nc_fn)
    
    # Figure out the run period for PRMS. It should usually be from
    # one day past the date of the restart file through yesterday.
    # This is a hack until FP code is in here and CBH files are
    # updated.
    start_prms_date = datetime.date(2019, 6, 2)
    end_prms_date = datetime.date(2019, 9, 8)
    print("hard coded prms run time " , start_prms_date.strftime('%Y-%m-%d'),
          end_prms_date.strftime('%Y-%m-%d'))

    # Remove the verification file before running PRMS.
    foo = glob.glob(dir + 'PRMS_VERIFIED_*')
    for f in foo:
        print(f)
        os.remove(f)
    
    # Run PRMS for the prescribed period.
    #
    # st, et, prms_path, work_dir, init_flag, save_flag, control_file, init_file, save_file
    init_file = RESTARTDIR + lsd.strftime('%Y-%m-%d') + '.restart'
#    save_file = RESTARTDIR + end_prms_date.strftime('%Y-%m-%d') + '.restart'
    
    run_prms.run(st=start_prms_date.strftime('%Y-%m-%d'),
                 et=end_prms_date.strftime('%Y-%m-%d'), prms_path=PRMSPATH,
                 work_dir=dir, init_flag=True, save_flag=False,
                 control_file=CONTROLPATH, init_file=init_file, save_file=None,
                 log_file_name=PRMSLOGPATH)
    
    # Verify that PRMS ran correctly.
    # args: work_dir, fname, min_time
    ret_code = prms_verifier.main(dir, "prms.out", 1)
    if ret_code != 0:
        print('PRMS run failed')

    else:
        print('PRMS run verified')
    
        # Create ncf files from the output CSV files (one for each
        # output variable).
        prms_outputs2_ncf.write_ncf(dir, MAKERSPACE)
    
        # Copy these nc files (made in the previous step) to the s3 area.

if __name__ == '__main__':
    argc = len(sys.argv) - 1
    if argc == 1:
        print('setting dir = ' + sys.argv[1])
        dir = sys.argv[1]
    else:
        dir='/var/lib/nhm/NHM-PRMS_CONUS/'
        
    dir = WORKDIR
    main(dir)
