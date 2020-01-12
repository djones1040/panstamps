#!/usr/local/bin/python
# encoding: utf-8
"""
Documentation for panstamps can be found here: http://panstamps.readthedocs.org/en/stable

Usage:
    panstamps [options] [--width=<arcminWidth>] [--filters=<filterSet>] [--settings=<pathToSettingsFile>] [--downloadFolder=<path>] (warp|stack) <ra> <dec> [<mjdStart> <mjdEnd>]
    panstamps [options] --closest=<beforeAfter> [--width=<arcminWidth>] [--filters=<filterSet>] [--settings=<pathToSettingsFile>] [--downloadFolder=<path>] <ra> <dec> <mjd>

    -h, --help                              show this help message
    -f, --fits                              download fits (default on)
    -F, --nofits                            don't download fits (default off)
    -j, --jpeg                              download jepg (default off)
    -J, --nojpeg                            don't download jepg (default on)
    -c, --color                             download color jepg (default off)
    -C, --nocolor                           don't download color jepg (default on)
    -a, --annotate                          annotate jpeg (default true)
    -A, --noannotate                        don't annotate jpeg (default false)
    -t, --transient                         add a small red circle at transient location (default false)
    -T, --notransient                       don't add a small red circle at transient location (default true)
    -g, --greyscale                         convert jpeg to greyscale (default false)
    -G, --nogreyscale                       don't convert jpeg to greyscale (default true)
    -i, --invert                            invert jpeg colors (default false)
    -I, --noinvert                          don't invert jpeg colors (default true)
    --width=<arcminWidth>                   width of image in arcsec (default 1)
    --filters=<filterSet>                   filter set to download and use for color image (default gri)
    --downloadFolder=<path>                 path to the download folder, relative or absolute (folder created where command is run if not set)
    --settings=<pathToSettingsFile>         the settings file    
    --closest=<beforeAfter>                 return the warp closest in time to the given mjd. If you want to set a strict time window then pass in a positive or negative time in sec (before | after | secs)

    ra                                      right-ascension in sexagesimal or decimal degrees
    dec                                     declination in sexagesimal or decimal degrees
    mjdStart                                the start of the time-window within which to select images
    mjdEnd                                  the end of the time-window within which to select images
    mjd                                     report the warp closest in time to this mjd
"""
################# GLOBAL IMPORTS ####################
import sys
import os
from os.path import expanduser
os.environ['TERM'] = 'vt100'
import readline
import glob
import pickle
from docopt import docopt, printable_usage
from fundamentals import tools, times
from panstamps.downloader import downloader
from panstamps.image import image
import argparse
# from ..__init__ import *


def tab_complete(text, state):
    return (glob.glob(text + '*') + [None])[state]

#class cl:
#    def __init__(self):
#        pass
#
#    def add_options(self, parser=None, usage=None, config=None):
#        if parser == None:
#            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")
#
#        # The basics
#        parser.add_argumant('-F', '--nofits',help='don\'t download fits (default off)',default=False,action="store_true")
#        parser.add_argumant('-j', '--jpeg',help='download jepg (default off)',default=False,action="store_true")
#        parser.add_argumant('-c', '--color',help='download color jepg (default off)',default=False,action="store_true")
#        parser.add_argumant('-A', '--noannotate',help=' don\'t annotate jpeg (default false)',default=False,action="store_true")
#        parser.add_argumant('-t', '--transient',help='add a small red circle at transient location (default false)',default=False,action="store_true")
#        parser.add_argumant('-g', '--greyscale',help='convert jpeg to greyscale (default false)',default=False,action="store_true")
#        parser.add_argumant('-i', '--invert',help='invert jpeg colors (default false)',default=False,action="store_true")
#        parser.add_argumant('--width',help='width of image in arcsec (default 1)',type=float)
#        parser.add_argument('--filters',help='filter set to download and use for color image (default gri)',type='string')
#        parser.add_argument('--downloadFolder',help='path to the download folder, relative or absolute (folder created where command is run if not set)',type='string')
#        parser.add_argumant('--settings',help='the settings file',type='string')
#        parser.add_argument('--closest',help="""return the warp closest in time to the given mjd. If you want to set a strict 
#time window then pass in a positive or negative time in sec (before | after | secs""",type='string')

#        return parser
        
