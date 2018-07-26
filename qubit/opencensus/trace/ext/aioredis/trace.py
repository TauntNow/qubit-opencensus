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

import logging
import wrapt

from qubit.opencensus.trace import asyncio_context

log = logging.getLogger(__name__)

MODULE_NAME = 'aioredis'

CONNECTION_WRAP_METHODS = 'execute'
CONNECTION_CLASS_NAME = 'RedisConnection'


def trace_integration(tracer=None):
    # Wrap Session class
    wrapt.wrap_function_wrapper(
        MODULE_NAME, 'RedisConnection.execute', wrap_execute)


async def wrap_execute(wrapped, instance, args, kwargs):
    """Wrap the session function to trace it."""
    command = args[0]
    _tracer = asyncio_context.get_opencensus_tracer()
    if _tracer is None:
        return await wrapped(*args, **kwargs)

    _span = _tracer.start_span()
    _span.name = '[aioredis] {}'.format(command)

    _tracer.add_attribute_to_current_span('redis.db', instance.db)
    _tracer.add_attribute_to_current_span('redis.address', instance.address[0])
    _tracer.add_attribute_to_current_span('redis.port', instance.address[1])
    _tracer.add_attribute_to_current_span('redis.encoding',
            str(instance.encoding))
    if len(args) > 1:
        _tracer.add_attribute_to_current_span('redis.key', args[1])

    # Add the requests url to attributes
    try:
        result = await wrapped(*args, **kwargs)
        if isinstance(result, bytes):
            _tracer.add_attribute_to_current_span('redis.resposne.size',
                    len(result))
        else:
            _tracer.add_attribute_to_current_span('redis.resposne.size',
                    0)
        _tracer.end_span()
        return result
    except Exception as e:
        _tracer.add_attribute_to_current_span('error', True)
        _tracer.add_attribute_to_current_span('error.message', str(e))
        _tracer.end_span()
        raise e

