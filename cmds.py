import os

from dockermap.api import DockerClientWrapper, DockerFile, ContainerMap, MappingDockerClient
from dockermap.map.policy.base import BasePolicy
from dockermap.shortcuts import chmod

#--- Config
PROJECT_NAME = 'myproj'
WORDPRESS_DL_URL = 'https://wordpress.org/wordpress-{}.zip'
WORDPRESS_VERSION = '4.3.1'
WORDPRESS_PLUGINS = [
    ('theme-check', '20150818.1'),
]
DBNAME = PROJECT_NAME
DBUSER = 'root'
DBPASS = 'whatever' # The DB container is never publicly exposed, so this password isn't really sensitive.
WORDPRESS_IMGNAME = '{}-wordpress'.format(PROJECT_NAME)
MARIADB_IMGNAME = '{}-mariadb'.format(PROJECT_NAME)

#--- Private
def _get_client():
    return DockerClientWrapper('unix://var/run/docker.sock')

def _make_worpress(nocache):
    APT_DEPS = [
        'curl',
        'zip',
        'apache2',
        'libapache2-mod-php5',
        'php5-mysql',
        'php5-gd',
        'php5-curl',
        'mysql-client',
        'gettext',
    ]
    WORDPRESS_PLUGINS_DL_URL = 'https://downloads.wordpress.org/plugin/{slug}.{version}.zip'
    wpurl = WORDPRESS_DL_URL.format(WORDPRESS_VERSION)
    wpprefix = '/var/www/wordpress'
    with DockerFile('debian:jessie') as df:
        df.volumes = ['{}/wp-content/uploads'.format(wpprefix)]
        df.expose = '80'
        df.command = '/run.sh'
        # Download and install
        df.run(' && '.join([
            'apt-get update',
            'DEBIAN_FRONTEND=noninteractive apt-get -yq install %s' % ' '.join(APT_DEPS),
            'rm -rf /var/lib/apt/lists/*',
        ]))
        # We don't do checksums because they're redundant. We already download through HTTPS.
        # If we trust the source, we can trust that the content is not malicious.
        assert wpurl.startswith('https')
        df.run(' && '.join([
            'curl -o wordpress.zip -sSL {}'.format(wpurl),
            'unzip wordpress.zip -d /var/www',
            'rm wordpress.zip',
        ]))
        # remove useless stuff from WP
        df.run('rm {}/wp-content/plugins/hello.php'.format(wpprefix))
        # install plugins. we don't use wp-cli because installing a plugin with it requires the DB
        for (pluginname, version) in WORDPRESS_PLUGINS:
            url = WORDPRESS_PLUGINS_DL_URL.format(slug=pluginname, version=version)
            df.run(' && '.join([
                'curl -o {slug}.zip -sSL {url}'.format(slug=pluginname, url=url),
                'unzip {slug}.zip -d {wpprefix}/wp-content/plugins'.format(slug=pluginname, wpprefix=wpprefix),
                'rm {slug}.zip'.format(slug=pluginname),
            ]))
        # wpcli setup
        df.run('cd / && curl -s -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar')
        # setup DB
        df.run(' && '.join([
            'cd {}'.format(wpprefix),
            'php /wp-cli.phar --allow-root core config --dbhost=mariadb --dbname={} --dbuser={} --dbpass={} --skip-check'.format(DBNAME, DBUSER, DBPASS),
        ]))
        # add theme
        df.add_file('theme', '{}/wp-content/themes/local_theme'.format(wpprefix))
        # fix permissions
        df.run('chown -R www-data:www-data {}'.format(wpprefix))
        # WP/apache config
        df.run('a2enmod rewrite')
        df.add_file('conf/wordpress_apache.conf', '/etc/apache2/sites-enabled/000-default.conf')
        df.add_file('conf/wordpress_run.sh', '/run.sh')
        df.run(chmod('+x', '/run.sh'))
        _get_client().build_from_file(df, WORDPRESS_IMGNAME, rm=True, nocache=nocache)

def _make_mariadb(nocache):
    with DockerFile('mariadb') as df:
        df.prefix('ENV', 'MYSQL_ROOT_PASSWORD', DBPASS)
        df.prefix('ENV', 'MYSQL_DATABASE', DBNAME)
        _get_client().build_from_file(df, MARIADB_IMGNAME, rm=True, nocache=nocache)

def _get_container_map(liveedit=False):
    result = ContainerMap(PROJECT_NAME, {
        'wordpress': {
            'image': WORDPRESS_IMGNAME,
            'links': 'mariadb',
            'attaches': 'uploads',
            'exposes': {80: 80},
        },
        'mariadb': {
            'image': MARIADB_IMGNAME,
        },
        'volumes': {
            'uploads': '/var/www/wordpress/wp-content/uploads',
        },
    })
    if liveedit:
        result.volumes.livetheme = '/var/www/wordpress/wp-content/themes/local_theme'
        result.host.livetheme = os.path.abspath('theme')
        result.containers['wordpress'].binds += [('livetheme', 'ro')]
    return result

#--- Public
def make(target=None, nocache=False):
    print("Building Wordpress image")
    _make_worpress(nocache=nocache)
    print("Building Database image")
    _make_mariadb(nocache=nocache)
    print("Done!")

def start(port, liveedit):
    cmap = _get_container_map(liveedit=liveedit)
    print("Starting website on http://localhost:80")
    MappingDockerClient(cmap, _get_client()).startup('wordpress')
    print("Done!")

def stop(clean=False):
    # We use a "manual approach" here because docker-map's approach is way too complicated for
    # our needs.
    NORMAL_CONTAINERS = ['wordpress']
    PERSISTENT_CONTAINERS = ['mariadb']
    VOLUMES = ['uploads']
    client = _get_client()
    print("Stopping instances...")
    for name in NORMAL_CONTAINERS + PERSISTENT_CONTAINERS:
        client.stop(BasePolicy.cname(PROJECT_NAME, name))
    for name in NORMAL_CONTAINERS:
        client.remove_container(BasePolicy.cname(PROJECT_NAME, name))
    if clean:
        print("Cleaning instances...")
        for name in PERSISTENT_CONTAINERS:
            client.remove_container(BasePolicy.cname(PROJECT_NAME, name))
        for name in VOLUMES:
            client.remove_container(BasePolicy.aname(PROJECT_NAME, name))
    print("Done!")