def main(arguments=None):
    """
    *The main function used when ``cl_utils.py`` is run as a single script from the cl, or when installed as a cl command*
    """
    # setup the command-line util settings
    su = tools(
        arguments=arguments,
        docString=__doc__,
        logLevel="WARNING",
        options_first=True,
        projectName="panstamps"
    )
    arguments, settings, log, dbConn = su.setup()

    #parser = self.add_options(usage=usagestring)
    #options,  args = parser.parse_args()
    #self.options = options
    ra,dec = 0,0
    # unpack remaining cl arguments using `exec` to setup the variable names
    # automatically
    argdict = {}
    for arg, val in arguments.items():
        if arg[0] == "-":
            varname = arg.replace("-", "") + "Flag"
        else:
            varname = arg.replace("<", "").replace(">", "")
        #if isinstance(val, str) or isinstance(val, str):
        argdict[varname] = val
            #exec("%s = '%s'" % (varname,val),globals(),globals())
        #else:
        #    argdict[varname] = float(val)
            #exec("%s = %s" % (varname,val,),globals(),globals())
        if arg == "--dbConn":
            dbConn = val
        log.debug('%s = %s' % (varname, val,))
        #if varname == 'ra': import pdb; pdb.set_trace()
    #print(ra,dec)
    #import pdb; pdb.set_trace()
    if argdict['ra']:
        try:
            argdict[ra] = float(argdict['ra'])
        except:
            if ":" not in argdict['ra']:
                log.error(
                    "ERROR: ra must be in decimal degree or sexagesimal format")
                return

    if argdict['dec']:
        try:
            argdict['dec'] = float(argdict['dec'])
        except:
            if ":" not in argdict['dec']:
                log.error(
                    "ERROR: dec must be in decimal degree or sexagesimal format")
                return

    ## START LOGGING ##
    startTime = times.get_now_sql_datetime()
    log.info(
        '--- STARTING TO RUN THE cl_utils.py AT %s' %
        (startTime,))

    # BUILD KEYWORD DICT
    kwargs = {}
    kwargs["log"] = log
    kwargs["settings"] = settings
    kwargs["ra"] = argdict['ra']
    kwargs["dec"] = argdict['dec']

    # FITS OPTIONS
    kwargs["fits"] = True  # DEFAULT
    if argdict['fitsFlag'] == False and argdict['nofitsFlag'] == True:
        kwargs["fits"] = False

    # JPEG OPTIONS
    kwargs["jpeg"] = False  # DEFAULT
    if argdict['jpegFlag'] == True and argdict['nojpegFlag'] == False:
        kwargs["jpeg"] = True

    # COLOR JPEG OPTIONS
    kwargs["color"] = False  # DEFAULT
    if argdict['colorFlag'] == True and argdict['nocolorFlag'] == False:
        kwargs["color"] = True

    # WIDTH OPTION
    kwargs["arcsecSize"] = 60
    if argdict['widthFlag']:
        kwargs["arcsecSize"] = float(argdict['widthFlag']) * 60.

    # CHOOSE A FILTERSET
    kwargs["filterSet"] = 'gri'
    if argdict['filtersFlag']:
        kwargs["filterSet"] = argdict['filtersFlag']

    for i in kwargs["filterSet"]:
        if i not in "grizy":
            log.error(
                "ERROR: the requested filter must be in the grizy filter set")
            return

    # WHICH IMAGE TYPE TO DOWNLOAD
    if argdict['stack']:
        kwargs["imageType"] = "stack"
    if argdict['warp']:
        kwargs["imageType"] = "warp"
    if argdict['closestFlag']:
        kwargs["imageType"] = "warp"

    # MJD WINDOW
    kwargs["mjdStart"] = argdict['mjdStart']
    kwargs["mjdEnd"] = argdict['mjdEnd']
    kwargs["window"] = False

    try:
        kwargs["window"] = int(argdict['closestFlag'])
    except:
        pass

    if not kwargs["window"]:
        if argdict['mjd'] and argdict['closestFlag'] == "before":
            kwargs["mjdEnd"] = argdict['mjd']
        elif argdict['mjd'] and argdict['closestFlag'] == "after":
            kwargs["mjdStart"] = argdict['mjd']
    else:
        if argdict['mjd'] and kwargs["window"] < 0:
            kwargs["mjdEnd"] = mjd
        elif argdict['mjd'] and kwargs["window"] > 0:
            kwargs["mjdStart"] = mjd

    # DOWNLOAD LOCATION
    if argdict['downloadFolderFlag']:
        home = expanduser("~")
        downloadFolderFlag = argdict['downloadFolderFlag'].replace("~", home)
    kwargs["downloadDirectory"] = downloadFolderFlag

    # xt-kwarg_key_and_value

    # DOWNLOAD THE IMAGES
    images = downloader(**kwargs)
    fitsPaths, jpegPaths, colorPath = images.get()
    jpegPaths += colorPath

    # POST-DOWNLOAD PROCESS IMAGES
    kwargs = {}
    kwargs["log"] = log
    kwargs["settings"] = settings
    # WIDTH OPTION
    kwargs["arcsecSize"] = 60
    if argdict['widthFlag']:
        kwargs["arcsecSize"] = float(argdict['widthFlag']) * 60.

    # ANNOTATE JPEG OPTIONS
    kwargs["crosshairs"] = True  # DEFAULT
    kwargs["scale"] = True
    if argdict['annotateFlag'] == False and argdict['noannotateFlag'] == True:
        kwargs["crosshairs"] = False  # DEFAULT
        kwargs["scale"] = False

    # INVERT OPTIONS
    kwargs["invert"] = False  # DEFAULT
    if argdict['invertFlag'] == True and argdict['noinvertFlag'] == False:
        kwargs["invert"] = True

    # GREYSCALE OPTIONS
    kwargs["greyscale"] = False  # DEFAULT
    if argdict['greyscaleFlag'] == True and argdict['nogreyscaleFlag'] == False:
        kwargs["greyscale"] = True

    # TRANSIENT DOT OPTIONS
    kwargs["transient"] = False  # DEFAULT
    if argdict['transientFlag'] == True and argdict['notransientFlag'] == False:
        kwargs["transient"] = True

    for j in jpegPaths:
        kwargs["imagePath"] = j

        # kwargs["transient"] = False

        # kwargs["invert"] = False
        # kwargs["greyscale"] = False
        oneImage = image(**kwargs)
        oneImage.get()

        # CALL FUNCTIONS/OBJECTS

    if "dbConn" in locals() and dbConn:
        dbConn.commit()
        dbConn.close()
    ## FINISH LOGGING ##
    endTime = times.get_now_sql_datetime()
    runningTime = times.calculate_time_difference(startTime, endTime)
    log.info('-- FINISHED ATTEMPT TO RUN THE cl_utils.py AT %s (RUNTIME: %s) --' %
             (endTime, runningTime, ))

    return


if __name__ == '__main__':
    #c = cl()
    main()
