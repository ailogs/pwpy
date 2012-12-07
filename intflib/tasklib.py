# Copyright 2012 Peter Williams
# Licensed under the GNU General Public License version 3 or higher

"""tasklib - library of clones of CASA tasks

The way that the casapy code is written it's basically impossible to
import its tasks into a straight-Python environment (trust me, I've
tried), so we're more-or-less duplicating lots of CASA code. I try
to provide saner semantics, APIs, etc.

The goal is to make task-like functionality as a real Python library
with no side effects, so that we can actually script data
processing. While we're at it, we make them available on the command
line.
"""

import casautil as cu
from kwargv import ParseKeywords, Custom

# Keep the tasks alphabetized!

__all__ = ('clearcal clearcal_cli '
           'concat concat_cli '
           'flagmanager_cli '
           'gaincal gaincal_cli GaincalConfig '
           'setjy setjy_cli SetjyConfig '
           'split split_cli SplitConfig '
           'cmdline_driver').split ()


## quickutil: usage die
#- snippet: usage.py (2012 Oct 01)
#- SHA1: ac032a5db2efb5508569c4d5ba6eeb3bba19a7ca
def showusage (docstring, short, stream, exitcode):
    if stream is None:
        from sys import stdout as stream
    if not short:
        print >>stream, 'Usage:', docstring.strip ()
    else:
        intext = False
        for l in docstring.splitlines ():
            if intext:
                if not len (l):
                    break
                print >>stream, l
            elif len (l):
                intext = True
                print >>stream, 'Usage:', l
        print >>stream, \
            '\nRun with a sole argument --help for more detailed usage information.'
    raise SystemExit (exitcode)

def checkusage (docstring, argv=None, usageifnoargs=False):
    if argv is None:
        from sys import argv
    if len (argv) == 1 and usageifnoargs:
        showusage (docstring, True, None, 0)
    if len (argv) == 2 and argv[1] in ('-h', '--help'):
        showusage (docstring, False, None, 0)

def wrongusage (docstring, *rest):
    import sys
    intext = False

    if len (rest) == 0:
        detail = 'invalid command-line arguments'
    elif len (rest) == 1:
        detail = rest[0]
    else:
        detail = rest[0] % tuple (rest[1:])

    print >>sys.stderr, 'error:', detail, '\n' # extra NL
    showusage (docstring, True, sys.stderr, 1)
#- snippet: die.py (2012 Oct 01)
#- SHA1: 3bdd3282e52403d2dec99d72680cb7bc95c99843
def die (fmt, *args):
    if not len (args):
        raise SystemExit ('error: ' + str (fmt))
    raise SystemExit ('error: ' + (fmt % args))
## end


# clearcal

clearcal_doc = \
"""
casatask clearcal [-w] <vis1> [more vises...]

Fill the imaging and calibration columns (MODEL_DATA, CORRECTED_DATA,
IMAGING_WEIGHT) of each measurement set with default values, creating
the columns if necessary.

-w - only create and fill the IMAGING_WEIGHT column
"""

clearcal_imaging_col_tmpl = {'_c_order': True,
                             'comment': '',
                             'dataManagerGroup': '',
                             'dataManagerType': '',
                             'keywords': {},
                             'maxlen': 0,
                             'ndim': 1,
                             'option': 0,
                             'shape': None,
                             'valueType': 'float'}
clearcal_imaging_dminfo_tmpl = {'TYPE': 'TiledShapeStMan',
                                'SPEC': {'DEFAULTTILESHAPE': [32, 128]},
                                'NAME': 'imagingweight'}

