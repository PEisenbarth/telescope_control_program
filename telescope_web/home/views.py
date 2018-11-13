# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from telescopecontrol.check_target import *
from telescopecontrol.commands import *
# from .check_target import *
# from .commands import *
from update_Status import update
from Monitor_hr4 import RoachReadout

update(OVST)
roach = RoachReadout()


def getvalue(request, name, val_type):
    """ 
        Converts the value of the html form element 'name' into 'val_type'
    """
    try:
        return val_type(request.GET.get(name))
    except:
        return None

def check_roach(request):
    '''Checks if settings on the Roachboard Readout were done'''
    if request.GET.get('submit_start_readout'):
        if not roach.running:
            threading.Thread(target=roach.run).start()
    if request.GET.get('submit_stop_readout'):
        roach.running = False
        roach.__init__()
    return {'roach': {'running': roach.running}}

@login_required()
def index(request):
    context = check_roach(request)
    return render(request, 'home/home.html', context)


@login_required()
def tracks(request): # TODO
    '''
    This is the view function for /track. It checks if a form for a tracking mode was submitted and calls the corresponding 
    funciton. After that, the user gets redirected to /track
    The keys of the dictionaries must have the same name as the kwargs in ObservationMode of the telescope control
    program
    '''
    context = check_roach(request)
    context ['nbar'] = 'track'
    current = current_track()
    context['in_range'] = OVST.in_range
    context['update_time'] = OVST.update_time

    if current:
        context['current_track'] = {
            'target':       current[0],
            'duration':     current[1],
            'startTime':    current[2],
            'mode':         current[3]
        }
    context['pending_tracks'] = pending_tracks()        # FIXME: Change ObservationMode object to ObsevationMode name
    if context['pending_tracks']:
        # Change the 'ObservationMode' object to the name of the mode so that the name gets displayed on the website
        # for i, pending in enumerate(context['pending_tracks']):
        #     context['pending_tracks'][i][5] = pending[5].mode
        pass
    try:
        target = str(request.GET.get('target'))
        duration = int(request.GET.get('duration'))
        startTime = str(request.GET.get('start_time'))
        if startTime == "":
            startTime = None
    except:
        pass
    if request.GET.get('submit_track'):

        track(target, duration, startTime)
        print 'tracking %s for %i minutes' % (target, duration)


        return redirect('/track')

    if request.GET.get('submit_cross'):
        az_cross = float(request.GET.get('az_cross'))
        el_cross = float(request.GET.get('el_cross'))
        track(target, duration, GoOff=(az_cross, el_cross), startTime=startTime)
        print 'Doing Cross'
        return redirect('/track')

    if request.GET.get('submit_lissajous'):
        lissajous_dict = {  'az_frame': getvalue(request, 'az_frame_lissajous', float),
                            'el_frame': getvalue(request, 'el_frame_lissajous', float),
                            'omegaAz': getvalue(request, 'az_omega', float),
                            'omegaEl': getvalue(request, 'el_omega', float),
                            'phiAz': getvalue(request, 'az_phi', float),
                            'phiEl': getvalue(request, 'el_phi', float)
                            }

        mode = mapping('Lissajous', **lissajous_dict)
        track(target, duration, startTime=startTime, mode=mode)
        return redirect('/track')

    if request.GET.get('submit_pong'):
        pong_dict = {   'az_frame':     getvalue(request, 'az_frame_pong', float),
                        'el_frame':     getvalue(request, 'el_frame_pong', float),
                        'startAz':      getvalue(request, 'az_start', float),
                        'startEl':      getvalue(request, 'el_start', float),
                        'startAngle':   getvalue(request, 'start_angle', float),
                        'velocity':     getvalue(request, 'velocity', float)
        }
        mode = mapping('Pong', **pong_dict)
        track(target, duration, startTime=startTime, mode=mode)
        return redirect('/track')

    if request.GET.get('submit_raster'):
        raster_dict ={
            'az_frame':             getvalue(request, 'az_frame_raster', float),
            'el_frame':             getvalue(request, 'el_frame_raster', float),
            'rasterLines':          getvalue(request, 'rasterLines', int),
            'firstAz':              getvalue(request, 'first', bool),
            'observationDuration':  duration
            }
        mode = mapping('Raster', **raster_dict)
        track(target, duration, startTime=startTime, mode=mode)

    if request.GET.get('stop_all_tracks'):
        stop_all_tracks()
        return redirect('/track')

    del_track = request.GET.get('del_track')
    if del_track:
        if del_track == 'current':
            stop_track()
            continue_track()
        else:
            try:
                delete_track(int(del_track))
            except:
                pass
        return redirect('/track')
    if request.GET.get('check_target'):
        target = str(request.GET.get('check_target_tbx'))
        try:
            azel = check_target(OVST, target, check=False)
            azel = [[round(item[0], 4), round(item[1], 4)] for item in azel]
            context.update({'target_ok': target,
                            'azel': azel})
        except ValueError:
            context.update({'target_error': '%s is not in Catalogue' % target})
        except LookupError:
            context.update({'target_error': '%s is not in range' % target})
        return render(request, 'home/track.html', context)
    return render(request, 'home/track.html', context)


