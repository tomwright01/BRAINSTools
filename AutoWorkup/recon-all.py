import sys
import getopt
import os
from workflow_reconall import create_reconall, mkdir_p

def help():
    print """
This program runs FreeSurfer's recon-all as a nipype script. This allows 
for better parallel processing for easier experimenting with new and/or
improved processing steps.

Usage:
python recon-all.py --T1 <infile1> --subject <name> [--T1 <infile2>... --T2 <inT2> --FLAIR <inFLAIR>]

Required inputs;
-i or --T1 <infile1>      Input T1 image. Multiple T1 images may be used as inputs each requiring its own
                          input flag

-s or --subject <name>    Name of the subject being processed.

--subjects_dir <dir>      Input subjects directory defines where to run workflow and output results

Optional inputs:
--T2 <inT2>               Input T2 image. T2 images are not used for processing, but the image will be converted
                          to .mgz format.

--FLAIR <inFLAIR>         Input FLAIR image. FLAIR images are not used for processing, but the image will be 
                              converted to .mgz format.

--plugin <plugin>         Plugin to use when running workflow

-q or --queue <queue>     Queue to submit as a qsub argument (requires 'SGE' or 'SGEGraph' plugin)

--qcache                  Make qcache

--cw256                   Include this flag after -autorecon1 if images have a FOV > 256.  The
                          flag causes mri_convert to conform the image to dimensions of 256^3.

--longbase <name>         Set the longitudinal base template. If a longitudinal 
                          base is set, no input files will be used/required.

Author:
David Ellis
University of Iowa
    """

def procargs(argv):
    config = { 'in_T1s' : list(),
               'subject_id' : None,
               'in_T2' : None,
               'in_FLAIR' : None,
               'plugin' : 'Linear',
               'queue' : None,
               'subjects_dir' : None,
               'long_base' : None,
               'qcache' : False,
               'cw256' : False,
               'longitudinal' : False,
               'timepoints' : list(),
               'openmp', None }

    try:
        opts, args = getopt.getopt(argv, "hi:q:s:", ["help",
                                                     "T1=",
                                                     "subject=",
                                                     "T2=",
                                                     "FLAIR=",
                                                     "plugin=",
                                                     "queue=",
                                                     "subjects_dir=",
                                                     "qcache",
                                                     "cw256",
                                                     "longbase=",
                                                     "tp=",
                                                     "openmp="])
    except getopt.GetoptError:
        print "Error occured when parsing arguments"
        help()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            help()
            sys.exit()
        elif opt in ("-i", "--T1"):
            config['in_T1s'].append(os.path.abspath(arg))
            if not os.path.isfile(arg):
                print "ERROR: input T1 image must be an existing image file"
                print "{0} does not exist".format(arg)
                sys.exit(2)
        elif opt in ("-s", "--subject"):
            config['subject_id'] = arg
        elif opt in ("--T2"):
            config['in_T2'] = os.path.abspath(arg)
            if not os.path.isfile(config['in_T2']):
                print "ERROR: input T2 image must be an existing image file"
                print "{0} does not exist".format(config['in_T2'])
                sys.exit(2)
        elif opt in ("--FLAIR"):
            config['in_FLAIR'] = os.path.abspath(arg)
            if not os.path.isfile(config['in_FLAIR']):
                print "ERROR: input FLAIR image must be an existing image file"
                print "{0} does not exist".format(config['in_FLAIR'])
                sys.exit(2)
        elif opt in ("--plugin"):
            config['plugin'] = arg
        elif opt in ("-q", "--queue"):
            config['queue'] = arg
        elif opt in ("--subjects_dir"):
            config['subjects_dir'] = os.path.abspath(arg)
            # Set the subjects directory environment variable