def clearcal (vis, weightonly=False):
    tb = cu.tools.table ()
    cb = cu.tools.calibrater ()

    # cb.open() will create the tables if they're not present, so
    # if that's the case, we don't actually need to run initcalset()

    tb.open (vis, nomodify=False)
    colnames = tb.colnames ()
    needinit = ('MODEL_DATA' in colnames) or ('CORRECTED_DATA' in colnames)
    if 'IMAGING_WEIGHT' not in colnames:
        c = dict (clearcal_imaging_col_tmpl)
        c['shape'] = tb.getcell ('DATA', 0).shape[-1:]
        tb.addcols ({'IMAGING_WEIGHT': c}, clearcal_imaging_dminfo_tmpl)
    tb.close ()

    if not weightonly:
        cb.open (vis)
        if needinit:
            cb.initcalset ()
        cb.close ()


def clearcal_cli (argv):
    checkusage (clearcal_doc, argv, usageifnoargs=True)

    argv = list (argv)
    weightonly = '-w' in argv
    if weightonly:
        sys.argv.remove ('-w')

    if len (argv) < 2:
        wrongusage (clearcal_doc, 'need at least one argument')

    cu.logger ()
    for vis in argv[1:]:
        clearcal (vis, weightonly=weightonly)


# concat

concat_doc = \
"""
casatask concat [-s] <input vises ...> <output vis>

Concatenate the visibility measurement sets.

-s - sort the output in time
"""

concat_freqtol = 1e-5
concat_dirtol = 1e-5

def concat (invises, outvis, timesort=False):
    import os.path
    tb = cu.tools.table ()
    ms = cu.tools.ms ()

    if os.path.exists (outvis):
        raise RuntimeError ('output "%s" already exists' % outvis)

    for invis in invises:
        if not os.path.isdir (invis):
            raise RuntimeError ('input "%s" does not exist' % invis)

    tb.open (invises[0])
    tb.copy (outvis, deep=True, valuecopy=True)
    tb.close ()

    ms.open (outvis, nomodify=False)

    for invis in invises[1:]:
        ms.concatenate (msfile=invis, freqtol=concat_freqtol,
                        dirtol=concat_dirtol)

    ms.writehistory (message='taskname=tasklib.concat', origin='tasklib.concat')
    ms.writehistory (message='vis = ' + ', '.join (invises), origin='tasklib.concat')
    ms.writehistory (message='timesort = ' + 'FT'[int (timesort)], origin='tasklib.concat')

    if timesort:
        ms.timesort ()

    ms.close ()


def concat_cli (argv):
    checkusage (concat_doc, argv, usageifnoargs=True)

    argv = list (argv)
    timesort = '-s' in argv
    if timesort:
        sys.argv.remove ('-s')

    if len (argv) < 3:
        wrongusage (concat_doc, 'need at least two arguments')

    cu.logger ()
    concat (argv[1:-1], argv[-1], timesort)


# flagmanager. Not really complicated enough to make it worth making a
# modular implementation to be driven from the CLI.

flagmanager_doc = \
"""
casatask flagmanager list <ms>
casatask flagmanager save <ms> <name>
casatask flagmanager restore <ms> <name>
casatask flagmanager delete <ms> <name>
"""

def flagmanager_cli (argv):
    import os.path
    checkusage (flagmanager_doc, argv, usageifnoargs=True)

    if len (argv) < 3:
        wrongusage (flagmanager_doc, 'expect at least a mode and an MS name')

    mode = argv[1]
    ms = argv[2]

    if mode == 'list':
        cu.logger ('info')
    elif mode == 'delete':
        # it WARNs 'deleting version xxx' ... yargh
        cu.logger ('severe')
    else:
        cu.logger ()

    try:
        factory = cu.tools.agentflagger
    except AttributeError:
        factory = cu.tools.testflagger

    af = factory ()
    af.open (ms)

    if mode == 'list':
        if len (argv) != 3:
            wrongusage (flagmanager_doc, 'expect exactly one argument in list mode')
        af.getflagversionlist ()
    elif mode == 'save':
        if len (argv) != 4:
            wrongusage (flagmanager_doc, 'expect exactly two arguments in save mode')
        name = argv[3]
        af.saveflagversion (versionname=name, merge='replace',
                            comment='version "%s" created by casatask flagmanager' % name)
    elif mode == 'restore':
        if len (argv) != 4:
            wrongusage (flagmanager_doc, 'expect exactly two arguments in restore mode')
        name = argv[3]
        af.restoreflagversion (versionname=name, merge='replace')
    elif mode == 'delete':
        if len (argv) != 4:
            wrongusage (flagmanager_doc, 'expect exactly two arguments in delete mode')
        name = argv[3]

        if not os.path.isdir (os.path.join (ms + '.flagversions', 'flags.' + name)):
            # This condition only results in a WARN from deleteflagversion ()!
            raise RuntimeError ('version "%s" doesn\'t exist in "%s.flagversions"'
                                % (name, ms))

        af.deleteflagversion (versionname=name)
    else:
        wrongusage (flagmanager_doc, 'unknown flagmanager mode "%s"' % mode)

    af.done ()


