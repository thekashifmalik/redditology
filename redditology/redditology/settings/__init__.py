# Django settings for redditology project.
import os

# Set up site root constant
SITE_ROOT = os.path.dirname(os.path.realpath(__file__) + '/../../')

# Method to return absolute paths from relative paths
def absolute_path(relative_root_path, target_file):
	return os.path.join(relative_root_path, target_file)

# Import corresponding environment settings.
try:
	app_env = os.environ["REDDITOLOGY_ENV"]
	if app_env == "production":
		# Import production settings
		from redditology.settings.production import *
	elif app_env == "development":
		# Import development settings
		from redditology.settings.development import *
except KeyError, e:
	# import local settings
	from redditology.settings.local import *

# Set various variables.
TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT - trailing slash.
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to using collectstatic.
STATIC_ROOT = ''

# Additional locations of static files - absolute paths
STATICFILES_DIRS = (
	absolute_path(SITE_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.Loader',
	'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	# Uncomment the next line for simple clickjacking protection:
	# 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'redditology.urls'

# WSGI server for debug server.
WSGI_APPLICATION = 'redditology.wsgi.application'

# Templates location - absolute path
TEMPLATE_DIRS = (
	absolute_path(SITE_ROOT, 'templates'),
)

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'suit',
	'django.contrib.admin',
	'django.contrib.admindocs',
	'south',
	'djcelery',

	'fetcher',
	'posts',
)

# Set up simple master logger
LOGGING = {
	'version': 1,
	'disable_existing_loggers': True,
	'formatters': {
		'verbose': {
			'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
		},
		'simple': {
			'format': '%(levelname)s %(message)s'
		},
	},
	'handlers': {
		'console':{
			'level': 'INFO',
			'class': 'logging.StreamHandler',
			'formatter': 'simple'
		},
	},
	'loggers': {
		'': {
			'handlers': ['console'],
			'level': 'INFO',
			'propagate': True,
		},
	}
}

# Celery settings
import djcelery
djcelery.setup_loader()


from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP

TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
)

SUIT_CONFIG = {
    'ADMIN_NAME': 'Redditology'
}