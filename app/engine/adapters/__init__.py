from . import benco, henry_schein, base86, darby, patterson, auto_detect

ADAPTERS = {
    "Benco": benco.parse,
    "Henry Schein": henry_schein.parse,
    "Base86": base86.parse,
    "Darby": darby.parse,
    "Patterson": patterson.parse,
}
