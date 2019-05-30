# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging

from opencensus.trace.span_context import SpanContext
from opencensus.trace import span as trace_span
from opencensus.trace import span_data as span_data_module
from opencensus.trace import print_exporter
from opencensus.trace.tracers import base
from qubit.opencensus.trace import asyncio_context


class ContextTracer(base.Tracer):
    """The interface for tracing a request context.

    :type span_context: :class:`~opencensus.trace.span_context.SpanContext`
    :param span_context: SpanContext encapsulates the current context within
                         the request's trace.
    """

    def __init__(self, exporter=None, span_context=None):
        if exporter is None:
            exporter = print_exporter.PrintExporter()

        if span_context is None:
            span_context = SpanContext()

        self.exporter = exporter
        self.span_context = span_context
        self.trace_id = span_context.trace_id
        self.root_span_id = span_context.span_id

        # List of spans to report
        self._spans_list = []

    def finish(self):
        """Finish all spans

        :rtype: dict
        :returns: JSON format trace.
        """
        while self._spans_list:
            self.end_span()

    def span(self, name='span'):
        """Create a new span with the trace using the context information.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.span.Span`
        :returns: The Span object.
        """
        span = self.start_span(name=name)
        return span

    def start_span(self, name='span'):
        """Start a span.

        :type name: str
        :param name: The name of the span.

        :rtype: :class:`~opencensus.trace.span.Span`
        :returns: The Span object.
        """
        parent_span = self.current_span()

        # If a span has remote parent span, then the parent_span.span_id
        # should be the span_id from the request header.
        if parent_span is None:
            parent_span = base.NullContextManager(
                span_id=self.span_context.span_id)

        span = trace_span.Span(
            name,
            parent_span=parent_span,
            context_tracer=self)
        self._spans_list.append(span)
        self.span_context.span_id = span.span_id
        asyncio_context.set_current_span(span)
        span.start()
        return span

    def end_span(self, *args, **kwargs):
        """End a span. Update the span_id in SpanContext to the current span's
        parent span id; Update the current span.
        """
        cur_span = self.current_span()
        if cur_span is None and self._spans_list:
            cur_span = self._spans_list[-1]

        if cur_span is None:
            logging.warning('No active span, cannot do end_span.')
            return

        cur_span.finish()
        self.span_context.span_id = cur_span.parent_span.span_id if \
            cur_span.parent_span else None

        if isinstance(cur_span.parent_span, trace_span.Span):
            asyncio_context.set_current_span(cur_span.parent_span)
        else:
            asyncio_context.set_current_span(None)

        if cur_span in self._spans_list:
            span_datas = self.get_span_datas(cur_span)
            self.exporter.export(span_datas)
            self._spans_list.remove(cur_span)

        return cur_span

    def current_span(self):
        """Return the current span."""
        current_span = asyncio_context.get_current_span()

        return current_span

    def list_collected_spans(self):
        return self._spans_list

    def add_attribute_to_current_span(self, attribute_key, attribute_value):
        """Add attribute to current span.

        :type attribute_key: str
        :param attribute_key: Attribute key.

        :type attribute_value:str
        :param attribute_value: Attribute value.
        """
        current_span = self.current_span()
        current_span.add_attribute(attribute_key, attribute_value)

    def get_span_datas(self, span):
        """Extracts a list of SpanData tuples from a span

        :rtype: list of opencensus.trace.span_data.SpanData
        :return list of SpanData tuples
        """
        span_tree = list(iter(span))
        span_datas = [
            span_data_module.SpanData(
                name=span.name,
                context=self.span_context,
                span_id=span.span_id,
                parent_span_id=span.parent_span.span_id if
                span.parent_span else None,
                attributes=span.attributes,
                start_time=span.start_time,
                end_time=span.end_time,
                child_span_count=len(span.children),
                stack_trace=span.stack_trace,
                time_events=span.time_events,
                links=span.links,
                status=span.status,
                same_process_as_parent_span=span.same_process_as_parent_span,
                span_kind=span.span_kind

            )
            for span in span_tree
        ]

        return span_datas


class AsyncSpan:
    def __init__(self, function, name=None):
        self.name = name
        self.function = None
        if isinstance(function, str):
            # alternate signature
            self.name = function
        elif callable(function):
            self.function = function
        else:
            raise TypeError("First parameter must be either a span name or a callable function")

    async def __call__(self, *args, **kargs):
        if self.function:
            with self:
                if asyncio.iscoroutinefunction(self.function):
                    return await self.function(*args, **kargs)
                else:
                    return self.function(*args, **kargs)
        elif len(args) and callable(args[0]):
            self.function = args[0]
            return self
        else:
            raise TypeError("Decorated function not yet set. Must be called with a callable function")

    async def __aenter__(self):
        _tracer = asyncio_context.get_opencensus_tracer()
        _span = _tracer.start_span()
        _span.name = self.name if self.name is not None else ("[func] " + self.function.__name__)
        return _span

    async def __aexit__(self, exc_type, exc, tb):
        _tracer = asyncio_context.get_opencensus_tracer()
        if exc:
            _tracer.add_attribute_to_current_span('error', True)
            _tracer.add_attribute_to_current_span('error.message', str(exc))
            _tracer.end_span()
            raise exc
        else:
            _tracer.end_span()

def span(name=None):
    return AsyncSpan(name)
