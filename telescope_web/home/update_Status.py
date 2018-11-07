import threading
import os
import time


def update(OVST):
    def html_div(text, div_class, color):
        return ("<div class='%s' style='color:%s'>%s</div>" % (div_class, color, text))

    def update_thread():
        while True:
            status_list = [sensor.valueToString for sensor in OVST.sensorUpdaterList[:6]]
            status_codes = [sensor.read()[1] for sensor in OVST.sensorUpdaterList[:6]]
            pos = OVST.get_pos()
            div_list = []
            for i in range(len(OVST.antennaList)):
                div_list.append(html_div('%.2f' % pos[i][1], 'az%i'%i, '#11d419'))
                div_list.append(html_div('%.2f' % pos[i][2], 'el%i'%i, '#11d419'))
            for n, status in enumerate(status_list):
                statuscode = status_codes[n]
                if statuscode == 0:
                    color = "white"
                elif statuscode == 1:
                    color = "#11d419"
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
                div_list.append(html_div(status, 'status%i'%n, color))
            with file(os.path.dirname(__file__)+'/templates/updated_content.html', 'w') as up:
                for div in div_list:
                    up.write(div)
            time.sleep(0.5)


    th = threading.Thread(target=update_thread)
    th.start()


