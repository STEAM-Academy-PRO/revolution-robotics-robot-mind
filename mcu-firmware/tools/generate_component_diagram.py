import argparse

import chevron
from graphviz import Digraph

from cglue.plugins.AsyncServerCalls import async_server_calls, AsyncServerCallSignal
from cglue.plugins.BuiltinDataTypes import builtin_data_types, QueueSignal, ArraySignal, ConstantArraySignal, \
    ConstantSignal, VariableSignal
from cglue.plugins.Locks import locks
from cglue.plugins.ProjectConfigCompactor import project_config_compactor
from cglue.plugins.RuntimeEvents import runtime_events, ServerCallSignal, EventSignal
from cglue.plugins.UserCodePlugin import user_code_plugin
from cglue.cglue import CGlue

component_template = '''<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="5" STYLE="ROUNDED" BGCOLOR="#ffffff">
    <TR>
        <TD COLSPAN="2" BORDER="1" SIDES="B">
            <FONT POINT-SIZE="22" FACE="Calibri">
                <B>{{ component_name }}</B>
            </FONT>
        </TD>
    </TR>
    <TR>
        <TD>
            {{# has_consumers }}
            <TABLE BORDER="0">
            {{# has_runnables }}
                <TR>
                    <TD BORDER="0">
                    <TABLE FIXEDSIZE="TRUE" WIDTH="0" HEIGHT="0" ALIGN="LEFT" BORDER="0" CELLBORDER="1" CELLSPACING="0">
                        {{# runnables }}
                        <TR>
                            <TD PORT="C{{ component_name }}/{{ name }}" BGCOLOR="lightgrey">&gt;</TD>
                            <TD ALIGN="LEFT" BGCOLOR="{{ style.bgcolor }}">
                                <FONT COLOR="{{ style.color }}">{{ name }}</FONT>
                            </TD>
                        </TR>
                        {{/ runnables }}
                    </TABLE>
                    </TD>
                </TR>
            {{/ has_runnables }}
            {{# has_consumer_ports }}
                <TR>
                    <TD BORDER="0">
                    <TABLE FIXEDSIZE="TRUE" WIDTH="0" HEIGHT="0" ALIGN="LEFT" BORDER="0" CELLBORDER="1" CELLSPACING="0">
                        {{# consumer_ports }}
                        <TR>
                            <TD PORT="C{{ component_name }}/{{ name }}" BGCOLOR="lightgrey">&gt;</TD>
                            <TD ALIGN="LEFT" BGCOLOR="{{ style.bgcolor }}"><FONT COLOR="{{ style.color }}">{{ name }}</FONT></TD>
                        </TR>
                        {{/ consumer_ports }}
                    </TABLE>
                    </TD>
                </TR>
            {{/ has_consumer_ports }}
            </TABLE>
            {{/ has_consumers }}
        </TD>
        <TD VALIGN="TOP">
            {{# has_provider_ports }}
            <TABLE FIXEDSIZE="TRUE" WIDTH="0" HEIGHT="0" ALIGN="RIGHT" BORDER="0" CELLBORDER="1" CELLSPACING="0">
                {{# provider_ports }}
                <TR>
                    <TD ALIGN="RIGHT" BGCOLOR="{{ style.bgcolor }}"><FONT COLOR="{{ style.color }}">{{ name }}</FONT></TD>
                    <TD PORT="P{{ component_name }}/{{ name }}" BGCOLOR="lightgrey">&gt;</TD>
                </TR>
                {{/ provider_ports }}
            </TABLE>
            {{/ has_provider_ports }}
        </TD>
    </TR>
</TABLE>>
'''


def add_component(g: Digraph, component_name, component_data):
    """Display a component and its ports"""
    # classify ports
    consumer_ports = []
    provider_ports = []
    runnables = []

    port_styles = {
        'ReadValue': {'bgcolor': '#dff0fa', 'color': '#000000'},
        'WriteData': {'bgcolor': '#dff0fa', 'color': '#000000'},
        'Constant':  {'bgcolor': '#dff0fa', 'color': '#000000'},

        'ReadIndexedValue': {'bgcolor': '#e7f5d8', 'color': '#000000'},
        'WriteIndexedData': {'bgcolor': '#e7f5d8', 'color': '#000000'},
        'ConstantArray':    {'bgcolor': '#e7f5d8', 'color': '#000000'},

        'ReadQueuedValue':  {'bgcolor': '#e4dcf1', 'color': '#000000'},

        'Runnable':        {'bgcolor': '#fffbe5', 'color': '#000000'},
        'ServerCall':      {'bgcolor': '#fffbe5', 'color': '#000000'},
        'Event':           {'bgcolor': '#fffbe5', 'color': '#000000'},

        'AsyncRunnable':   {'bgcolor': '#ffe5e5', 'color': '#000000'},
        'AsyncServerCall': {'bgcolor': '#ffe5e5', 'color': '#000000'}
    }

    empty_style = {'bgcolor': '#f2f2f2', 'color': '#000000'}

    for port_name, port_data in component_data['ports'].items():
        port_type_data = rt.port_types[port_data['port_type']]
        port_display_data = {'name': port_name, 'style': port_styles.get(port_data['port_type'], empty_style)}

        if port_data['port_type'] in ['Runnable', 'AsyncRunnable']:
            runnables.append(port_display_data)
        elif port_data['port_type'] in ['ServerCall', 'AsyncServerCall']:
            provider_ports.append(port_display_data)
        else:
            if 'consumes' in port_type_data.config:
                consumer_ports.append(port_display_data)

            if 'provides' in port_type_data.config:
                provider_ports.append(port_display_data)

    consumer_ports = sorted(consumer_ports, key=lambda x: x['name'])
    provider_ports = sorted(provider_ports, key=lambda x: x['name'])
    runnables = sorted(runnables, key=lambda x: x['name'])

    # render HTML template and add node
    template_ctx = {
        'component_name': component_name,

        'consumer_ports': consumer_ports,
        'provider_ports': provider_ports,
        'runnables': runnables,

        'has_runnables': len(runnables) > 0,
        'has_consumer_ports': len(consumer_ports) > 0,
        'has_provider_ports': len(provider_ports) > 0,

        'has_consumers': len(runnables) + len(consumer_ports) > 0
    }

    g.node(component_name, label=chevron.render(component_template, data=template_ctx))


