import subprocess
import logging

log = logging.getLogger(__name__)

class ScreenshotCreator(object):
    def __init__(self, url, output_file, selector, renderdelay=None, waitcapturedelay=None, http_timeout=None, viewportsize=None,
                 mogrify=False, resize=None, crop=None):

        self.params_list = [
            'capturejs', '-l',
            '-u', url,
            '-o', output_file,
            '-s', selector
        ]

        if renderdelay:
            self.params_list.extend(('-R', str(renderdelay)))

        if waitcapturedelay:
            self.params_list.extend(('-W', str(waitcapturedelay)))

        if http_timeout:
            self.params_list.extend(('-T', str(http_timeout)))

        if viewportsize:
            self.params_list.extend(('-V', str(viewportsize)))

        if mogrify:
            self.params_list.extend((';', 'mogrify'))

            if resize:
                self.params_list.extend(('-resize', str(resize)))

            if crop:
                self.params_list.extend(('-crop', str(crop)))

            self.params_list.append(output_file)

    def execute(self):
        command = ' '.join(self.params_list)
        log.info("Creating screenshot: {}".format(command))
        try:
            subprocess.Popen(command, shell=True)
            # output = subprocess.check_output(self.params_list, stderr=subprocess.STDOUT)
            # log.warn('Capturejs output: ' + output)
            return True
        except subprocess.CalledProcessError, e:
            log.warn(str(e))

        return False



