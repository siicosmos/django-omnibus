import logging

from django.core.management.base import BaseCommand

try:
    from django.utils.module_loading import import_string
except ImportError:
    from django.utils.module_loading import import_by_path as import_string

from tornado import ioloop, httpserver
from sys import exit

from ...pubsub import PubSub
from ...settings import (
    SERVER_PORT, AUTHENTICATOR_FACTORY, CONNECTION_FACTORY, WEBAPP_FACTORY,
    DIRECTOR_ENABLED, FORWARDER_ENABLED, SERVER_SSL, SERVER_SSL_KEY, SERVER_SSL_CERT)


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Initialize pubsub helper.
        pubsub = PubSub()

        if DIRECTOR_ENABLED:
            logger.info('Starting director.')
            pubsub.init_director()

        if FORWARDER_ENABLED:
            logger.info('Starting forwarder.')
            pubsub.init_forwarder()

        # Get factories for connection and tornado webapp.
        authenticator_factory = import_string(AUTHENTICATOR_FACTORY)
        connection_factory = import_string(CONNECTION_FACTORY)
        webapp_factory = import_string(WEBAPP_FACTORY)

        # Create app and listen on SEVER_PORT
        app = webapp_factory(
            connection_factory(authenticator_factory(), pubsub))

        if SERVER_SSL:
            if SERVER_SSL_KEY != '' and SERVER_SSL_CERT != '':
                options = {"certfile": SERVER_SSL_CERT, "keyfile": SERVER_SSL_KEY}

                http_server = httpserver.HTTPServer(app, ssl_options=options)
                http_server.listen(SERVER_PORT)
            else:
                exit('No key/certificate configured for SSL support')
        else:
            app.listen(SERVER_PORT)

        # Go, run!
        loop = ioloop.IOLoop().instance()
        try:
            logger.info('Starting omnibusd.')
            loop.start()
        except KeyboardInterrupt:
            logger.info('Received KeyboardInterrup, stopping omnibusd.')
            loop.stop()
