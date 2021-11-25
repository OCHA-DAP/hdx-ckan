# import logging
# import subprocess
# import urllib
#
# from pylons import config
#
# log = logging.getLogger(__name__)
#
# class ScreenshotCreator(object):
#     def __init__(self, url, output_file, selector, renderdelay=None, waitcapturedelay=None, http_timeout=None, viewportsize=None,
#                  mogrify=False, resize=None, crop=None):
#
#         self.url = url
#         self.output_file = output_file
#
#         self.selector = selector
#         self.renderdelay = renderdelay
#         self.waitcapturedelay = waitcapturedelay
#         self.http_timeout = http_timeout
#         self.viewportsize = viewportsize
#         self.mogrify = mogrify
#         self.resize = resize
#         self.crop = crop
#
#         self.url_params = ''
#         striped_selector = selector.strip('"').strip()
#         if striped_selector and (len(striped_selector) > 0):
#             self.url_params += 'selector=' + urllib.quote_plus(striped_selector)+'&'
#
#
#
#         if renderdelay:
#             self.url_params += 'timeout=' + urllib.quote_plus(str(renderdelay)) + '&'
#
#         # if waitcapturedelay:
#         #     self.params_list.extend(('-W', str(waitcapturedelay)))
#         #
#         # if http_timeout:
#         #     self.params_list.extend(('-T', str(http_timeout)))
#         #
#
#         if mogrify:
#             if resize:
#                 self.url_params += 'resize=' + urllib.quote_plus(str(resize)) + '&'
#
#             if crop:
#                 self.url_params += 'crop=' + urllib.quote_plus(str(crop)) + '&'
#
#
#     def execute(self):
#
#         try:
#             query = self.url_params + 'url=' + self.url
#             snap_service_url = config.get('hdx.snap_service.url')
#             url = snap_service_url + '/png?' + query
#
#             log.info('Url:' + url + ' File:' + self.output_file)
#             urllib.urlretrieve(url, self.output_file)
#             log.warn('File:' + self.output_file)
#
#             return True
#         except subprocess.CalledProcessError, e:
#             log.warn(str(e))
#
#         return False
#
#
#