@login_required()
def pointing(request):
    """
    View for the /pointing site
    """
    context = check_roach(request)
    context['nbar'] = 'pointing'
    if request.GET.get('moveazel'):
        try:
            az = float(request.GET.get('az'))
            el = float(request.GET.get('el'))
            move(az, el)
            print 'moving to %f and %f' % (az, el)
        except:
            print 'Please insert an integer'
        return redirect('/pointing')
    if request.GET.get('moveradec'):
        try:
            ra = str(request.GET.get('ra'))
            dec = str(request.GET.get('dec'))
            move(ra, dec)
            print 'moving to %s and %s' % (ra, dec)
        except:
            print 'Please insert an integer'
        return redirect('/pointing')

    if request.GET.get('movetarget'):
        try:
            target = str(request.GET.get('target'))
            move(target)
            print 'moving to %s' % target
        except:
            print 'Please insert an integer'
        return redirect('/pointing')


    if (request.GET.get('home')):
        home()
        print 'moving home'
        return redirect('/pointing')
    if (request.GET.get('quit')):
        quit_tel()
        return redirect('/pointing')
    return render(request, 'home/pointing.html', context)


@login_required()
def tel_settings(request):
    context = check_roach(request)
    context.update({'nbar': 'tel_settings',
                    'halt':  OVST.halt})
    if request.GET.get('submit_choose_antennas'):
        antennas = []
        for i, ant in enumerate(OVST.antennaList):
            if request.GET.get('antenna%i'%i) == ant.name:
                antennas.append(ant)
        if len(antennas) == 0:
            choose_telescopes()
        print 'antennas chosen:'
        print antennas
        choose_telescopes(antennas)
        return redirect('/tel_settings')

    if request.GET.get('submit_clear_fault'):
        rollover = []
        for i, ant in enumerate(OVST.antennaList):
            rollover.append(int(request.GET.get('rollover%i'%i)))
        clear_fault(rollover)

    if request.GET.get('submit_halt'):
        halt_telescopes()

    if request.GET.get('submit_clear_halt'):
        clear_halt()

    context['antennas'] = [ant.name for ant in OVST.antennaList]
    context['active_antennas'] = [ant.name for ant in OVST.active_antennas]
    context['halt'] = OVST.halt
    return render(request, 'home/tel_settings.html', context)



@login_required()
def change_password(request):
    """Allows users to change their password on their own"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request,
                             mark_safe("Your password was updated successfully! Go back to <a href='/'>Home</a>"))
            return redirect('change_password')
        else:
            messages.error(request, 'There was an error changing the password')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/change_password.html', {
        'form': form
    })


def updated_content(request):
    return render(request, 'home/updated_content.html')

def roach_plot(request):
    return render(request, 'home/roach_plot.svg')