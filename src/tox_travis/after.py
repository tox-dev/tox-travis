"""Add a flag to pause and wait for all Travis jobs to complete."""
from __future__ import print_function
import os
import sys
import json
import time

from tox.config import _split_env as split_env
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2  # Python 2

from .utils import TRAVIS_FACTORS, parse_dict


# Exit code constants. They are purposely undocumented.
# Please do not depend on their values.
NO_GITHUB_TOKEN = 32
INVALID_POLLING_INTERVAL = 33
INCOMPLETE_TRAVIS_ENVIRONMENT = 34
JOBS_FAILED = 35


def travis_after(ini, envlist):
    """Wait for all jobs to finish, then exit successfully."""
    # after-all disabled for pull requests
    if os.environ.get('TRAVIS_PULL_REQUEST', 'false') != 'false':
        return

    if not after_config_matches(ini, envlist):
        return  # This is not the one that needs to wait

    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print('No GitHub token given.', file=sys.stderr)
        sys.exit(NO_GITHUB_TOKEN)

    api_url = os.environ.get('TRAVIS_API_URL', 'https://api.travis-ci.org')
    build_id = os.environ.get('TRAVIS_BUILD_ID')
    job_number = os.environ.get('TRAVIS_JOB_NUMBER')

    try:
        polling_interval = int(os.environ.get('TRAVIS_POLLING_INTERVAL', 5))
    except ValueError:
        print('Invalid polling interval given: {0}'.format(
            repr(os.environ.get('TRAVIS_POLLING_INTERVAL'))), file=sys.stderr)
        sys.exit(INVALID_POLLING_INTERVAL)

    if not all([api_url, build_id, job_number]):
        print('Required Travis environment not given.', file=sys.stderr)
        sys.exit(INCOMPLETE_TRAVIS_ENVIRONMENT)

    # This may raise an Exception, and it should be printed
    job_statuses = get_job_statuses(
        github_token, api_url, build_id, polling_interval, job_number)

    if not all(job_statuses):
        print('Some jobs were not successful.')
        sys.exit(JOBS_FAILED)

    print('All required jobs were successful.')


def after_config_matches(ini, envlist):
    """Determine if this job should wait for the others."""
    section = ini.sections.get('travis:after', {})

    if not section:
        return False  # Never wait if it's not configured

    if 'envlist' in section or 'toxenv' in section:
        if 'toxenv' in section:
            print('The "toxenv" key of the [travis:after] section is '
                  'deprecated in favor of the "envlist" key.', file=sys.stderr)

        toxenv = section.get('toxenv')
        required = set(split_env(section.get('envlist', toxenv) or ''))
        actual = set(envlist)
        if required - actual:
            return False

    # Translate travis requirements to env requirements
    env_requirements = [
        (TRAVIS_FACTORS[factor], value) for factor, value
        in parse_dict(section.get('travis', '')).items()
        if factor in TRAVIS_FACTORS
    ] + [
        (name, value) for name, value
        in parse_dict(section.get('env', '')).items()
    ]

    return all([
        os.environ.get(name) == value
        for name, value in env_requirements
    ])


def get_job_statuses(github_token, api_url, build_id,
                     polling_interval, job_number):
    """Wait for all the travis jobs to complete.

    Once the other jobs are complete, return a list of booleans,
    indicating whether or not the job was successful. Ignore jobs
    marked "allow_failure".
    """
    auth = get_json('{api_url}/auth/github'.format(api_url=api_url),
                    data={'github_token': github_token})['access_token']

    while True:
        build = get_json('{api_url}/builds/{build_id}'.format(
            api_url=api_url, build_id=build_id), auth=auth)
        jobs = [job for job in build['jobs']
                if job['number'] != job_number and
                not job['allow_failure']]  # Ignore allowed failures
        if all(job['finished_at'] for job in jobs):
            break  # All the jobs have completed
        elif any(job['state'] != 'passed'
                 for job in jobs if job['finished_at']):
            break  # Some required job that finished did not pass

        print('Waiting for jobs to complete: {job_numbers}'.format(
            job_numbers=[job['number'] for job in jobs
                         if not job['finished_at']]))
        time.sleep(polling_interval)

    return [job['state'] == 'passed' for job in jobs]


def get_json(url, auth=None, data=None):
    """Make a GET request, and return the response as parsed JSON."""
    headers = {
        'Accept': 'application/vnd.travis-ci.2+json',
        'User-Agent': 'Travis/Tox-Travis-1.0a',
        # User-Agent must start with "Travis/" in order to work
    }
    if auth:
        headers['Authorization'] = 'token {auth}'.format(auth=auth)

    params = {}
    if data:
        headers['Content-Type'] = 'application/json'
        params['data'] = json.dumps(data).encode('utf-8')

    request = urllib2.Request(url, headers=headers, **params)
    response = urllib2.urlopen(request).read()
    return json.loads(response.decode('utf-8'))