# gaincal
#
# I've folded in the bandpass functionality since there's
# so much overlap. Some limitations that this leads to:
#
# - bandpass solint has a frequency component that we don't support
# - bandpass combine defaults to 'scan'

gaincal_doc = \
"""
casatask gaincal vis=<MS> caltable=<TBL> [keywords]

Compute calibration parameters from data. Encompasses the functionality
of CASA tasks 'gaincal' *and* 'bandpass'.

vis=
  Input dataset

caltable=
  Output calibration table (can exist if append=True)

gaintype=
  Kind of gain solution:
    G       - gains per poln and spw (default)
    T       - like G, but one value for all polns
    GSPLINE - like G, with a spline fit. "Experimental"
    B       - bandpass
    BPOLY   - bandpass with polynomial fit. "Somewhat experimental"
    K       - antenna-based delays
    KCROSS  - global cross-hand delay ; use parang=True
    XY+QU   - ?
    XYf+QU  - ?

calmode=
  What parameters to solve for: amplitude ("a"), phase ("p"), or both
  ("ap"). Default is "ap". Not used in bandpass solutions.

solint=
  Solution interval; this is an upper bound, but solutions
  will be broken across certain boundaries according to "combine".
  'inf'    - solutions as long as possible (the default)
  'int'    - one solution per integration
  (str)    - a specific time with units (e.g. '5min')
  (number) - a specific time in seconds

combine=
  Comma-separated list of boundary types; solutions will NOT be
  broken across these boundaries. Types are:
    field scan spw

refant=
  Comma-separated list of reference antennas in decreasing
  priority order.

solnorm=
  Normalize solution amplitudes to 1 after solving (only applies
  to gaintypes G, T, B). Also normalizes bandpass phases to zero
  when solving for bandpasses. Default: false.

append=
  Whether to append solutions to an existing table. If the table
  exists and append=False, the table is overwritten! (Default: false)

*** Pre-applied calibrations:

gaintable=
  Comma-separated list of calibration tables to apply on-the-fly
  before solving

gainfield=
  SEMICOLON-separated list of field selections to apply for each gain table.
  If there are fewer items than there are gaintable items, the list is
  padded with blank items, implying no selection by field.

interp=
  COMMA-separated list of interpolation types to use for each gain
  table. If there are fewer items, the list is padded with 'linear'
  entries. Allowed values:
    nearest linear cubic spline

spwmap=
  SEMICOLON-separated list of spectral window mappings for each
  existing gain table; each record is a COMMA-separated list of
  integers. For the i'th spw in the dataset, spwmap[i] specifies
  the record in the gain table to use. For instance [0, 0, 1, 1]
  maps four spws in the UV data to just two spectral windows in
  the preexisting gain table.

opacity=
  Comma-separated list of opacities in nepers. One for each spw; if
  there are more spws than entries, the last entry is used for the
  remaining spws.

gaincurve=
  Whether to apply VLA-specific built in gain curve correction
  (default: false)

parang=
  Whether to apply parallactic angle rotation correction
  (default: false)

*** Low-level parameters:

minblperant=
  Number of baselines for each ant in order to solve (default: 4)

minsnr=
  Min. SNR for acceptable solutions (default: 3.0)

preavg=
  Interval for pre-averaging data within each solution interval,
  in seconds. Default is -1, meaning not to pre-average.

*** Standard keywords

antenna=
field=
intent=
observation=
scan=
spw=
taql=
timerange=
uvrange=
  Standard UV data selection keywords

loglevel=
  Standard logging keyword "loglevel" (default: warn; allowed:
  severe warn info info1 info2 info3 info4 info5 debug1 debug2 debugging)
"""

