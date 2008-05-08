from datetime import datetime

from jinja.filters import simplefilter

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

@simplefilter
def friendly_date(d):
	now = datetime.now()
	
	if d.year <= (now.year - 1):
		return "Years ago"
	
	if d.year == (now.year - 1):
		return "Last year"
	
	if d.month <= (now.month - 1):
		return "Earlier this year"
	
	if d.month == (now.month - 1):
		return "Last month"
	
	if d.day <= (now.day - 6):
		return "Earlier this month"
	
	if d.day == (now.day - 1):
		return "Yesterday @ %02d:%02d" % (d.hour, d.minute)
	
	if not d.day == now.day:
		return weekdays[d.day]
	
	if d.day == now.day:
		return "Today @ %02d:%02d" % (d.hour, d.minute)

