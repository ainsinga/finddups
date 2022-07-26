# mungdups1.py (python3)
# Aron Insinga W1AKI
# initial creation: 23 July 2022

PROGRAM_NAME = 'mungdups1'    # probably sys.argv[0] without the path
PROGRAM_VERSION = '0.1'

# CAVEAT EMPTOR: NEVER EXPORT FROM CLUBLOG OR LET IT UPLOAD TO LOTW.
# Otherwise, you will have to do something like this program does.
# (Or wait for LoTW 2.0 which will let you hide mangled QSOs, realsoonnow.)

# SUMMARY:
#
#    Find dups accidentally created due to QSO data that was fouled up by
# exporting from LoTW, importing into clublog (which rounds/truncates),
# exporting from clublog, and then importing into LoTW.
#    They can't be deleted from LoTW (*sigh*) but we can
# use this to delete them from a logger's database, or
# at least filter them out of an .adi file so they don't get imported.
# (Yeah, it means we can upload from any logger to anyplace,
# but we should never (never ever!) export from clublog to anyplace.
#    Matched QSOs may have had times or frequencies modified by LoTW
# to match the QSL partner's, so matched QSOs are not touched at all.
#    Once the dups have been identified, set propmode=IRL (IRLP)
# for them in the output .adi file so that they can be deleted or
# at least not imported into a logger again.
#    Note that an ADIF file must NOT start with '<' for the header to be valid.
# There has to be some comment text or whatever before the first header tag.
# https://www.adif.org/311/ADIF_311.htm#ADI_Header

# PREREQUISITES:
#
# Install the python3 package adif_io from https://pypi.org/project/adif-io/
#    https://packaging.python.org/en/latest/tutorials/installing-packages/
# -or-
# Execute set-env.sh to set PYTHONPATH to find a copy that's under this
#    directory.
#
# Python >= 3.7 guarantees that the dict class preserves key order
#    which is a big aid to diffing the output against the input
#    http://gandenberger.org/2018/03/10/ordered-dicts-vs-ordereddict/

# USAGE:
#
# TBS

# Reminders for myself:
#    mo = re.search(string, cursor) # mo = match object, a common abbreviation
#    MatchObject.group(0) # (arg 0 is optional) entire string matching regex
#    MatchObject.group(n1) # string for 1st paren group in regex
#    MatchObject.group(n1, n2, ...) # tuple of paren groups in regex


import fileinput, sys, string
# import os
import adif_io
from datetime import datetime, timedelta, timezone

#### CLUBLOG MATCHING ####

# https://clublog.freshdesk.com/support/solutions/articles/55757-log-matching
# says that a match is defined as:
# Clublog pairs-up matching QSO entries in uploaded logs,
# recording new DXCC band/mode slots in the order that it finds them
# in order to generate its Log matching reports.
# In order to match a specific QSO in your log:
#    ...(overhead)...
#    The callsign you logged must correspond exactly...
#    The band and mode of the QSO must correspond...
#    The time of the QSO must be close ... within a tolerance of +/- 15 minutes.
# Also:
#    Clublog stores times rounded/truncated to the minute.
#    Unrelated to matching, Clublog stores frequencies rounded (truncated?) to 3 decimal digits
#        (0.001 MHz, 1 kHz).

#### LOTW MATCHING ####

# https://lotw.arrl.org/lotw-help/key-concepts/#confirmation
# says that a match is defined as:
#    your QSO description specifies a callsign that matches...
#    your QSO partner's QSO description specifies a callsign that matches...
#    both QSO descriptions specify start times within 30 minutes of each other
#    both QSO descriptions specify the same band (and if specified, the same rx band)
#    both QSO descriptions specify the same mode (an exact mode match), or
#        must specify modes belonging to the same mode group
#    for satellite QSOs, both QSO descriptions must specify the same satellite, and
#        a propagation mode of SAT
# Also:
#    LoTW stores times to the second.
#    Unrelated to matching, LoTW keeps frequencies to 4 decimal digits
#        (0.0001 MHz, 0.1 kHz).

# So the "key" for our hashmap is (see SEP below):
#    <CALL>|<QSO_DATE>|<BAND>|<RX_BAND>|<MODE>


#### MANIFEST CONSTANTS ####

# this is not found at all in my .adi files so it will separate fields
SEP = '|'

# ADIF tags are supposed to be case-insensitive!
# For simplicity, we will only support the case that LoTW generates,
# which is upper case except for *_LoTW_* tags (see below).
#
#TODO: Use a case-insensitive key-comparison subclass of dict.
#      But when we print the keys (tags), we want the original case
#      to make it easier to compare the output with the (test) input.
#      For more information on the Python dict ckass, see:
#      https://stackoverflow.com/questions/3296499/case-insensitive-dictionary-search
#      (and elsewhere, no doubt).

# We use these End tag strings when writing the output.
END_OF_RECORD = '<EOR>'
END_OF_HEADER = '<EOH>'

