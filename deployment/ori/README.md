# Kubernetes
In order to easily manage docker containers on Google Cloud Platform or Amazon AWS we use Kubernetes.
The best way to manage kubernetes yaml files is by using [Helm](https://helm.sh/) which can be downloaded [here](https://docs.helm.sh/using_helm#install-helm).

```bash
# Staging configuration
$ helm install . --namespace=staging --set publicIp=<external-ip>
```

```bash
# Production configuration
$ helm install . --namespace=production --values values-production.yaml --set publicIp=<external-ip>
```

```bash
# Upgrade release
$ helm list
$ helm upgrade <release> .
```