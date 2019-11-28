#!/usr/bin/env python3
import argparse
import logging
import sys
import time
import requests

from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY


class LogstashPipelineCollector(object):

    def __init__(self, target):
        self._target = target.rstrip("/")

    def collect(self):

        # The metrics we want to export.
        metrics = {
            'events_metrics': {
                'duration':
                    GaugeMetricFamily('logstash_pipeline_events_processing_duration_seconds_total',
                                      'Logstash pipeline events processing total time',
                                      labels=["pipeline_id"]),
                'in':
                    GaugeMetricFamily('logstash_pipeline_events_processing_in_count',
                                      'Logstash pipeline incoming events',
                                      labels=["pipeline_id"]),
                'out':
                    GaugeMetricFamily('logstash_pipeline_events_processing_out_count',
                                      'Logstash pipeline outgoing events',
                                      labels=["pipeline_id"]),
                'filtered':
                    GaugeMetricFamily('logstash_pipeline_events_processing_filtered_count',
                                      'Logstash pipeline filtered events',
                                      labels=["pipeline_id"]),
                'queue_push_duration':
                    GaugeMetricFamily('logstash_pipeline_events_processing_queue_push_duration_seconds_total',
                                      'Logstash pipeline events queue push total time',
                                      labels=["pipeline_id"])
            },
            'plugins_inputs_metrics': {
                'out':
                    GaugeMetricFamily('logstash_pipeline_plugins_inputs_out_count',
                                      'Logstash pipeline input plugins outgoing events',
                                      labels=["pipeline_id", "plugin_name", "plugin_id"]),
                'queue_push_duration':
                    GaugeMetricFamily('logstash_pipeline_plugins_inputs_queue_push_duration_seconds_total',
                                      'Logstash pipeline input plugins queue push total time',
                                      labels=["pipeline_id", "plugin_name", "plugin_id"])
            },
            'plugins_filters_metrics': {
                'in':
                    GaugeMetricFamily('logstash_pipeline_plugins_filters_in_count',
                                      'Logstash pipeline filters plugins incoming events',
                                      labels=["pipeline_id", "plugin_name", "plugin_id"]),
                'out':
                    GaugeMetricFamily('logstash_pipeline_plugins_filters_out_count',
                                      'Logstash pipeline filters plugins outgoing events',
                                      labels=["pipeline_id", "plugin_name", "plugin_id"]),
                'duration':
                    GaugeMetricFamily('logstash_pipeline_plugins_filters_duration_seconds_total',
                                      'Logstash pipeline filters plugins total processing time',
                                      labels=["pipeline_id", "plugin_name", "plugin_id"]),
                'grok_matches':
                    GaugeMetricFamily('logstash_pipeline_plugins_filters_grok_matches_count',
                                      'Logstash pipeline grok filter plugins matches',
                                      labels=["pipeline_id", "plugin_id"]),
                'grok_failures':
                    GaugeMetricFamily('logstash_pipeline_plugins_filters_grok_failures_count',
                                      'Logstash pipeline grok filter plugins failures',
                                      labels=["pipeline_id", "plugin_id"])
            },
            'plugins_outputs_metrics': {
                'in':
                    GaugeMetricFamily('logstash_pipeline_plugins_outputs_in_count',
                                      'Logstash pipeline outputs plugins incoming events',
                                      labels=["pipeline_id", "plugin_name", "plugin_id"]),
                'out':
                    GaugeMetricFamily('logstash_pipeline_plugins_outputs_out_count',
                                      'Logstash pipeline outputs plugins outgoing events',
                                      labels=["pipeline_id", "plugin_name", "plugin_id"]),
                'duration':
                    GaugeMetricFamily('logstash_pipeline_plugins_outputs_duration_seconds_total',
                                      'Logstash pipeline outputs plugins total processing time',
                                      labels=["pipeline_id", "plugin_name", "plugin_id"])
            }
        }

        try:
            result = requests.get(self._target + "/_node/stats").json()
            logging.debug("Logstash's response: %s", result)
        except ValueError as ve:
            logging.error("Error decoding logstash response: %s", ve)
        except requests.exceptions.ConnectionError as ce:
            logging.error("Error connecting to logstash: %s", ce)
        else:

            if result['pipelines']:
                for pipeline_id in result['pipelines']:

                    # grab events metrics
                    events = result['pipelines'][pipeline_id]['events']
                    metrics['events_metrics']['duration'] \
                        .add_metric([pipeline_id], events['duration_in_millis'] / 1000.0)
                    metrics['events_metrics']['in'] \
                        .add_metric([pipeline_id], events['in'])
                    metrics['events_metrics']['out'] \
                        .add_metric([pipeline_id], events['out'])
                    metrics['events_metrics']['filtered'] \
                        .add_metric([pipeline_id], events['filtered'])
                    metrics['events_metrics']['queue_push_duration'] \
                        .add_metric([pipeline_id], events['queue_push_duration_in_millis'] / 1000.0)

                    # grab input plugins metrics
                    for input_plugin in result['pipelines'][pipeline_id]['plugins']['inputs']:
                        plugin_name = input_plugin['name']
                        plugin_id = input_plugin['id']
                        metrics['plugins_inputs_metrics']['out'] \
                            .add_metric([pipeline_id, plugin_name, plugin_id],
                                        input_plugin['events']['out'])
                        metrics['plugins_inputs_metrics']['queue_push_duration'] \
                            .add_metric([pipeline_id, plugin_name, plugin_id],
                                        input_plugin['events']['queue_push_duration_in_millis'] / 1000.0)

                    # grab filters plugins metrics
                    for filter_plugin in result['pipelines'][pipeline_id]['plugins']['filters']:
                        plugin_name = filter_plugin['name']
                        plugin_id = filter_plugin['id']
                        metrics['plugins_filters_metrics']['in'] \
                            .add_metric([pipeline_id, plugin_name, plugin_id],
                                        filter_plugin['events']['in'])
                        metrics['plugins_filters_metrics']['out'] \
                            .add_metric([pipeline_id, plugin_name, plugin_id],
                                        filter_plugin['events']['out'])
                        metrics['plugins_filters_metrics']['duration'] \
                            .add_metric([pipeline_id, plugin_name, plugin_id],
                                        filter_plugin['events']['duration_in_millis'] / 1000.0)

                        # grok plugin has some special fields
                        if plugin_name == "grok":
                            metrics['plugins_filters_metrics']['grok_matches'] \
                                .add_metric([pipeline_id, plugin_id],
                                            filter_plugin['matches'])
                            metrics['plugins_filters_metrics']['grok_failures'] \
                                .add_metric([pipeline_id, plugin_id],
                                            filter_plugin['failures'])

                            # "patterns_per_field" : {
                            #   "message" : 2
                            # }

                    # grab output plugins metrics
                    for output_plugin in result['pipelines'][pipeline_id]['plugins']['outputs']:
                        plugin_name = output_plugin['name']
                        plugin_id = output_plugin['id']
                        metrics['plugins_outputs_metrics']['in'] \
                            .add_metric([pipeline_id, plugin_name, plugin_id],
                                        output_plugin['events']['in'])
                        metrics['plugins_outputs_metrics']['out'] \
                            .add_metric([pipeline_id, plugin_name, plugin_id],
                                        output_plugin['events']['out'])
                        metrics['plugins_outputs_metrics']['duration'] \
                            .add_metric([pipeline_id, plugin_name, plugin_id],
                                        output_plugin['events']['duration_in_millis'] / 1000.0)

        # return metrics
        for metric_type in metrics:
            for metric in metrics[metric_type]:
                yield metrics[metric_type][metric]


if __name__ == "__main__":

    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="set debug mode")
    parser.add_argument("logstash_endpoint", help="logstash's endpoint", nargs='?', default="http://localhost:9600")
    parser.add_argument("listen_port", help="exporter binding port", nargs='?', default=9198, type=int)
    args = parser.parse_args()

    # set logging
    if args.debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    logging_format = "%(asctime)s: %(levelname)s: %(message)s"
    logging.basicConfig(format=logging_format, level=logging_level)

    # setup and register metrics collector
    REGISTRY.register(LogstashPipelineCollector(args.logstash_endpoint))

    # expose metrics
    start_http_server(args.listen_port)
    logging.info("Now listening on port %d..." % args.listen_port)
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Quitting...")
        sys.exit()
