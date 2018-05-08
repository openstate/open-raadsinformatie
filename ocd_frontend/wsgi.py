import os.path

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

import rest

application = DispatcherMiddleware(rest.create_app(), {
    '/v1': rest.create_app()
})

# For testing purposes, add a route that serves static files from a directory.
# DO NOT USE IN PRODUCTION. Serve static files through your webserver instead.
if application.app.config.get('DEBUG', False):
    from flask import send_from_directory


    @application.app.route('/data/<path:filename>')
    def download_dump(filename):
        collection_name = '_'.join(filename.split('_')[:2])
        base_dir = os.path.join(application.app.config.get('DUMPS_DIR'),
                                collection_name)
        return send_from_directory(base_dir, filename, as_attachment=True)


    @application.app.route('/media/<path:filename>')
    def serve_media(filename):
        base_dir = os.path.join(application.app.config.get('THUMBNAILS_DIR'),
                                os.path.dirname(filename))
        return send_from_directory(base_dir, os.path.basename(filename))

if __name__ == '__main__':
    run_simple('0.0.0.0', 5000, application, processes=8, use_reloader=True, use_debugger=True)
