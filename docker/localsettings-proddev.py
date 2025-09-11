DEPLOY_MODE = 'proddev'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp4dev'
EMAIL_PORT = 2525
EMAIL_USE_SSL = False

DB_CONNECTION = {'HOST': 'mysql'}
MEMCACHED_HOST = 'memcached'
RABBITMQ_HOSTPORT = 'rabbitmq:5672'
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'courselib.elasticsearch_backend.CustomElasticsearchSearchEngine',
        'URL': 'http://elasticsearch:9200/',
        'INDEX_NAME': 'haystack',
        'TIMEOUT': 60,
    },
}

MOSS_DISTRIBUTION_PATH = '/moss'
DB_BACKUP_DIR = '/db_backups'
SUBMISSION_PATH = '/submissions'
