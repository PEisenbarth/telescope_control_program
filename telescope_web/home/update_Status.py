import threading
import os
import time

def update(OVST, current_track):
    """
    Writes the telescopes' position data and the PLC states continuously into a html file which will be accessed by
    the website
    """
    def html_div(text, div_class, color):
        return ("<div class='%s' style='color:%s'>%s</div>" % (div_class, color, text))

    def update_thread():
        while True:
            status_list = [sensor.valueToString for sensor in OVST.sensorUpdaterList[:6]]
            status_codes = [sensor.read()[1] for sensor in OVST.sensorUpdaterList]
            # If no sensor shows an error, release the software error to
            if OVST.error and all(i == 1 for i in status_codes):
                OVST.error = False

            pos = OVST.get_pos()
            div_list = []
            for i in range(len(OVST.antennaList)):
                current = current_track()
                # Get status colors for positions
                az_color = get_status_color(status_codes[6+2*i])
                el_color = get_status_color(status_codes[7+2*i])
                if current:
                    # If there is currently a track, calculate the deviation from the target
                    target_pos = OVST.get_target_pos(current[0], check=False)
                    az_off = target_pos[i][0] - pos[i][1]
                    el_off = target_pos[i][1] - pos[i][2]
                    div_list.append(html_div('%.2f %+.2f' % (pos[i][1], az_off), 'az%i'%i, az_color))
                    div_list.append(html_div('%.2f %+.2f' % (pos[i][2], el_off), 'el%i'%i, el_color))
                else:
                    div_list.append(html_div('%.2f' % pos[i][1], 'az%i'%i, az_color))
                    div_list.append(html_div('%.2f' % pos[i][2], 'el%i'%i, el_color))

            # Iterate through the status and return a div for each
            for n, status in enumerate(status_list):
                statuscode = status_codes[n]
                color = get_status_color(statuscode)
                div_list.append(html_div(status, 'status%i'%n, color))
            with file(os.path.dirname(__file__)+'/templates/home/updated_content.html', 'w') as up:
                for div in div_list:
                    up.write(div)
            time.sleep(0.5)

    def get_status_color(statuscode):
        # Apply a meaningful color to the current status
        if statuscode == 0:
            color = "white"
        elif statuscode == 1:
            color = "limegreen"
        elif statuscode == 2:
            color = "yellow"
        elif statuscode == 3:
            color = "red"
        elif statuscode == 4:
            color = "purple"
        elif statuscode == 5:
            color = "teal"
        elif statuscode == 6:
            color = "blue"
        else:
            color = 'white'

        return color

    th = threading.Thread(target=update_thread)
    th.start()


