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
from roachboard_readout import RoachReadout

update(OVST, current_track)
roach = RoachReadout('spectrum')

def getvalue(request, name, val_type):
    """ 
        Converts the value of the html form element 'name' into 'val_type'
    """
    try:
        return val_type(request.GET.get(name))
    except:
        return None

def return_message(request, tag, message):
    if tag == 'success':
        messages.success(request, message)
    elif tag == 'error':
        messages.error(request, message)
    else:
        messages.info(request, message)


def check_roach(request):
    ''' Checks if settings on the Roachboard Readout were done, applies it and starts the readout. 
    '''
    if request.GET.get('submit_start_readout') or request.GET.get('submit_start_power_readout'):
        if not roach.running:
            if request.GET.get('submit_start_readout'):
                roach.__init__('spectrum')    # Reinitialise to make sure to have default values
            if request.GET.get('submit_start_power_readout'):
                roach.__init__('power')
            bof = getvalue(request, 'select_bof', int)
            acc_len = getvalue(request, 'tbx_acc_len', eval)
            plot_min = getvalue(request, 'tbx_plot_min', int)
            plot_max = getvalue(request, 'tbx_plot_max', int)

            if bof != None:
                roach.bitstream = roach.boffiles[roach.mode][bof]
            if acc_len:
                roach.acc_len = acc_len
            try:    # Convert gain string to hex
                gain = int(request.GET.get('tbx_gain'), 16)
                if gain:
                    roach.gain = gain
            except:
                pass
            if plot_min:
                roach.plot_lims[0] = plot_min
            if plot_max:
                roach.plot_lims[1] = plot_max
            if request.GET.get('cbx_save_roach'):
                roach.save = True
                print 'Saving data'
            threading.Thread(target=roach.run).start()
            time.sleep(2)   # Give some time to let the server connect to the roachboard

    if request.GET.get('submit_stop_readout'):
        roach.running = False
        while roach.save:   # Wait until Data is saved
            time.sleep(1)
    return {'roach': {'running':    roach.running,
                      'mode':       roach.mode,
                      'boffiles':   roach.boffiles,
                      'boffile':    roach.bitstream,
                      'acc_len':    roach.acc_len,
                      'gain':       roach.gain,
                      'connected':  roach.fpga.is_connected() if roach.fpga else None,
                      'plot_min':   roach.plot_lims[0],
                      'plot_max':   roach.plot_lims[1],
                      'save_data':  roach.save
                      }
            }

@login_required()
def index(request):
    context = check_roach(request)
    return render(request, 'home/home.html', context)


