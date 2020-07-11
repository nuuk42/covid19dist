# import basics
import sys, os, logging, atexit
import fnmatch
import io
import base64
from datetime import datetime

# import WEB interface
from flask import Flask, render_template, current_app, url_for, g, request

import service_utl
from kool import get_json_attribute

import urllib.request as r
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


# ---------------------------------------------------------------------------
#
#  Globals
#

# root logger
log = None
http_log = None

# create the app
application = Flask(__name__)

# -----------------------
def to_lines(f):
    """ Convert the stream from the file 'f' into an enumarable object """
    line = f.readline()
    while line:
        yield line.decode('ascii')
        line = f.readline()


# ---------------------------------------------------------------------------
#
def get_data(country, timespan_days):
    log.debug('> country=%s timespan_days=%d' % (country,timespan_days) )
    url = 'https://datahub.io/core/covid-19/r/time-series-19-covid-combined.csv'
    # cal start-date
    now = datetime.now()
    start_date = np.datetime64('%4d-%02d-%02d' %(now.year,now.month,now.day) ) - timespan_days

    # resulting lists
    country_list, list_date, list_registered, list_ill = [ [],[],[],[] ]

    # open data source
    with r.urlopen(r.Request(url, headers={'Accept':'*/*','User-Agent':'curl/7.60.0'})) as http_response:
        rd = csv.reader( to_lines(http_response) )
        next(rd) # skip first line

        # read only value after the start date
        # selected_values is an nested array: [ [], [], [], .....]
        selected_values = filter(lambda l: np.datetime64(l[0])>=start_date , rd )

        for row in selected_values:
            # build country list
            country_list.append(row[1])
            # check selected country.
            if row[1].upper()==country.upper():

                # setup the date of the record
                row_date = np.datetime64(row[0])

                # setup values - some columns may be empty - assume 0 in this case
                row_registerd, row_recoverd, row_dead = list(x for x in map(lambda y: int(0) if len(y)==0 else int(y), row[5:8]) )
                # calc. number of persons currenlty ill
                row_ill  = row_registerd - row_recoverd - row_dead

                # for some countries we get multible values for the same day. 
                if row_date in list_date:
                    # get the index
                    ix = list_date.index(row_date)
                    # sum this up
                    list_ill[ix] += row_ill  
                    list_registered[ix] += row_registerd
                else:
                    # add data for one day
                    list_date.append( row_date )
                    list_ill.append( row_ill )
                    list_registered.append( row_registerd )

    # calculate the newly registered cases per day. Note: this list has one value less then the others...
    list_new_reg = [ list_registered[ix]-list_registered[ix-1] for ix in range(1,len(list_registered)) ]
    # create the data house....
    data = { 'date':list_date[1:], 'registered':list_registered[1:], 'ill':list_ill[1:], 'new_reg':list_new_reg }

    # remove duplicated values from the list of countries and sort the result
    country_set = sorted( set(country_list) )

    log.debug('< number of data points: %d number of countries: %d' % (len(data['date']), len(country_set) )  )
    return data, country_set

def create_image(data):
    """ Create image for data 
    
    The function will return the firgure object with 3 plots:
    - number of currently ill persons
    - total number of registered cases
    - number of newly registered cases
    """
    log.debug('>')
    # --------------
    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    days = mdates.DayLocator()  # every day:

    years_fmt = mdates.DateFormatter('%Y')
    month_fmt = mdates.DateFormatter('%m')
    day_fmt = mdates.DateFormatter('%m.%d')
    # -----------------------
    # select format
    fig,ax=plt.subplots(figsize=(12,8))
    # format the ticks
    ax.xaxis.set_major_locator(days)
    ax.xaxis.set_major_formatter(day_fmt)

    # create the 3 different plots
    ax.plot('date','ill',data=data,label='currently ill')
    ax.plot('date','registered',data=data,label='registered')
    ax.plot('date','new_reg',data=data,label='newly infected per day')

    # rotates and right aligns the x labels, and moves the bottom of the axes up to make room for them
    fig.autofmt_xdate()
    ax.legend(loc='upper center', shadow=True, fontsize='x-large')
    ax.grid(True)
    # return firgure
    log.debug('<')
    return fig

