#!/usr/bin/python3

import argparse
import configparser
import datetime
import re
import os
import sys

import jenkins
from prettytable import PrettyTable
from dateutil.relativedelta import relativedelta


# snaps do set $HOME to something like
# /home/$USER/snap/jenkins-tool/$SNAP_VERSION
# the real home (usually /home/$USERNAME) is stored in $SNAP_REAL_HOME
# see https://snapcraft.io/docs/environment-variables
SNAP_REAL_HOME = os.getenv('SNAP_REAL_HOME')
if SNAP_REAL_HOME:
    CONF_PATH = os.path.join(os.path.join(SNAP_REAL_HOME, '.config', 'jentool.ini'))
else:
    CONF_PATH = os.path.join(os.path.expanduser('~'), '.config', 'jentool.ini')


def _jenkins(url, user, password):
    """get a jenkinsapi jenkins instance"""
    j = jenkins.Jenkins(url,
                        username=user,
                        password=password)
    return j


def _get_profile(args):
    if not os.path.exists(args.config_file):
        print(f'jentool configuration file {args.config_file} does not exist')
        sys.exit(1)
    config = configparser.ConfigParser()
    config.read(args.config_file)
    if args.config_profile not in config:
        print(f'can not find section {args.config_profile} in {args.config_file}')
        sys.exit(1)
    if 'url' not in config[args.config_profile]:
        print(f'url not in profile {args.config_profile}')
        sys.exit(1)
    if 'user' not in config[args.config_profile]:
        print(f'user not in profile {args.config_profile}')
        sys.exit(1)
    if 'password' not in config[args.config_profile]:
        print(f'password not in profile {args.config_profile}')
        sys.exit(1)
    return (config[args.config_profile]['url'],
            config[args.config_profile]['user'],
            config[args.config_profile]['password'])


def _parser():
    parser = argparse.ArgumentParser(
        description='Jenkins tool')
    jenkins_group = parser.add_argument_group(title='Jenkins')
    jenkins_group.add_argument('--config-file', '-c',
                               default=CONF_PATH,
                               help='Path to the configuration file. Default: %(default)s')
    jenkins_group.add_argument('--config-profile', '-p', default='default',
                               help='The profile (section) to use in the config-file. '
                               'Default: %(default)s')
    subparsers = parser.add_subparsers(title='sub-command help')
    # jobs disable
    parser_jobs_disable = subparsers.add_parser(
        'jobs-disable', help='Disable the given job(s)')
    parser_jobs_disable.add_argument('job_name', metavar='job-name', help='the Jenkins job name(s) (regex)')
    parser_jobs_disable.set_defaults(func=jobs_disable)
    # jobs delete
    parser_jobs_delete = subparsers.add_parser(
        'jobs-delete', help='Delete the given job(s)')
    parser_jobs_delete.add_argument('job_name', metavar='job-name', help='the Jenkins job name(s) (regex)')
    parser_jobs_delete.add_argument('--disabled-only', action='store_true', help='Only delete disabled jobs')
    parser_jobs_delete.set_defaults(func=jobs_delete)
    # jobs list
    parser_jobs_list = subparsers.add_parser(
        'jobs-list', help='List the given job(s)')
    parser_jobs_list.add_argument('job_name', metavar='job-name', help='the Jenkins job name(s) (regex)')
    parser_jobs_list.set_defaults(func=jobs_list)
    # jobs config
    parser_jobs_config = subparsers.add_parser(
        'jobs-config', help='Get config(s) for the given job(s)')
    parser_jobs_config.add_argument('job_name', metavar='job-name', help='the Jenkins job name(s) (regex)')
    parser_jobs_config.set_defaults(func=jobs_config)
    # jobs copy
    parser_jobs_copy = subparsers.add_parser(
        'jobs-copy', help='Copy the given job(s)')
    parser_jobs_copy.add_argument('job_name', metavar='job-name', help='the Jenkins job name(s) (regex)')
    parser_jobs_copy.add_argument('job_name_pattern', metavar='job-name-pattern', help='the Jenkins job name search pattern (regex)')
    parser_jobs_copy.add_argument('job_name_repl', metavar='job-name-repl', help='the Jenkins job name replacement')
    parser_jobs_copy.set_defaults(func=jobs_copy)
    # nodes list
    parser_nodes_list = subparsers.add_parser(
        'nodes-list', help='List all nodes')
    parser_nodes_list.set_defaults(func=nodes_list)
    # jobs failing
    parser_jobs_failing = subparsers.add_parser(
        'jobs-failing', help='List failing jobs')
    parser_jobs_failing.add_argument('pattern', metavar='pattern', help='the Jenkins job name(s) (regex)')
    parser_jobs_failing.add_argument('--max-score', '-m', default=0, type=int, help='the maximum health score to look for')
    parser_jobs_failing.set_defaults(func=jobs_failing)
    # jobs unstable
    parser_jobs_unstable = subparsers.add_parser(
        'jobs-unstable', help='List unstable jobs')
    parser_jobs_unstable.add_argument('pattern', metavar='pattern', help='the Jenkins job name(s) (regex)')
    parser_jobs_unstable.set_defaults(func=jobs_unstable)
    # jobs running
    parser_builds_running = subparsers.add_parser(
        'builds-running', help='List running builds')
    parser_builds_running.add_argument('--longer-than', default=0, type=int, help='Only builds running longer than X seconds')
    parser_builds_running.set_defaults(func=builds_running)

    return parser


