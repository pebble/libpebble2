__author__ = 'katharine'

from libpebble2.protocol.base.types import *
import libpebble2.protocol.datalogging as datalogging
from textwrap import dedent


def format_properties(packet):
    print "<table>"
    if len(packet._type_mapping) > 0:
        print "<tr><th>Field</th><th>Type</th></tr>"
        for name, field in packet._type_mapping.iteritems():
            if not isinstance(field, Union):
                print "<tr><td>{}</td><td>".format(name)
                if field._enum is not None:
                    pass
                else:
                    print type(field).__name__
                print "</td></tr>"
            else:
                print "<tr><td>{}</td><td>".format(name)
                print "<table>"
                print "<tr><th><em>{}</em></th><th></th></tr>".format(field.determinant._name)
                for k, v in sorted(field.contents.iteritems(), key=lambda x: x[0]):
                    print "<tr><th>0x{:02x}</th><td>".format(k)
                    print "<h3>{}</h3>".format(v.__name__)
                    print "<p>{}</p>".format(dedent(v.__doc__ or "").strip().replace("\n", "<br>\n"))
                    format_properties(v)
                    print "</td></tr>"
                print "</table></td></tr>"
    print "</table>"

def generate(module):
    print """
    <html>
        <head>
            <style>
            table * {
                vertical-align: top;
            }
            </style>
        </head>
        <body>
    """
    packets = [getattr(module, x) for x in module.__all__]
    for packet in packets:
        if hasattr(packet, '_Meta') and packet._Meta.get('endpoint', None) is not None:
            print "<h2>{} (endpoint 0x{:04x})</h2>".format(packet.__name__, packet._Meta['endpoint'])
            print "<strong><em>"
            if packet._Meta.get('endianness', '>') == '<':
                print "little endian"
            else:
                print "big endian"
            print "</strong></em>"
            if packet.__doc__ is not None:
                print "<p>{}</p>".format(dedent(packet.__doc__).strip().replace("\n", "<br>\n"))
            format_properties(packet)
    print "</body></html>"

if __name__ == "__main__":
    generate(datalogging)