# Header tags (dict keys) that we create instead of inherit from the input
# (excluding USERDEFn because those dict keys are only referenced once)
# These are all in upper case; see printHeader.
KEY_PROGRAMID = 'PROGRAMID'
KEY_PROGRAM_VERSION = 'PROGRAM_VERSION'
KEY_CREATED_TIMESTAMP = 'CREATED_TIMESTAMP'

# Header tags (dict keys) from the input that we will NOT preserve
# because they will probably be incorrect for the output.
# adif_io seems to return them in upper case instead of '*_LoTW_*'.
KEY_APP_LOTW_NUMREC = 'APP_LOTW_NUMREC'
KEY_APP_LOTW_LASTQSORX = 'APP_LOTW_LASTQSORX'


# disused (AFAIK) propagation mode, used in output to identify duplicates
UNUSED_PROP_MODE = 'IRL'    # IRLP

####TODO: matching mode groups with modes, or modes in the same group


####

def printText(text):
    """Print text (hopefully not starting with '<')
    into ADIF file to indicate there is a header"""

    print(text)

def printTag(name, value):
    """Print an ADIF tag"""
    print('<%s:%d>%s' % (name, len(value), value))

def printUserStringTag(name, value):
    """Print a user-defined ADIF tag with a string value"""
    print('<%s:%d:S>%s' % (name, len(value), value))

def printEndTag(endTag):
    """Print an ADIF End of Header or End of Record tag"""
    print(endTag)


####

def currentTimestamp():
    """Return the current timestamp as 'YYYYMMDD HHMMSS' UTC!"""
    now = datetime.utcnow()
    return '{:04d}{:02d}{:02d} {:02d}{:02d}{:02d}'.format(
        now.year, now.day, now.month,
        now.hour, now.minute, now.second)


####

# side effect: modifies the header dict

#TODO: Make adif_io save text from start of input and print it first in Step 1.


def printHeader(fileName, header):

    # Step 1: We need to put something into the output that
    # doesn't start with '<' to indicate there is a header
    printText('Munged ADIF file to try to add PROPMODE {} to duplicates created by clublog'.format(UNUSED_PROP_MODE))
    printText('(This text is necessary because an ADIF file header cannot start with a tag.)')
    printText('Program written by Aron W1AKI but you are using it at your own risk!')

    # Step 2: Move old header tags into USERDEFn tags
    # These keys are assumed to be in upper case; see printHeader.
    header['USERDEF1'] = fileName
    header['USERDEF2'] = sys.argv[0]
    if KEY_PROGRAMID         in header: header['USERDEF3'] = header[KEY_PROGRAMID]
    if KEY_PROGRAM_VERSION   in header: header['USERDEF4'] = header[KEY_PROGRAM_VERSION]
    if KEY_CREATED_TIMESTAMP in header: header['USERDEF5'] = header[KEY_CREATED_TIMESTAMP]

    # Step 3: Add our new header tags
    # These keys are assumed to be in upper case; see printHeader.
    header[KEY_PROGRAMID] = PROGRAM_NAME
    header[KEY_PROGRAM_VERSION] = PROGRAM_VERSION
    header[KEY_CREATED_TIMESTAMP] = currentTimestamp()

    # Step 4: Print the header tags.
    # (If the ADIF version was in the input, we will print it here.)

    # Print these important identifying header tags first.
    headerTagsToWriteFirst = [KEY_PROGRAMID, KEY_PROGRAM_VERSION, KEY_CREATED_TIMESTAMP]

    # Ignore these header tags that will probably not be valid in the output.
    headerTagsToIgnore = [KEY_APP_LOTW_NUMREC, KEY_APP_LOTW_LASTQSORX] #WASL {KEY_APP_LOTW_NUMREC:None, KEY_APP_LOTW_LASTQSORX:None}

    print('# headerTagsToIgnore: ', headerTagsToIgnore);
    print('# headerTagsToWriteFirst: ', headerTagsToWriteFirst);

    # Print tags that were in the original file and not modified above in their
    # original case.  Tags modified above are all in upper case

    for k in header:
        if k in headerTagsToWriteFirst:
            print('#   {} in headerTagsToWriteFirst: {}'.format(k, k in headerTagsToWriteFirst));
            printTag(k, header[k])
    for k in header:
        print('#   {} in headerTagsToIgnore: {}'.format(k, k in headerTagsToIgnore));
        print('#   {} in headerTagsToWriteFirst: {}'.format(k, k in headerTagsToWriteFirst));
        print('#   {} not in either: {}'.format(k, not (k in headerTagsToWriteFirst) and not (k in headerTagsToIgnore)));
        if not (k in headerTagsToWriteFirst) and not (k in headerTagsToIgnore):
            printTag(k, header[k])

    # End the header
    printEndTag(END_OF_HEADER)

####

def main(fileName):
    qsos, header =  adif_io.read_from_file(fileName)

    print('--header--')
    print(header)
    #print('--qsos--')
    #print(qsos)
    print('----')

    #TODO: grind()

    printHeader(fileName, header)

    #TODO: emitMungedLog()
    #TODO:WAS: f.close()


if __name__ == '__main__':
    main(sys.argv[1])
else:
    print('Usage: {}: lotwreport.adi >new.adi'.format(sys.argv[0]))


# end
