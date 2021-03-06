from app import migrate, app
from flask_script import Manager
from flask_migrate import MigrateCommand

if __name__ == '__main__':
	#command
	manager = Manager(app)
	manager.add_command('db', MigrateCommand)
	manager.run()