import os
from jinja2 import Environment, FileSystemLoader, StrictUndefined


def get_template():
    """ Return a jinja2.Template """
    filename = 'triage.j2'
    triage_dir = os.path.dirname(os.path.abspath(__file__))
    rhcephbugs_dir = os.path.dirname(triage_dir)
    project_dir = os.path.dirname(rhcephbugs_dir)
    template_dir = os.path.join(project_dir, 'templates')
    env = Environment(extensions=['jinja2_time.TimeExtension'],
                      loader=FileSystemLoader(template_dir),
                      trim_blocks=True,
                      undefined=StrictUndefined)
    return env.get_template(filename)


def report_everyone(release, milestone, people):
    """
    Report on all people
    """
    template = get_template()
    return template.render(release=release, milestone=milestone, people=people)