class GaincalConfig (ParseKeywords):
    vis = Custom (str, required=True)
    caltable = Custom (str, required=True)
    gaintype = 'G'
    calmode = 'ap'

    solint = 'inf'
    combine = [str]
    refant = [str]
    solnorm = False
    append = False
    minblperant = 4
    minsnr = 3.0
    preavg = -1.0

    gaintable = [str]
    gainfield = Custom ([str], sep=';')
    interp = [str]
    opacity = [float]
    gaincurve = False
    parang = False

    @Custom ([str], sep=';')
    def spwmap (v):
        return [map (int, e.split (',')) for e in v]

    # gaincal keywords: splinetime npointaver phasewrap smodel
    # bandpass keywords: fillgaps degamp degphase visnorm maskcenter
    #   maskedge

    antenna = str
    field = str
    intent = str
    observation = str
    scan = str
    spw = str
    taql = str # msselect
    timerange = str
    uvrange = str

    loglevel = 'warn' # teeny hack for CLI


def gaincal (cfg):
    cb = cu.tools.calibrater ()
    cb.open (filename=cfg.vis, compress=False, addcorr=False, addmodel=False)

    # Selection

    selkws = {}

    for k in 'field intent observation scan spw uvrange'.split ():
        selkws[k] = getattr (cfg, k) or ''

    for p in 'antenna:baseline timerange:time taql:msselect'.split ():
        ck, sk = p.split (':')
        selkws[sk] = getattr (cfg, ck) or ''

    selkws['chanmode'] = 'none'
    cb.selectvis (**selkws)

    # On-the-fly calibrations

    n = len (cfg.gaintable)

    if len (cfg.gainfield) < n:
        cfg.gainfield += [''] * (n - len (cfg.gainfield))
    elif len (cfg.gainfield) > n:
        raise ValueError ('more "gainfield" entries than "gaintable" entries')

    if len (cfg.interp) < n:
        cfg.interp += ['linear'] * (n - len (cfg.interp))
    elif len (cfg.interp) > n:
        raise ValueError ('more "interp" entries than "gaintable" entries')

    if len (cfg.spwmap) < n:
        cfg.spwmap += [[-1]] * (n - len (cfg.interp))
    elif len (cfg.spwmap) > n:
        raise ValueError ('more "spwmap" entries than "gaintable" entries')

    for table, field, interp, spwmap in zip (cfg.gaintable, cfg.gainfield,
                                             cfg.interp, cfg.spwmap):
        cb.setapply (table=table, field=field, interp=interp, spwmap=spwmap,
                     t=0., calwt=True)

    if len (cfg.opacity):
        cb.setapply (type='TOPAC', opacity=cfg.opacity, t=-1, calwt=True)

    if cfg.gaincurve:
        cb.setapply (type='GAINCURVE', t=-1, calwt=True)

    if cfg.parang:
        cb.setapply (type='P')

    # Solve

    solkws = {}

    for k in 'append preavg minblperant minsnr solnorm'.split ():
        solkws[k] = getattr (cfg, k)

    for p in 'caltable:table calmode:apmode'.split ():
        ck, sk = p.split (':')
        solkws[sk] = getattr (cfg, ck)

    if isinstance (cfg.solint, (int, float)):
        solkws['t'] = '%fs' % cfg.solint # sugar
    else:
        solkws['t'] = str (cfg.solint)

    solkws['combine'] = ','.join (cfg.combine)
    solkws['refant'] = ','.join (cfg.refant)
    solkws['phaseonly'] = False
    solkws['type'] = cfg.gaintype.upper ()

    if solkws['type'] == 'GSPLINE':
        cb.setsolvegainspline (**solkws)
    elif solkws['type'] == 'BPOLY':
        cb.setsolvebandpoly (**solkws)
    else:
        cb.setsolve (**solkws)

    cb.solve ()
    cb.close ()


