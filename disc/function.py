import datetime
from datetime import timedelta, date 
_YEAR = datetime.datetime.now().year

def allsundays(year):
    list = []
    d = date(year, 1, 1)                    # January 1st
    f = date(year, 1, 1)                    # January 1st
    d += timedelta( (5 - d.weekday() + 7) % 7)  # First Sunday
    f += timedelta( f.weekday() + 6)  # First Friday
    
    while d.year == year:
    	s = d.isocalendar()[1]
    	etiqueta = 'Semana #: '+str(s) + ' del '+ unicode(d)+' al ' +unicode(f)
        list.append( (etiqueta, unicode(f) ) ) 
        d += timedelta(days = 7)
        f += timedelta(days = 7)
    return list 

lista = allsundays(_YEAR)
print lista