def connections(signals):

    # special cases: call signals basically provide runnables, but runnables are displayed as consumers (of events)
    invert_signals = [ServerCallSignal, AsyncServerCallSignal]

    """List provider-consumer pairs from the signal list"""
    for provider_name, signals in signals.items():
        for consumer_connections in signals.values():
            if type(consumer_connections) is list:
                consumer_connections_list = consumer_connections
            else:
                consumer_connections_list = [consumer_connections]

            for signal in consumer_connections_list:
                for consumer in signal.consumers:
                    if type(signal.signal) in invert_signals:
                        yield consumer[0], provider_name, str(type(signal.signal))
                    else:
                        yield provider_name, consumer[0], str(type(signal.signal))


def create_graph(filename, format):
    g = Digraph(engine='dot', filename=filename, format=format)
    g.attr('node', shape='plaintext')
    g.attr('graph', rankdir='LR')
    g.attr('graph', ranksep='3')
    g.attr('graph', splines='polyline')
    g.attr('graph', concentrate='true')
    g.attr('graph', bgcolor='#fdf9f9')
    g.attr('graph', margin='0')

    return g


def prepare_graph(g, context, components_to_draw, edges_to_draw, ignored_components=None):
    for component in components_to_draw:
        name = component.name
        add_component(g, name, context.component_instances[name].component.config)

    if ignored_components is None:
        ignored_components = []

    signal_styles = {
        str(EventSignal): 'dot',
        str(ServerCallSignal): 'odot',
        str(AsyncServerCallSignal): 'obox',

        str(VariableSignal): 'normal',
        str(ArraySignal): 'inv',
        str(QueueSignal): 'diamond',
        str(ConstantSignal): 'empty',
        str(ConstantArraySignal): 'invempty',
    }

    for provider_name, consumer_name, signal_type in edges_to_draw:
        pc = provider_name.split('/')[0]
        cc = consumer_name.split('/')[0]
        if pc in ignored_components or cc in ignored_components:
            continue
        g.edge(
            '{}:P{}:e'.format(pc, provider_name),
            '{}:C{}:w'.format(cc, consumer_name),
            arrowhead=signal_styles.get(signal_type, 'normal')
        )


def draw_single_component_graph(context, component, dirname, filename):
    g = create_graph(filename + '-' + component + '.gv', args.format)

    components_to_draw = set()
    edges_to_draw = []
    for provider_name, consumer_name, signal_type in connections(context['signals']):
        pc = provider_name.split('/')[0]
        cc = consumer_name.split('/')[0]
        if pc == component or cc == component:
            components_to_draw.add(pc)
            components_to_draw.add(cc)
            edges_to_draw.append((provider_name, consumer_name, signal_type))

    prepare_graph(g, context, components_to_draw, edges_to_draw)

    g.render(directory=dirname, cleanup=True)


def draw_global_graph(context, dirname, filename, ignored_components, display=True):
    g = create_graph(filename + '.gv', args.format)

    rt = context['runtime']
    components_to_draw = rt._components
    edges_to_draw = connections(context['signals'])

    prepare_graph(g, context, components_to_draw, edges_to_draw, ignored_components)

    if display:
        g.view(directory=dirname, cleanup=False)
    else:
        g.render(directory=dirname, cleanup=False)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Name of project config json file', default="project.json")
    parser.add_argument('--format', help='Output file format', choices=['pdf', 'svg'], default="pdf")
    parser.add_argument('--output', help='Output file name', default="diagram")
    parser.add_argument('--component', help='Only render connections for this component', default=None)
    parser.add_argument('--all', help='Create a diagram for every component', action='store_true')
    parser.add_argument('--display', help='Open generated diagram', action='store_true')
    parser.add_argument('--ignore-components', help='Ignore connections to/from these components. Comma separated list', default='')

    args = parser.parse_args()

    rt = CGlue(args.config)
    rt.add_plugin(project_config_compactor())
    rt.add_plugin(builtin_data_types())
    rt.add_plugin(runtime_events())
    rt.add_plugin(locks())
    rt.add_plugin(async_server_calls())
    rt.add_plugin(user_code_plugin())

    rt.load()

    context = rt.get_project_structure()

    # render
    if '/' in args.output:
        dirname, filename = args.output.rsplit('/', 1)
    else:
        dirname = '.'
        filename = args.output

    ignored_components = args.ignore_components.split(',')
    if args.all:
        for component in rt._components:
            draw_single_component_graph(context, component, dirname, filename)
        draw_global_graph(context, dirname, filename, ignored_components, args.display)

    elif args.component:
        draw_single_component_graph(context, args.component, dirname, filename)
    else:
        draw_global_graph(context, dirname, filename, ignored_components, args.display)
