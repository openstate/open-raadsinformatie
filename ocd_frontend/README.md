# Frontend for Open Raadsinformatie API

Although it is called `frontend` it is only serving files using `Flask`.

## nginx

Flask is configured using `USE_X_SENDFILE = True`. 
When generating the reponse for a file request, the `X-Accel-Redirect` header is set, prepended by `/file_repository`.
`nginx` must be configured to deal with this so add the following `location` block for the `openraadsinformatie.nl` server:

```
location /file_repository {
  internal;
  alias /home/projects/html/ori/data;
} 
```