def gaincal_cli (argv):
    checkusage (gaincal_doc, argv, usageifnoargs=True)
    cfg = GaincalConfig ().parse (argv[1:])
    cu.logger (cfg.loglevel)
    gaincal (cfg)


# setjy

setjy_doc = \
"""
casatask setjy vis= [keywords]

Insert model data into a measurement set. We force usescratch=False
and scalebychan=True. You probably want to specify "field".

fluxdensity=
  Up to four comma-separated numbers giving Stokes IQUV intensities in
  Jy. Default values are [-1, 0, 0, 0]. If the Stokes I intensity is
  negative (i.e., the default), a "sensible default" will be used:
  detailed spectral models if the source is known (see "standard"), or
  1 otherwise. If it is zero and "modimage" is used, the flux density
  of the model image is used. The built-in standards do NOT have
  polarimetric information, so for pol cal you do need to manually
  specify the flux density information -- or see the program
  "mspolmodel".

modimage=
  An image to use as the basis for the source's spatial structure and,
  potentialy, flux density (if fluxdensity=0). Only usable for Stokes
  I.  If the verbatim value of "modimage" can't be opened as a path,
  it is assumed to be relative to the CASA data directory; a typical
  value might be "nrao/VLA/CalModels/3C286_C.im".

spindex=
reffreq=
  If using fluxdensity, these specify the spectral dependence of the
  values, such that S = fluxdensity * (freq/reffreq)**spindex. Reffreq
  is in GHz. Default values are 0 and 1, giving no spectral
  dependence.

standard='Perley-Butler 2013'
  Solar-system standards are not supported by this implementation, so
  acceptable values are: Baars, Perley 90, Perley-Taylor 95,
  Perley-Taylor 99, Perley-Butler 2010, Perley-Butler 2013.

Supported selection keywords: field obs scan spw time

And standard logging keyword "loglevel" (default: warn; allowed:
  severe warn info info1 info2 info3 info4 info5 debug1 debug2 debugging)
"""

class SetjyConfig (ParseKeywords):
    vis = Custom (str, required=True)
    modimage = str
    fluxdensity = [-1., 0., 0., 0.]
    spindex = 0.
    reffreq = 1. # GHz
    standard = 'Perley-Butler 2013'

    # supported selection keywords:
    field = str
    obs = str
    scan = str
    spw = str
    time = str

    # teeny hack for CLI
    loglevel = 'warn'


def setjy (cfg):
    import os.path
    kws = {}

    for kw in 'field fluxdensity time scan spw standard'.split ():
        v = getattr (cfg, kw)
        if v is None:
            v = ''
        kws[kw] = v

    kws['reffreq'] = str (cfg.reffreq) + 'GHz'
    kws['observation'] = cfg.obs or ''
    kws['spix'] = cfg.spindex
    kws['scalebychan'] = True # don't think you'd ever want false??

    if cfg.modimage is None:
        kws['modimage'] = ''
    else:
        if os.path.isdir (cfg.modimage):
            mi = cfg.modimage
        else:
            mi = cu.datadir (cfg.modimage)
            if not os.path.isdir (mi):
                raise RuntimeError ('no model image "%s" or "%s"' % (cfg.modimage, mi))
        kws['modimage'] = mi

    im = cu.tools.imager ()
    im.open (cfg.vis, usescratch=False) # don't think you'll ever want True?
    im.setjy (**kws)
    im.close ()


