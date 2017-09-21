from trytond.pool import Pool
from .disc import *

def register():
    Pool.register(
        Asociacion,
        Campo,
        Zona,
        Distrito,
        Iglesia,
        Gp, 
        Party,
        Reporte, 
        ReporteBautizo,
        module='discipulado', type_='model')