#!/usr/bin/python3

import argparse
import configparser
import re
import os
import sys

import jenkins


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
    parser_jobs_delete.set_defaults(func=jobs_delete)
    # jobs list
    parser_jobs_list = subparsers.add_parser(
        'jobs-list', help='List the given job(s)')
    parser_jobs_list.add_argument('job_name', metavar='job-name', help='the Jenkins job name(s) (regex)')
    parser_jobs_list.set_defaults(func=jobs_list)
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
            jenkins.delete_job(job['fullname'])
            print(f"Deleted job {job['fullname']}")


def jobs_list(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)
    regex = re.compile(args.job_name)
    for job in jenkins.get_jobs():
        if regex.match(job['fullname']):
            print(f"{job['fullname']}")


def jobs_copy(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)
    regex = re.compile(args.job_name)
    for job in jenkins.get_jobs():
        if regex.match(job['fullname']):
            job_name_new = re.sub(args.job_name_pattern, args.job_name_repl, job['fullname'])
            if job['fullname'] != job_name_new:
                print(f"Copy job {job['fullname']:60} -> {job_name_new}")
                jenkins.copy_job(job['fullname'], job_name_new)


def nodes_list(args):
    url, user, password = _get_profile(args)
    jenkins = _jenkins(url, user, password)
    print(f'{"Name":30} Labels')
    for node in jenkins.get_nodes():
        if jenkins.node_exists(node['name']):
            ni = jenkins.get_node_info(node['name'])
            labels = [l['name'] for l in ni['assignedLabels'] if l['name'] != node['name']]
            print(f'{node["name"]:30} {", ".join(labels):10}')


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
