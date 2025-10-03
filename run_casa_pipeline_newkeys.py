#!/usr/bin/env python
# 
# Run this script INSIDE CASA or with CASA available.
# 

# This is the PHANGS ALMA staging and imaging script.

# This script loads the project data, constructs the PHANGS pipeline
# handlers, and then executes each step: staging, imaging,
# postprocessing. The user has control over which targets, spectral
# products, and steps run.

# This is a documented version that we provide with the main pipeline
# repository as an example tou users. You should be able to modify
# this script to get a good start on your own wrapper to the pipeline.


##############################################################################
# Load routines, initialize handlers
##############################################################################

import os, sys
import importlib

# Pipeline directory. Set this to the location on your system

pipedir = '/data/c3040163/llama/alma/phangs_imaging_scripts-master/'

# Location of the master key. Set this to the master key that points
# to all of the keys for your project.

key_file = '/data/c3040163/llama/alma/phangs_imaging_scripts-master/full_run_newkeys/keys/master_key.txt'

# Make missing directories

for dirname in ['singledish', 'cleanmasks']:
    if not os.path.exists(dirname):
        os.mkdir(dirname)

# Change directory to the pipeline directory.

startdir = os.getcwd()

os.chdir(pipedir)

# Make sure we are inside CASA (you will need to modify this to use
# the pipeline via a command line call)

sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(os.getcwd())+os.sep+'analysis_scripts')
from packaging import version # need CASA 6+!
 


# Import the logger and initialize the logging. You can change the
# level of message that you want to see by changing "level" here or
# save to a logfile with the keyword.

from phangsPipeline import phangsLogger as pl
pl.setup_logger(level='DEBUG', logfile=None)

# Imports

# sys.path.insert(1, )
from phangsPipeline import handlerKeys as kh
from phangsPipeline import handlerVis as uvh
from phangsPipeline import handlerImaging as imh
from phangsPipeline import handlerPostprocess as pph

# Initialize the various handler objects. First initialize the
# KeyHandler, which reads the master key and the files linked in the
# master key. Then feed this keyHandler, which has all the project
# data, into the other handlers (VisHandler, ImagingHandler,
# PostProcessHandler), which run the actual pipeline using the project
# definitions from the KeyHandler.

this_kh = kh.KeyHandler(master_key=key_file)
this_uvh = uvh.VisHandler(key_handler=this_kh)
this_imh = imh.ImagingHandler(key_handler=this_kh)
this_pph = pph.PostProcessHandler(key_handler=this_kh)

# Make any missing directories

this_kh.make_missing_directories(imaging=True, derived=True, postprocess=True, release=True)

##############################################################################
# Set up what we do this run
##############################################################################


# Set the configs (arrays), spectral products (lines), and targets to
# consider.

# Set the targets. Called with only () it will use all targets. The
# only= , just= , start= , stop= criteria allow one to build a smaller
# list. 

# Set the configs. Set both interf_configs and feather_configs just to
# determine which cubes will be processed. The only effect in this
# derive product calculation is to determine which cubes get fed into
# the calculation.

# Set the line products. Similarly, this just determines which cubes
# are fed in. Right now there's no derived product pipeline focused on
# continuum maps.

# ASIDE: In PHANGS-ALMA we ran a cheap parallelization by running
# several scripts with different start and stop values in parallel. If
# you are running a big batch of jobs you might consider scripting
# something similar.

# Note here that we need to set the targets, configs, and lines for
# *all three* relevant handlers - the VisHandler (uvh), ImagingHandler
# (imh), and PostprocessHandler (pph). The settings below will stage
# combined 12m+7m data sets (including staging C18O and continuum),
# image the CO 2-1 line from these, and then postprocess the CO 2-1
# cubes.

this_uvh.set_targets()
this_uvh.set_interf_configs(only=['12m'])
this_uvh.set_no_cont_products(False)
this_uvh.set_line_products(only=['co21'])

# e.g., could be to be more selective:
# this_uvh.set_targets(only=['ngc3489','ngc3599','ngc4476'])
# this_uvh.set_interf_configs(only=['12m+7m'])
# this_uvh.set_line_products(only=['co21'])

this_imh.set_targets()
this_imh.set_interf_configs(only=['12m'])
this_imh.set_no_cont_products(False)
this_imh.set_line_products(only=['co21'])

this_pph.set_targets()
this_pph.set_interf_configs()

# Use boolean flags to set the steps to be performed when the pipeline
# is called. See descriptions below (but only edit here).

if not os.path.exists(startdir+'/reduction/imaging/ngc5037/ngc5037_12m_co21.ms'):
    do_staging = True
else:
    do_staging = False

do_imaging = True
do_postprocess = False
do_stats = False

##############################################################################
# Run staging
##############################################################################

# "Stage" the visibility data. This involves copying the original
# calibrated measurement set, continuum subtracting (if requested),
# extraction of requested lines and continuum data, regridding and
# concatenation into a single measurement set. The overwrite=True flag
# is needed to ensure that previous runs can be overwritten.

if do_staging:
    this_uvh.loop_stage_uvdata(do_copy=True, do_contsub=True,
                               do_extract_line=True, do_extract_cont=True,
                               do_remove_staging=False, overwrite=False)

##############################################################################
# Step through imaging
##############################################################################

# Image the concatenated, regridded visibility data. The full loop
# involves applying any user-supplied clean mask, multiscale imaging,
# mask generation for the single scale clean, and single scale
# clean. The individual parts can be turned on or off with flags to
# the imaging loop call but this call does everything.

if do_imaging:
    #this_imh.loop_imaging(do_all=True)
    kwargs = {}
    kwargs['do_all'] = False
    kwargs['do_read_clean_mask'] = False
    kwargs['do_export_to_fits'] = True
    if not os.path.exists(startdir+'/reduction/imaging/ngc5037/ngc5037_12m_co21_dirty.image'):
        kwargs['do_dirty_image'] = True
        kwargs['do_export_to_fits'] = True
        kwargs['export_dirty'] = True
    else:
        kwargs['export_dirty'] = False
    if not os.path.exists(startdir+'/reduction/imaging/ngc5037/ngc5037_12m_co21_multiscale.image'):
        kwargs['do_multiscale_clean'] = True
        kwargs['do_export_to_fits'] = True
        kwargs['export_multiscale'] = True
    else:
        kwargs['do_revert_to_dirty'] = False
        kwargs['do_revert_to_multiscale'] = True
        kwargs['export_multiscale'] = False
    if not os.path.exists(startdir+'/reduction/imaging/ngc5037/ngc5037_12m_co21_singlescale.image'):
        kwargs['do_singlescale_mask'] = True
        kwargs['do_singlescale_clean'] = True
    else:
        kwargs['do_revert_to_dirty'] = False
        kwargs['do_revert_to_multiscale'] = False
        kwargs['do_revert_to_singlescale'] = True
    kwargs['overwrite'] = False
    print('---***---***---***---')
    print('this_imh.loop_imaging('+', '.join(['{}={!r}'.format(x, y) for x, y in zip(kwargs.keys(), kwargs.values())])+')')
    print('---***---***---***---')
    this_imh.loop_imaging(**kwargs)


##############################################################################
# Step through postprocessing
##############################################################################

# Postprocess the data in CASA after imaging. This involves primary
# beam correction, linear mosaicking, feathering, conversion to Kelvin
# units, and some downsampling to save space.

if do_postprocess:
    this_pph.loop_postprocess(do_prep=True, do_feather=True,
                              do_mosaic=True, do_cleanup=True)
