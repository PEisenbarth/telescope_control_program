# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, redirect
# from telescopecontrol.commands import *
# from telescopecontrol.check_target import *
from .check_target import *
from .commands import *
from update_Status import update
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# TODO: Implement Telescope Settings
# update(OVST)

def index(request):
    return render(request, 'home.html')


def getvalue(request, name, val_type):
    # Converts the value of the html form element 'name' into 'val_type'
    try:
        return val_type(request.GET.get(name))
    except:
        return None

#@login_required(login_url='/login')
def track(request): # TODO
    '''
    This is the view function for /track. It checks if a form for a tracking mode was submitted and calls the corresponding 
    funciton. After that, the user gets redirected to /track
    The keys of the dictionaries must have the same name as the kwargs in ObservationMode of the telescope control
    program
    '''
    context = {'nbar': 'track'}
    current = current_track()
    if current:
        context['current_track'] = {
            'target':       current[0],
            'duration':     current[1],
            'startTime':    current[2],
            'mode':         current[3]
        }
    context['pending_tracks'] = pending_tracks()
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
        try:
            print 'tracking %s for %i minutes' % (target, duration)
            track(target, duration, startTime)
        except:
            pass
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
    print del_track
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
            azel = check_target(OVST, target)
            azel = [[round(item[0], 4), round(item[1], 4)] for item in azel]
            context.update({'target_ok': [target],
                       'azel': azel,
                       })
        except ValueError:
            context.update({'target_error': '%s not in Catalogue' % target})
        except LookupError:
            context.update({'target_error': '%s not in range' % target})
        return render(request, 'track.html', context)
    if request.GET.get('del_tracks'):
        print request.GET.get('del_tracks')
    return render(request, 'track.html', context)


def pointing(request):
    '''
    View for the /pointing site
    '''
    context = {'nbar': 'pointing'}
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
    return render(request, 'pointing.html', context)


def tel_settings(request):
    context = {'nbar': 'tel_settings',
               'halt':  OVST.halt}
    if request.GET.get('submit_choose_antennas'):
        antennas = []
        for i, ant in enumerate(OVST.antennaList):
            if request.GET.get('antenna%i'%i) == ant.name:
                antennas.append(ant)
        print 'antennas chosen:'
        print antennas
        choose_telescopes(antennas)
        return redirect('/tel_settings')

    if request.GET.get('submit_clear_fault'):
        rollover = []
        for i, ant in enumerate(OVST.antennaList):
            rollover.append(request.GET.get('rollover%i'%i))
        clear_fault()

    context['antennas'] = [ant.name for ant in OVST.antennaList]
    context['active_antennas'] = [ant.name for ant in OVST.active_antennas]
    return render(request, 'tel_settings.html', context)


def updated_content(request):
    return render(request, 'updated_content.html')