#            os.environ["SUBJECTS_DIR"] = subjects_dir
        elif opt in ("--qcache"):
            config['qcache'] = True
        elif opt in ("--cw256"):
            config['cw256'] = True
        elif opt in ("--longbase"):
            config['longitudinal'] = True
            config['long_base'] = arg
            #TODO: Check that the longitudinal base pre-exists
        elif opt in ("--tp"):
            config['timepoints'].append(arg)
        elif opt in ("--openmp"):
            try:
                config['openmp'] = int(arg)
            except ValueError:
                print "ERROR: --openmp flag accepts only integers"
                sys.exit(2)

    if config['subject_id'] == None:
        print "ERROR: Must set subject_id using -s flag"
        help()
        sys.exit(2)
        
    if not config['longitudinal'] and len(config['in_T1s']) == 0:
        print "ERROR: Must have at least one input T1 image"
        help()
        sys.exit(2)
        
    if config['subjects_dir'] == None:
        print "ERROR: Must set the subjects_dir before running"
        help()
        sys.exit(2)
        
    print 'Subject ID: {0}'.format(config['subject_id'])
    print 'Input T1s: {0}'.format(config['in_T1s'])
    if config['in_T2'] != None:
        print 'Input T2: {0}'.format(config['in_T2'])
    if config['in_FLAIR'] != None:
        print 'Input FLAIR: {0}'.format(config['in_FLAIR'])
    print 'Plugin: {0}'.format(config['plugin'])
    print 'Make qcache: {0}'.format(config['qcache'])
    print 'Conform to 256: {0}'.format(config['cw256'])
    if config['queue'] != None:
        print 'Queue: {0}'.format(config['queue'])

    if config['longitudinal']:
        # set input requirements for running longitudinally
        # print erros when inputs are not set correctly
        print 'Running longitudinally'
        print 'Longitudinal Base: {0}'.format(config['long_base'])
    return config

def which(program):
    # code from http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
    return None


def checkenv():
    """Check for the necessary FS environment variables"""
    # will search for test program to ensure that
    # it has been added to the PATH variable
    test_program = 'mris_sphere'
    fs_home = os.environ.get('FREESURFER_HOME')
    print "FREESURFER_HOME: {0}".format(fs_home)
    if fs_home == None:
        print "ERROR: please set FREESURFER_HOME before running the workflow"
    elif not os.path.isdir(fs_home):
        print "ERROR: FREESURFER_HOME must be set to a valid directory before running workflow"
    elif which(test_program) == None:
        print """ERROR: Could not find necessary executable in path
        Please source the setup script before running the workflow:
        source {0}/SetUpFreeSurfer.sh
        """.format(fs_home)
    else:
        return fs_home
    sys.exit(2)

    
def modify_qsub_args(queue, memoryGB, minThreads, maxThreads, stdout='/dev/null', stderr='/dev/null'):
    """
    Code from BRAINSTools:
    https://github.com/BRAINSia/BRAINSTools.git
    BRAINSTools/AutoWorkup/utilities/distributed.py

    Outputs qsub_args string for Nipype nodes
    queue is the string to specify the queue "-q all.q | -q HJ,ICTS,UI"
    memoryGB is a numeric in gigabytes to be given (ie 2.1 will result in "-l mem_free=2.1G")
          if memoryGB = 0, then it is automatically computed.
    minThreads The fewest number of threads to use (if an algorithm has benifits from more than 1 thread)
    maxThreads The max number of threads to use (if an algorithm is not multi-threaded, then just use 1)
    stdout Where to put stdout logs
    stderr Where to put stderr logs

    >>> modify_qsub_args('test', 2, 5, None)
    -S /bin/bash -cwd -pe smp 5 -l mem_free=2G -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 2, 5, -1 )
    -S /bin/bash -cwd -pe smp 5- -l mem_free=2G -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 8, 5, 7)
    -S /bin/bash -cwd -pe smp 5-7 -l mem_free=8G -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 8, 5, 7, -1)
    -S /bin/bash -cwd -pe smp 5-7 -l mem_free=8G -o /dev/null -e /dev/null test FAIL
    >>> modify_qsub_args('test', 1, 5, 7, stdout='/my/path', stderr='/my/error')
    -S /bin/bash -cwd -pe smp 5-7 -l mem_free=1G -o /my/path -e /my/error test FAIL
    """
    assert memoryGB <= 48 , "Memory must be supplied in GB, so anything more than 24 seems not-useful now."

    ## NOTE: At least 1 thread needs to be requested per 2GB needed
    memoryThreads = int(math.ceil((old_div(math.ceil(memoryGB),2)))) #Ensure that threads are integers
    minThreads = max(minThreads, memoryThreads)
    maxThreads = max(maxThreads, memoryThreads)
    maxThreads=int(maxThreads) # Ensure that threads are integers
    minThreads=int(minThreads) # Ensure that threads are integers

    if maxThreads is None or minThreads == maxThreads:
       threadsRangeString =  '{0}'.format(minThreads)
       maxThreads = minThreads
    elif maxThreads == -1:
       threadsRangeString= '{0}-'.format(minThreads)
       maxThreads = 12345 #HUGE NUMBER!
    else:
       threadsRangeString= "{0}-{1}".format(minThreads,maxThreads)

    if maxThreads < minThreads:
       assert  maxThreads > minThreads, "Must specify maxThreads({0}) > minThreads({1})".format(minThreads,maxThreads)

    ## TODO:  May need to figure out how to set memory and threads for cluster.
    ## for now just let the number of threads requested take care of this because
    ## the job manager on helium is really slow with lots of constraints
    ##  -l mem_free={mem}

    ## format_str = '-S /bin/bash -cwd -pe smp {mint}{maxt} -o {stdout} -e {stderr} {queue}'
    format_str = '-S /bin/bash -cwd -pe smp {totalThreads} -o {stdout} -e {stderr} {queue}'.format(
                 mint=minThreads, maxt=threadsRangeString,
                 totalThreads=threadsRangeString,
                 mem=memoryGB,
                 stdout=stdout, stderr=stderr, queue=queue)
    return format_str