def jobs_disable(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)
    regex = re.compile(args.job_name)
    for job in jenkins.get_jobs():
        if regex.match(job['fullname']):
            print(f"Disable job {job['fullname']}")
            jenkins.disable_job(job['fullname'])


def jobs_delete(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)
    regex = re.compile(args.job_name)
    for job in jenkins.get_jobs():
        if regex.match(job['fullname']):
            if args.disabled_only:
                # ignore if the job is enabled
                job_info = jenkins.get_job_info(job['fullname'])
                if job_info['disabled'] is False:
                    continue
            jenkins.delete_job(job['fullname'])
            print(f"Deleted job {job['fullname']}")


def jobs_list(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)
    regex = re.compile(args.job_name)
    for job in jenkins.get_jobs():
        if regex.match(job['fullname']):
            print(f"{job['fullname']}")


def jobs_config(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)
    regex = re.compile(args.job_name)
    for job in jenkins.get_jobs():
        if regex.match(job['fullname']):
            print(jenkins.get_job_config(job['fullname']))


def jobs_copy(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)
    regex = re.compile(args.job_name)
    for job in jenkins.get_jobs():
        if regex.match(job['fullname']):
            job_name_new = re.sub(args.job_name_pattern, args.job_name_repl, job['fullname'])
            if job['fullname'] != job_name_new:
                if jenkins.job_exists(job_name_new):
                    print(f"Job {job_name_new} already exists. skipping copy ...")
                else:
                    print(f"Copy job {job['fullname']:60} -> {job_name_new}")
                    jenkins.copy_job(job['fullname'], job_name_new)


def nodes_list(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)
    t = PrettyTable()
    t.field_names = ['Name', 'Labels', 'Executors', 'Offline']
    for node in jenkins.get_nodes():
        if jenkins.node_exists(node['name']):
            ni = jenkins.get_node_info(node['name'])
            labels = [l['name'] for l in ni['assignedLabels'] if l['name'] != node['name']]
            t.add_row([node["name"], ", ".join(labels), ni['numExecutors'], node['offline']])
    print(t)


def jobs_failing(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)

    pattern = args.pattern
    max_score = args.max_score

    t = PrettyTable()
    t.field_names = ['Name', 'Score', 'URL']
    t.align = 'l'
    for info in jenkins.get_job_info_regex(pattern):
        if info['color'] == 'red' and info['healthReport'][0]['score'] <= max_score:
            t.add_row([info["name"], info['healthReport'][0]["score"], info['url']])

    print(t)


def jobs_unstable(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)

    t = PrettyTable()
    t.field_names = ['Name', 'URL']
    t.align = 'l'
    for info in jenkins.get_job_info_regex(args.pattern):
        if info['lastUnstableBuild']:
            if info['lastUnstableBuild']['number'] == info['lastBuild']['number']:
                t.add_row([info["name"], info['url']])

    print(t)


def builds_running(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)

    t = PrettyTable()
    t.field_names = ['Name', 'Started at', 'Url', 'Worker']
    t.align = 'l'

    for build in jenkins.get_running_builds():
        build_info = jenkins.get_build_info(build['name'], build['number'])
        now_dt = datetime.datetime.now()
        if datetime.datetime.timestamp(now_dt) - build_info['timestamp'] / 1000 > args.longer_than:
            timestamp_dt = datetime.datetime.fromtimestamp(build_info['timestamp'] / 1000)
            delta_dt = relativedelta(now_dt, timestamp_dt)
            t.add_row([build_info['fullDisplayName'],
                       f'{timestamp_dt} ({delta_dt.days} days, {delta_dt.hours} hours)',
                       build_info['url'],
                       build_info['builtOn']])
    print(t)


def main():
    parser = _parser()
    args = parser.parse_args()
    url, user, password = _get_profile(args)
    args = parser.parse_args()

    if 'func' not in args:
        sys.exit(parser.print_help())
    args.func(args)
    sys.exit(0)



if __name__ == '__main__':
    main()