@login_required()
def tracks(request):  # TODO
    '''
    This is the view function for /track. It checks if a form for a tracking mode was submitted and calls the corresponding 
    funciton. After that, the user gets redirected to /track
    The keys of the dictionaries must have the same name as the kwargs in ObservationMode of the telescope control
    program
    '''
    context = check_roach(request)
    context ['nbar'] = 'track'
    context['in_range'] = OVST.in_range
    context['update_time'] = OVST.update_time
    do_track = False
    current = current_track()
    if current:
        context['current_track'] = {
            'target':       current[0],
            'duration':     current[1],
            'startTime':    current[2],
            'mode':         current[3]
        }
    context['pending_tracks'] = pending_tracks()
    try:
        select = getvalue(request, 'select_target', str)
        if select:
            if select == 'target':
                target = getvalue(request, 'target', str)
            if select == 'radec':
                ra = getvalue(request, 'ra', str)
                dec = getvalue(request, 'dec', str)
                target = ('radec, %s, %s' % (ra, dec))
            if select == 'azel':
                az = getvalue(request, 'az', str)
                el = getvalue(request, 'el', str)
                target = ('azel, %s, %s' % (az, el))
            if select == 'gal':
                gal_long = getvalue(request, 'gal_long', float)
                gal_lat = getvalue(request, 'gal_lat', float)
                if gal_long == None:
                    gal_long = getvalue(request, 'gal_long', str)
                    gal_long = dms2dd(gal_long)
                if gal_lat == None:
                    gal_lat = getvalue(request, 'gal_lat', str)
                    gal_lat = dms2dd(gal_lat)
                target = ('gal, %s, %s' % (gal_long, gal_lat))
        duration = int(request.GET.get('duration'))
        startTime = str(request.GET.get('start_time'))
        if startTime == "":
            startTime = None
        do_track = True
    except:
        pass
    GoOff = None
    mode = None
    if request.GET.get('submit_track'):
        print 'tracking %s for %i minutes' % (target, duration)

    if request.GET.get('submit_cross'):
        az_cross = float(request.GET.get('az_cross'))
        el_cross = float(request.GET.get('el_cross'))
        GoOff = [az_cross, el_cross]
        print 'Doing Cross'

    if request.GET.get('submit_lissajous'):
        lissajous_dict = {  'az_frame': getvalue(request, 'az_frame_lissajous', float),
                            'el_frame': getvalue(request, 'el_frame_lissajous', float),
                            'omegaAz': getvalue(request, 'az_omega', float),
                            'omegaEl': getvalue(request, 'el_omega', float),
                            'phiAz': getvalue(request, 'az_phi', float),
                            'phiEl': getvalue(request, 'el_phi', float)
                            }
        mode = mapping('Lissajous', **lissajous_dict)

    if request.GET.get('submit_pong'):
        pong_dict = {   'az_frame':     getvalue(request, 'az_frame_pong', float),
                        'el_frame':     getvalue(request, 'el_frame_pong', float),
                        'startAz':      getvalue(request, 'az_start', float),
                        'startEl':      getvalue(request, 'el_start', float),
                        'startAngle':   getvalue(request, 'start_angle', float),
                        'velocity':     getvalue(request, 'velocity', float)
        }
        mode = mapping('Pong', **pong_dict)

    if request.GET.get('submit_raster'):
        raster_dict ={
            'az_frame':             getvalue(request, 'az_frame_raster', float),
            'el_frame':             getvalue(request, 'el_frame_raster', float),
            'rasterLines':          getvalue(request, 'rasterLines', int),
            'firstAz':              getvalue(request, 'first', bool),
            'observationDuration':  duration
            }
        mode = mapping('Raster', **raster_dict)

    if do_track:
        if mode:
            tag, message = track(target, duration, GoOff=GoOff, startTime=startTime, mode=mode)
            return_message(request, tag, message)
        else:
            tag, message = track(target, duration, GoOff=GoOff, startTime=startTime)
            return_message(request, tag, message)
        return redirect('/track')

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

    if request.GET.get('movegal'):
        gal_long = getvalue(request, 'gal_long', str)
        gal_lat = getvalue(request, 'gal_lat', str)
        message = move_galactic(gal_long, gal_lat)
        return redirect('/pointing')

    if request.GET.get('home'):
        home()
        print 'moving home'
        return redirect('/pointing')
    if request.GET.get('safety'):
        safety()
        return redirect('/pointing')
    if request.GET.get('quit'):
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
        choose_telescopes(antennas)
        names = [ant.name for ant in active_telescopes()]
        messages.success(request, 'Telescopes chosen: %s' % names)
        return redirect('/tel_settings')

    if request.GET.get('submit_clear_fault'):
        rollover = []
        for i, ant in enumerate(OVST.antennaList):
            rollover.append(int(request.GET.get('rollover%i'%i)))
        clear_fault(rollover)

    if request.GET.get('submit_halt'):
        halt_telescopes()
        if OVST.halt:
            messages.success(request, 'Telescopes halted!')

    if request.GET.get('submit_clear_halt'):
        clear_halt()
        if not OVST.halt:
            messages.success(request, 'Telescopes halt cleared!')

    if request.GET.get('modbus_connection'):
        mod = getvalue(request, 'modbus_connection', str)
        if mod == 'open':
            OVST.openModbusConnections()
        else:
            OVST.closeAllModbusConnections()

    context['antennas'] = [ant.name for ant in OVST.antennaList]
    context['active_antennas'] = [ant.name for ant in OVST.active_antennas]
    context['halt'] = OVST.halt
    return render(request, 'home/tel_settings.html', context)

def lines(request):
    return render(request, 'home/lines.html')

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


@login_required()
def updated_content(request):
    return render(request, 'home/updated_content.html')


@login_required()
def roach_plot(request):
    return render(request, 'home/roach_plot.html')
