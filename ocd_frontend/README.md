# Frontend for Open Raadsinformatie API

Although it is called `frontend` it is only serving files using `Flask`.

## nginx

Flask is configured using `USE_X_SENDFILE = True`. 
When generating the reponse for a file request, the `X-Accel-Redirect` header is set, prepended by `/file_repository`.
`nginx-load-balancer` must be configured to deal with this so add the following `location` block for the `openraadsinformatie.nl` server:

```
location /file_repository {
  internal;
  alias /data;
} 
```

Add the following location block to intercept the `/resolve` links (which will yield to `/file_repository` above):

```
location /v1/resolve/ { try_files $uri @app; }
location @app {
    include uwsgi_params;
    uwsgi_pass ori_frontend_1:5000;
    uwsgi_read_timeout 1200;
}
```

For this to work, add the /data directory as a volume in `nginx-load-balancer/docker/docker-compose.yml`:

```
volumes:
  - ...
  - /data:/data
```
