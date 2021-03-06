import numpy as np
import csv

def read(csvfn):
    # figure out the number of features (ncol - 1)
    # figure out the number of timesteps (nrow -1)
    with open(csvfn, 'rb') as csvfile:
        spamreader = csv.reader(csvfile)

        header = spamreader.next()
        nfeat = len(header) - 6

        ii = 0
        for row in spamreader:
            ii = ii + 1
        nts = ii

    vals = np.zeros(shape=(nts,nfeat))
    with open(csvfn, 'rb') as csvfile:
        spamreader = csv.reader(csvfile)

        # Read the header line
        header = spamreader.next()

        # Read the CSV file values, line-by-line, column-by-column
        ii = 0
        for row in spamreader:
            jj = 0
            kk = 0
            for tok in row:
                # Get the base date (ie date of first time step) from the first row of values
                if ii == 0:
                    base_date = row[:6]

                # Now skip the date/time fields and put the values into the 2D array
                if jj > 5:
                    vals[ii][kk] = float(tok)
                    kk = kk + 1
                jj = jj + 1
            ii = ii + 1
    return nts, nfeat, base_date, vals


# Read a PRMS "output" csv. For these files, there is a remapping in the header line that tells the order of the columns
def read_output(csvfn):
    # figure out the number of features (ncol - 1)
    # figure out the number of timesteps (nrow -1)
    with open(csvfn, 'rb') as csvfile:
        spamreader = csv.reader(csvfile)

        header = spamreader.next()
        nfeat = len(header) - 1

        ii = 0
        for row in spamreader:
            ii = ii + 1
        nts = ii

    vals = np.zeros(shape=(nts,nfeat))
    indx = np.zeros(shape=nfeat, dtype=int)
    with open(csvfn, 'rb') as csvfile:
        spamreader = csv.reader(csvfile)

        # Read the header line
        header = spamreader.next()
        for ii in xrange(1,len(header)):
            indx[ii-1] = int(header[ii])

        print indx

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
                        print 'read_output: ', str(tok), str(ii), str(kk), str(indx[kk]-1)
                else:
                    # Get the base date (ie date of first time step) from the first row of values
                    if ii == 0:
                        base_date = tok
                    print tok

                jj = jj + 1
            ii = ii + 1
    return nts, nfeat, base_date, vals

# Read a PRMS "CBH" file. For these files, I cut off the header of the cbh files. There is no mapping info because
# the values are in the order of the HRU IDs.
def read_cbh(csvfn):
    # figure out the number of features (ncol - 1)
    # figure out the number of timesteps (nrow -1)
    with open(csvfn, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=' ')

        header = spamreader.next()
        nfeat = len(header) - 6

        ii = 0
        for row in spamreader:
            ii = ii + 1
        nts = ii + 1

    vals = np.zeros(shape=(nts,nfeat))
    with open(csvfn, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=' ')

        # Read the CSV file values, line-by-line, column-by-column
        ii = 0
        for row in spamreader:
            for kk in xrange(0,nfeat):
                try:
                    vals[ii][kk] = float(row[kk+6])
                except:
                    print 'read_output: ', row[0], row[1], row[2]

                # Get the base date (ie date of first time step) from the first row of values
                if ii == 0:
                    base_date = str(row[0]) + "-" + str(row[1]) + "-" + str(row[2])

            ii = ii + 1
    return nts, nfeat, base_date, vals


# tester
if __name__ == '__main__':
    print read('/work/markstro/intern_demo/ModelInput/skunk_humid.csv')