from jinja import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))

def render_template(template_name, *args, **kwargs):
	"""Gets a template and renders it"""
	return env.get_template('%s.html' % template_name).render(kwargs)