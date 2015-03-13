import logging
import os
import subprocess

import pylons.config as config

import ckan.common as common

log = logging.getLogger(__name__)
_ = common._


def generate_custom_css_path(css_dest_dir, css_filename_base, timestamp, relative_path=False):
    if relative_path:
        css_base_path = '/css/generated'
    else:
        css_base_path = config.get('hdx.css.basepath', None)
    css_filename = css_filename_base + '-' + timestamp + ".css"
    if css_base_path:
        # css_dir_path = css_base_path + css_dest_dir
        css_file_path = css_base_path + css_dest_dir + '/' + css_filename
        return css_file_path
    else:
        log.error('hdx.css.basepath must be set in config file')
        return None

class LessCompiler(object):

    def __init__(self, less, css_dest_dir, css_filename_base, timestamp='', translate_func=None):
        '''
       :param less: less code that needs to be compiled
       :type less: unicode
       :param css_dest_dir: folder in which to save the compiled CSS. This will be concatenated to 'hdx.css.basepath'
       :type css_dest_dir: string
       :param css_filename_base: name of the css file (WITHOUT .CSS) to be generated to which the timestamp will be concatenated
       :type css_filename_base: string
       :param timestamp: name of the css file to be generated to which the timestamp will be concatenated
       :type timestamp: string
       '''

        self.translate_func = _ if translate_func is None else translate_func


        self.timestamp = timestamp

        self.css_file_path = generate_custom_css_path(css_dest_dir, css_filename_base, timestamp)

        self.less_base_path = config.get('hdx.less.basepath', None)
        less_tmp_filename = css_filename_base + '-' + timestamp + ".less"
        self.less_tmp_filepath = self.less_base_path + '/tmp' + css_dest_dir + "/" + less_tmp_filename

        less_import = '@import "{}/organization/wfp/organization-wfp";'.format(self.less_base_path)
        self.less = less_import + less
        if not self.less_base_path:
            log.error('hdx.css.basepath must be set in config file')

    def compile_less(self):
        '''
        :return: dictionary with 'success' flag and 'message'
        '''
        if self.css_file_path and self.less_base_path:
            try:

                self._write_string_to_fs(self.less_tmp_filepath, self.less)

                # css = lesscpy.compile(StringIO.StringIO(self.less), minify=False)

                css = subprocess.check_output(['lessc', self.less_tmp_filepath], stderr=subprocess.STDOUT)

                self._write_string_to_fs(self.css_file_path, css)

                log.info('CSS file created: ' + self.css_file_path)

                return {
                    'success': True,
                    'message': self.translate_func('CSS compiled successfully.')
                }
            except Exception as e:
                message = e.output if hasattr(e, 'output') else e.message
                log.error(message)
                return {
                    'success': False,
                    'message': self.translate_func('Exception occurred while parsing the less file:') + message
                }

        else:
            return {
                'success': False,
                'message': self.translate_func('Path problem. Either "hdx.css.basepath" or "hdx.less.basepath" not set in ckan config.')
            }

    def _write_string_to_fs(self, filepath, contents):
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))
        with open(filepath, "w") as f:
            f.write(contents)