def setjy_cli (argv):
    checkusage (setjy_doc, argv, usageifnoargs=True)
    cfg = SetjyConfig ().parse (argv[1:])
    cu.logger (cfg.loglevel)
    setjy (cfg)


# split
#
# note: spw=999 -> exception; scan=999 -> no output, or error, generated

split_doc = \
"""
casatask split vis=<MS> out=<MS> [keywords...]

timebin=
  Time-average data into bins of "timebin" seconds; defaults to no averaging

step=
  Frequency-average data in bins of "step" channels; defaults to no averaging

col=all
  Extract the column "col" as the DATA column. If "all", copy all available
  columns without renaming. Possible values:
  DATA MODEL_DATA CORRECTED_DATA FLOAT_DATA LAG_DATA

combine=[col1,col2,...]
  When time-averaging, don't start a new bin when the specified columns change.
  Acceptable column names:
  scan state

Also accepts standard u-v filtering keywords:
  baseline correlation field intent obs spw subarray taql time uvrange

And standard logging keyword "loglevel" (default: warn; allowed:
  severe warn info info1 info2 info3 info4 info5 debug1 debug2 debugging)
"""

class SplitConfig (ParseKeywords):
    vis = Custom (str, required=True)
    out = Custom (str, required=True)

    timebin = float # seconds
    step = 1
    col = 'all'
    combine = [str]

    # basic selection keywords:
    baseline = str
    correlation = str
    field = str
    intent = str
    obs = str
    scan = str
    spw = str
    subarray = str
    taql = str
    time = str
    uvrange = str

    # teeny hack for CLI
    loglevel = 'warn'

def split (cfg):
    import os.path
    kws = {}

    # ms.split() seems to merrily overwrite existing MSes which
    # seems pretty questionable. Forbid that for now as best we can.
    # Race conditions ahoy.
    if os.path.exists (cfg.out):
        raise RuntimeError ('destination "%s" already exists' % cfg.out)

    for k in ('baseline correlation field intent obs scan spw step subarray '
              'taql time uvrange').split ():
        v = getattr (cfg, k)
        if v is None:
            v = ''
        kws[k] = v

    for m in ('out:outputms col:whichcol').split ():
        myk, ck = m.split (':')
        kws[ck] = getattr (cfg, myk)

    if cfg.timebin is None:
        kws['timebin'] = '-1s'
    else:
        kws['timebin'] = str (cfg.timebin) + 's'

    kws['combine'] = ','.join (cfg.combine)

    ms = cu.tools.ms ()
    ms.open (cfg.vis)
    ms.split (**kws)
    ms.close ()


def split_cli (argv):
    checkusage (split_doc, argv, usageifnoargs=True)
    cfg = SplitConfig ().parse (argv[1:])
    cu.logger (cfg.loglevel.upper ()) # log warnings, errors to stderr
    split (cfg)


# Driver for command-line access

def cmdline_usage (stream, exitcode):
    print >>stream, 'usage: casatask <task> [task-specific arguments]'
    print >>stream
    print >>stream, 'Supported tasks:'
    print >>stream

    for name in sorted (globals ().iterkeys ()):
        if name.endswith ('_cli'):
            print >>stream, name[:-4]

    raise SystemExit (exitcode)


def cmdline_driver (argv):
    import sys

    if len (argv) < 2 or argv[1] == '--help':
        cmdline_usage (sys.stdout, 0)

    driver = globals ().get (argv[1] + '_cli')
    if driver is None:
        print >>sys.stderr, 'error: unknown task "%s"; run with no arguments for a list' % argv[1]
        sys.exit (1)

    subargv = [' '.join (argv[:2])] + argv[2:]
    driver (subargv)


if __name__ == '__main__':
    import sys
    cmdline_driver (sys.argv)
