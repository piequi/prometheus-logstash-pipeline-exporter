# Prometheus Logstash Pipelines Exporter

This prometheus exporter exposes Logstash pipelines metrics only. \
It does not expose JVM nor OS metrics provided by Logstash.

This exporter supports Logstash 6.x and 7.x

If logstash is unavailable, it will simply log an error when scraping. This
makes the exporter survive temporary Logstash unavailability.

## Usage
```
usage: logstash-pipeline-exporter.py [-h] [-d] [logstash_endpoint] [web_listen_address]

positional arguments:
  logstash_endpoint   logstash's endpoint (default: http://localhost:9600)
  web_listen_address  exporter binding address and port (default: 0.0.0.0:9649)

optional arguments:
  -h, --help          show this help message and exit
  -d, --debug         set debug mode (default: False)
```

## Plugin IDs
Logstash automatically generates IDs for the plugins you use in your pipelines,
like `7a5abdf3-b2af-40d6-a668-27a0531aaf88`.

In order to differentiate them easily and have meaningful labels, use the `id`
setting :
```logstash
mutate {
  id      => "mutate_replace_foo_bar"
  replace => { "foo" => "bar" }
}
```
> See https://www.elastic.co/guide/en/logstash/current/plugins-filters-mutate.html#plugins-filters-mutate-id

This `id` setting is available for all plugins.

## Docker
*TODO*


## Requirements
* Python 3
*
