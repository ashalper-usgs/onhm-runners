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
import docker
import re

# these are onhm modules
import run_prms

RESTARTDIR = 'restart/'
INDIR = 'input/'
OUTDIR = 'output/'
GRIDMET_PROVISIONAL_DAYS = 59
PRMSPATH = '/work/markstro/operat/repos/prms/prms/prms'
WORKDIR = '/var/lib/NHM-PRMS_CONUS/'
CONTROLPATH = './NHM-PRMS.control'
PRMSLOGPATH = './prms.log'
MAKERSPACE = ['dprst_stor_hru', 'gwres_stor', 'hru_impervstor',
              'hru_intcpstor', 'pkwater_equiv', 'soil_moist_tot']
CBHFILES = ['tmin.cbh', 'tmax.cbh', 'prcp.cbh']

# This one will probably need to change
FPWRITEDIR = WORKDIR

# Check the restart directory for restart files. Return the date of
# the latest one.
def last_simulation_date(client, dir):
    try:
        # Run BusyBox container to mount the Docker volume on
        # /var/lib, and list restart files.

        # TODO: probably should have auto_remove=True here, but we
        # were having mysterious problems with it. See
        # https://docker-py.readthedocs.io/en/stable/containers.html#container-objects
        command = 'sh -c "ls ' + dir + RESTARTDIR + '*.restart"'
        restart_file_names = client.containers.run(
            'busybox', command,
            volumes={'nhm_nhm':
                     {'bind': '/var/lib', 'mode': 'ro'}}
        )
    except docker.errors.ContainerError:
        print('Restart files not found on Docker volume')
        exit(1)
    except docker.errors.ImageNotFound:
        print('Could not find busybox Docker image')
        exit(1)
    except docker.errors.APIError:
        print('Could not call into Docker API')
        exit(1)

    # remove any prefix "b'" and suffix "\n'" (don't know yet why
    # Docker does this)
    s = re.sub(r'^[^/]+|[\\n\']+$', '', str(restart_file_names))

    restart_dates_present = []
    for name in s.split('\\n'):
        head, tail = os.path.split(name)
        restart_dates_present.append(
            datetime.datetime.strptime(tail[0:10], "%Y-%m-%d")
        )
    
    restart_dates_present.sort(reverse=True)
    return restart_dates_present[0].date()

def compute_pull_dates(restart_date):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    pull_date = yesterday - datetime.timedelta(days=GRIDMET_PROVISIONAL_DAYS)
    
    # if the restart date is earlier than the pull date...
    if restart_date < pull_date:
        # ...reset the pull date
        pull_date = restart_date
        print('log message: pull_date reset to restart_date')
    
    return pull_date, yesterday

def main(dir):
    try:
        client = docker.from_env() # Initialize Docker API
    except docker.errors.APIError:
        print('Could not invoke Docker API')
        exit(1)

    # Determine the date for the last simulation by finding the last
    # restart file.
    lsd = last_simulation_date(client, dir)
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
    print('starting script')
    #numdays = 2
    #fp = FpoNHM()
    client.containers.run()

    print('instantiated')

    extract_type = 'date'
    numdays = 2
<<<<<<< HEAD

    ready = fp.initialize(dir + INDIR + 'nhm_hru_data/', dir + OUTDIR,
                          dir + INDIR + 'nhm_hru_data/weights.csv',
=======
    #initialize(self, iptpath, optpath, weights_file, type=None, days=None, start_date=None, end_date=None)
`    ready = fp.initialize(dir + INDIR + 'nhm_hru_data/', dir + OUTDIR, dir + INDIR+'nhm_hru_data/weights.csv',
>>>>>>> master
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
        
        # Run PRMS again to update the restart file
        end_date_restart = end_pull_date - datetime.timedelta(days=GRIDMET_PROVISIONAL_DAYS)
        restart_fn = end_date_restart.strftime('%Y-%m-%d') + '.restart'
        run_prms.run(st=start_prms_date.strftime('%Y-%m-%d'),
                 et=end_date_restart.strftime('%Y-%m-%d'), prms_path=PRMSPATH,
                 work_dir=dir, init_flag=True, save_flag=True,
                 control_file=CONTROLPATH, init_file=init_file,
                 save_file=restart_fn,
                 log_file_name=PRMSLOGPATH)


if __name__ == '__main__':
    argc = len(sys.argv) - 1
    if argc == 1:
        print('setting dir = ' + sys.argv[1])
        dir = sys.argv[1]
    else:
        dir='/var/lib/nhm/NHM-PRMS_CONUS/'
        
    dir = WORKDIR
    main(dir)