def figure_2_png(fig):
    """ convert a figure object into a base64 PNG string """
    log.debug('>')
    # Convert plot to PNG image
    pngImage = io.BytesIO()
    FigureCanvas(fig).print_png(pngImage)
    
    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

    log.debug('<')
    return pngImageB64String

# ---------------------------------------------------------------------------
#
#  WEB Methods 
#

# --------------- / ---------------------------------------------------------
# main route
@application.route('/')
def index():
    country = request.args.get('country','Germany')
    timespan_days = int(request.args.get('timespan','30') )
    data, country_set = get_data(country, timespan_days)

    # check, if data found for country...
    if len(data['date']) > 0:
        figure = create_image(data)
        return render_template('index.html',image=figure_2_png(figure), country=country,countries=country_set,timespan=timespan_days)
    return render_template('unknown_country.html',country=country,countries=country_set,timespan=timespan_days)

# ---------------------------------------------------------------------------
#
#  WEB Infrastructure
#

# ---------------------------------------------------------------------------
def before_request():
    log.debug('> %s' %g)
    log.debug('<')

# ---------------------------------------------------------------------------
def tear_down_request(application):
    log.debug('> %s' % application)
    log.debug('<')

# ---------------------------------------------------------------------------
def sig_term_handler(signum, stack):
    log.warning('SIGTERM')

# ---------------------------------------------------------------------------
def atexit_handler():
    """ Called before exit of the process    """
    pass

# ---------------------------------------------------------------------------
def init():
    """ Init infrastructure

    - init logging
    - register before_request handler
    - register teardown handler
    - register handler for signal "SIGTERM"

    """
    # get access to the global variables
    global log, http_log, application, db_pool

    # get the logging configuration from the environment
    log_config = get_json_attribute(os.getenv("LOG_CONFIG"))

    # get the root logger and configure it with the default value from "LOG_CONFIG"
    root_log = logging.getLogger()
    root_log.setLevel(service_utl.get_numeric_loglevel(log_config.Level.Default))

    # remove all existing handlers
    root_log.handlers = []

    # create two log handlers: one writes to stdout - used for WARNING+INFO+DEBUG
    #                          one writes to stderr - used for ERROR

    # get a new stream-handler sending log-data to stderr for log-level > WARNING
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.formatter = logging.Formatter(fmt=log_config.Format)
    stderr_handler.addFilter( lambda record: record.levelno > logging.WARNING )
    root_log.addHandler(stderr_handler)

    # get a new stream-handler sending log-data to stdout for log-level <= WARNING 
    stdout_handler = logging.StreamHandler(sys.stdout)
    ## stdout_handler = logging.StreamHandler(sys.stderr)
    stdout_handler.formatter = logging.Formatter(fmt=log_config.Format)
    stdout_handler.addFilter( lambda record: record.levelno <= logging.WARNING )
    root_log.addHandler(stdout_handler)

    # get out "local" loggers
    http_log = logging.getLogger('http')
    log = logging.getLogger(__name__)
    log.setLevel(service_utl.get_numeric_loglevel(log_config.Level.Main))

    # register startup
    application.before_request(before_request)

    # register teardown
    # NOTE: in debug-mode, the tear-down functions are NOT called
    application.teardown_request(tear_down_request)

    # we register a handler here that will close the connection pool
    atexit.register(atexit_handler)

    # log the path
    source_location = os.path.dirname(os.path.abspath(__file__))
    print("Source location: %s" % source_location)  # /a/b/c/d/e


    for root, dir, files in os.walk(source_location):
        print( root )
        for items in fnmatch.filter(files, "*"):
            print ("..." + items)


    log.debug('done with init')


# ---------------------------------------------------------------------------
init()
if __name__ == '__main__':
    # Get port from environment variable or choose 9099 as local default and run...
    application.run(host='0.0.0.0', port=int(os.getenv("PORT", 9099)), debug=True)
