import ckan.plugins as p
import ckanext.hdx_users.model as umodel

class ValidationCommand(p.toolkit.CkanCommand):
	'''
	Usage:
		paster users [initdb]
		- Creates the necessary tables in the database
	'''
	summary = __doc__.split('\n')[0]
	usage = __doc__

	def __init__(self,name):
		super(ValidationCommand, self).__init__(name)

	def command(self):
		if not self.args or self.args[0] in ['-h', '--help', 'help'] or not len(self.args) in [1,2]:
			print self.usage
			return

		cmd = self.args[0]
		self._load_config()
		if cmd == 'initdb':
			print 'Initializing Database...'
			self.initdb()
		elif cmd == 'cleandb':
			self.cleandb()
		else:
			print 'Error: command "{0}" not recognized'.format(cmd)
			print self.usage

	def initdb(self):
		'''
		Create the tables defined by model
		'''
		umodel.setup()

	def cleandb(self):
		'''
		Delete tables defined by model
		'''
		umodel.delete_tables()