def main(argv):
    config = procargs(argv)
    config['FREESURFER_HOME'] = checkenv()
    if config['longitudinal']:
        long_id = "{0}.long.{1}".format(config['subject_id'], config['long_base'])
        subject_folder = long_id
    else:
        subject_folder = config['subject_id']
    
    # Experiment Info
    ExperimentInfo = {"Atlas": {"TEMP_CACHE": os.path.join(config['subjects_dir'], config['subject_id']),
                                "LOG_DIR": os.path.join(config['subjects_dir'], 'log')}}
    
    # Create necessary output directories
    for item in ExperimentInfo["Atlas"].iteritems():
        mkdir_p(item[1])
    for folder in ['bem', 'label', 'mri', 'scripts', 'src', 'stats', 'surf', 'tmp', 'touch', 'trash']:
        mkdir_p(os.path.join(config['subjects_dir'], subject_folder, folder))
        if folder == 'mri':
            mkdir_p(os.path.join(config['subjects_dir'], subject_folder, folder, 'orig'))
            mkdir_p(
                os.path.join(config['subjects_dir'], subject_folder, folder, 'transforms'))

    # Now that we've defined the args and created the folders, create workflow
    reconall = create_reconall(config['in_T1s'],
                               config['subject_id'],
                               config['in_T2'],
                               config['in_FLAIR'],
                               config['subjects_dir'],
                               config['qcache'],
                               config['cw256'],
                               config['FREESURFER_HOME'],
                               config['longitudinal'],
                               config['long_base'],
                               config['timepoints'],
                               plugin_args
                               )

    # Set workflow configurations
    reconall.config['execution'] = {
        'stop_on_first_crash': 'false',
        'stop_on_first_rerun': 'false',
        # This stops at first attempt to rerun, before running, and before
        # deleting previous results.
        'hash_method': 'timestamp',
        'remove_unnecessary_outputs': 'false',
        'use_relative_paths': 'false',
        'remove_node_directories': 'false',
    }
    reconall.config['logging'] = {
        'workflow_level': 'DEBUG',
        'filemanip_level': 'DEBUG',
        'interface_level': 'DEBUG',
        'log_directory': ExperimentInfo["Atlas"]["LOG_DIR"]
    }

    # Run Workflow
    reconall.base_dir = ExperimentInfo["Atlas"]["TEMP_CACHE"]
    if config['plugin'] in ('SGE', 'SGEGraph') and config['queue'] != None:
        reconall.run(plugin=config['plugin'], plugin_args=dict(qsub_args='-q ' + config['queue']))
    elif config['plugin'] != 'Linear':
        reconall.run(plugin=config['plugin'])
    else:
        reconall.run()


if __name__ == "__main__":
    main(sys.argv[1:])

